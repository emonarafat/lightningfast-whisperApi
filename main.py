from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from transformers import pipeline
from pydub import AudioSegment
from concurrent.futures import ThreadPoolExecutor, as_completed
import tempfile, os, time, math, logging

# Config
MODEL_NAME = "openai/whisper-tiny"
CHUNK_SEC = 120
DEVICE = 0 if os.getenv("WHISPER_DEVICE", "cpu") != "cpu" else "cpu"
WORKERS = int(os.getenv("WORKER_COUNT", max(1, (os.cpu_count() or 2) - 1)))

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("WhisperAPI")

# FastAPI app
app = FastAPI(title="⚡ Whisper Streaming Transcriber")
executor = ThreadPoolExecutor(max_workers=WORKERS)

# Load model pipeline
logger.info("🔄 Loading Whisper model pipeline...")
pipe = pipeline(
    "automatic-speech-recognition",
    model=MODEL_NAME,
    device=DEVICE,
    chunk_length_s=CHUNK_SEC,
    batch_size=8,
    return_timestamps=False
)
logger.info(f"✅ Whisper model '{MODEL_NAME}' loaded on {'cuda' if DEVICE != 'cpu' else 'cpu'} with chunk size {CHUNK_SEC}s")

# Response model
class TranscriptionResponse(BaseModel):
    transcript: str
    audio_duration_sec: float
    processing_time_sec: float
    message: str

# UI
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root():
    return """
    <html><body>
    <h1>🎙️ Whisper Transcription API</h1>
    <p>Use <code>/docs</code> for Swagger UI. Health: <a href="/health">/health</a></p>
    </body></html>
    """

@app.get("/health", summary="Health check", description="Returns health and configuration of the transcription service")
async def health():
    return {
        "status": "ok",
        "device": "cuda" if DEVICE != "cpu" else "cpu",
        "model": MODEL_NAME,
        "workers": WORKERS
    }

# Transcribe chunk (used in parallel)
def transcribe_chunk(idx, audio_path, language):
    logger.info(f"🔍 Transcribing chunk {idx}: {audio_path} (language={language})")
    try:
        result = pipe(audio_path, generate_kwargs={"language": language})["text"]
        logger.info(f"✔️ Chunk {idx} transcribed successfully")
        return (idx, result)
    except Exception as e:
        logger.exception(f"❌ Error transcribing chunk {idx}")
        return (idx, f"[Error in chunk {idx}]")
    finally:
        try:
            os.remove(audio_path)
            logger.debug(f"🗑️ Deleted temp file: {audio_path}")
        except Exception as cleanup_error:
            logger.warning(f"⚠️ Failed to delete chunk file {audio_path}: {cleanup_error}")


@app.post(
    "/transcribe",
    response_model=TranscriptionResponse,
    summary="Transcribe audio file",
    description="Uploads an audio file and returns the transcribed text using Whisper. Supports chunked and parallel processing."
)
async def transcribe(
    file: UploadFile = File(..., description="Audio file to be transcribed"),
    language: str = Query("en", description="Language spoken in the audio (ISO 639-1 code, e.g., 'en', 'bn', 'hi')")
):
    try:
        logger.info(f"📥 Received file: {file.filename}")
        start = time.time()

        # Save uploaded file
        fd, original_path = tempfile.mkstemp(suffix=os.path.splitext(file.filename)[1])
        with os.fdopen(fd, "wb") as f:
            content = await file.read()
            f.write(content)
            logger.info(f"💾 Stored uploaded file: {original_path} ({len(content)} bytes)")

        # Load and chunk audio
        audio = AudioSegment.from_file(original_path)
        os.remove(original_path)
        audio_duration = round(audio.duration_seconds, 2)
        logger.info(f"🎚️ Audio duration: {audio_duration} seconds")

        duration = math.ceil(audio.duration_seconds)
        chunks = []
        for i, start_sec in enumerate(range(0, duration, CHUNK_SEC)):
            fd, chunk_path = tempfile.mkstemp(suffix=".wav")
            os.close(fd)
            audio[start_sec*1000: min((start_sec+CHUNK_SEC)*1000, duration*1000)].export(chunk_path, format="wav")
            logger.debug(f"📦 Created chunk {i}: {chunk_path}")
            chunks.append((i, chunk_path))

        logger.info(f"🚀 Starting parallel transcription with {len(chunks)} chunks and {WORKERS} workers...")
       futures = [executor.submit(transcribe_chunk, i, path, language) for i, path in chunks]
        results = [f.result() for f in as_completed(futures)]
        results.sort(key=lambda x: x[0])

        transcript = "\n".join([txt for _, txt in results])
        duration_sec = round(time.time() - start, 2)

        logger.info(f"✅ Transcription completed in {duration_sec}s")
        return TranscriptionResponse(
            transcript=transcript,
            audio_duration_sec=audio_duration,
            processing_time_sec=duration_sec,
            message="🎉 Done!"
        )

    except Exception as e:
        logger.exception("❌ Transcription failed")
        raise HTTPException(status_code=500, detail="Transcription failed")
