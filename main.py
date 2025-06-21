from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel, Field
from transformers import pipeline
from pydub import AudioSegment
import asyncio, tempfile, os, time, math, logging, json
from typing import List, Optional


# ───────────────────────────────────────────────────────────
# Configuration
# ───────────────────────────────────────────────────────────
MODEL_NAME = os.getenv("WHISPER_MODEL", "openai/whisper-small")
CHUNK_SEC = int(os.getenv("CHUNK_SEC", 60))
DEVICE = 0 if os.getenv("WHISPER_DEVICE", "cpu") != "cpu" else "cpu"
WORKERS = int(os.getenv("WORKER_COUNT", max(1, (os.cpu_count() or 2) - 1)))

# Logging Setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("WhisperAPI")

# ───────────────────────────────────────────────────────────
# App Setup
# ───────────────────────────────────────────────────────────
app = FastAPI(
    title="⚡ Whisper Streaming Transcriber",
    description="Stream or batch transcribe audio files into text using OpenAI's Whisper ASR via Transformers. Supports chunked processing for long audio.",
    version="1.0.0"
)

# ───────────────────────────────────────────────────────────
# Model Initialization
# ───────────────────────────────────────────────────────────
logger.info("🔄 Loading model...")
pipe = pipeline(
    "automatic-speech-recognition",
    model=MODEL_NAME,
    device=DEVICE,
    chunk_length_s=CHUNK_SEC,
    batch_size=10,
    return_timestamps=False
)
logger.info(f"✅ Loaded '{MODEL_NAME}' on {'cuda' if DEVICE != 'cpu' else 'cpu'} with chunk size {CHUNK_SEC}s")

# ───────────────────────────────────────────────────────────
# Response Models
# ───────────────────────────────────────────────────────────
class TranscriptionResponse(BaseModel):
    transcript: str = Field(..., description="Full transcript of all chunks")
    audio_duration_sec: float = Field(..., example=125.3)
    processing_time_sec: float = Field(..., example=7.1)
    message: str = Field(..., example="🎉 Done!")

class ChunkResult(BaseModel):
    chunk: int
    text: str

class StreamingTranscriptionResponse(BaseModel):
    chunks: List[ChunkResult]
    transcript: str
    audio_duration_sec: float
    processing_time_sec: float
    message: str

# ───────────────────────────────────────────────────────────
# Utility
# ───────────────────────────────────────────────────────────
async def transcribe_chunk(idx: int, audio_path: str, language: str):
    loop = asyncio.get_running_loop()

    def run():
        logger.info(f"🔍 Processing chunk {idx}")
        try:
            result = pipe(audio_path, generate_kwargs={"language": language})["text"]
            return idx, result
        except Exception as e:
            logger.warning(f"❌ Chunk {idx} failed: {str(e)}")
            return idx, f"[Error in chunk {idx}]"
        finally:
            try:
                os.remove(audio_path)
            except:
                pass

    return await loop.run_in_executor(None, run)

def create_chunks(audio: AudioSegment, chunk_sec: int) -> List[tuple[int, str]]:
    chunks = []
    duration = math.ceil(audio.duration_seconds)
    for i, start_sec in enumerate(range(0, duration, chunk_sec)):
        fd, chunk_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        audio[start_sec*1000: min((start_sec + chunk_sec) * 1000, duration * 1000)].export(chunk_path, format="wav")
        chunks.append((i, chunk_path))
    return chunks

# ───────────────────────────────────────────────────────────
# Routes
# ───────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root():
    return """
    <html><body>
    <h1>🎙️ Whisper Transcription API</h1>
    <p>Use <a href="/docs">/docs</a> for Swagger UI or <a href="/health">/health</a> for status</p>
    </body></html>
    """

@app.get("/health", summary="Health Check", tags=["System"])
async def health():
    return {
        "status": "ok",
        "device": "cuda" if DEVICE != "cpu" else "cpu",
        "model": MODEL_NAME,
        "workers": WORKERS
    }

@app.post("/transcribe", response_model=TranscriptionResponse, summary="Transcribe audio (batch)", tags=["Transcription"])
async def transcribe(
    file: UploadFile = File(..., description="Audio file to transcribe"),
    language: str = Query("en", description="Language spoken in the audio")
):
    try:
        logger.info(f"📥 Received: {file.filename}")
        start = time.time()

        fd, orig_path = tempfile.mkstemp(suffix=os.path.splitext(file.filename)[1])
        with os.fdopen(fd, "wb") as f:
            f.write(await file.read())

        audio = AudioSegment.from_file(orig_path)
        os.remove(orig_path)

        chunks = create_chunks(audio, CHUNK_SEC)
        logger.info(f"🧩 Created {len(chunks)} chunk(s)")

        results = await asyncio.gather(*[transcribe_chunk(i, path, language) for i, path in chunks])
        results.sort(key=lambda x: x[0])
        transcript = "\n".join([text for _, text in results])
        duration = round(audio.duration_seconds, 2)
        elapsed = round(time.time() - start, 2)

        return TranscriptionResponse(
            transcript=transcript,
            audio_duration_sec=duration,
            processing_time_sec=elapsed,
            message="🎉 Done!"
        )
    except Exception as e:
        logger.exception("❌ Transcription error")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

@app.post("/transcribe/stream", summary="Stream chunks as they’re transcribed", tags=["Transcription"])
async def stream_transcription(
    file: UploadFile = File(..., description="Audio file to transcribe and stream"),
    language: str = Query("en", description="Language spoken in the audio")
):
    try:
        logger.info(f"📥 Streaming request: {file.filename}")
        start = time.time()

        fd, temp_path = tempfile.mkstemp(suffix=os.path.splitext(file.filename)[1])
        with os.fdopen(fd, "wb") as f:
            f.write(await file.read())

        audio = AudioSegment.from_file(temp_path)
        os.remove(temp_path)
        duration = round(audio.duration_seconds, 2)

        chunks = create_chunks(audio, CHUNK_SEC)
        logger.info(f"🚿 Streaming {len(chunks)} chunk(s)...")

        async def stream_chunks():
            yield '{"chunks":['
            first = True
            collected = []

            tasks = [transcribe_chunk(i, p, language) for i, p in chunks]
            for coro in asyncio.as_completed(tasks):
                idx, text = await coro
                collected.append((idx, text))
                if not first:
                    yield ",\n"
                yield json.dumps({"chunk": idx, "text": text})
                first = False

            collected.sort(key=lambda x: x[0])
            full_text = "\n".join([t for _, t in collected])
            elapsed = round(time.time() - start, 2)
            yield f'], "transcript": {json.dumps(full_text)}, "audio_duration_sec": {duration}, "processing_time_sec": {elapsed}, "message": "🎉 Done!"}}'

        return StreamingResponse(stream_chunks(), media_type="application/json")

    except Exception as e:
        logger.exception("❌ Streaming failed")
        raise HTTPException(status_code=500, detail=f"Streaming transcription failed: {str(e)}")
