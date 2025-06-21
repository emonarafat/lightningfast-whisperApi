# ⚡ Fastest Whisper API

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/python-3.10%2B-blue?logo=python">
  <img alt="FastAPI" src="https://img.shields.io/badge/fastapi-%3E=0.100-green?logo=fastapi">
  <img alt="License" src="https://img.shields.io/github/license/emonarafat/lightningfast-whisperApi">
  <img alt="Contributions Welcome" src="https://img.shields.io/badge/contributions-welcome-brightgreen">
  <img alt="Dockerized" src="https://img.shields.io/badge/docker-ready-blue?logo=docker">
  <img alt="Async" src="https://img.shields.io/badge/async-powered-lightgrey">
</p>

A fully async, chunk-aware FastAPI transcription service powered by OpenAI Whisper models. Supports real-time streamed responses and Swagger UI documentation.

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/emonarafat/lightningfast-whisperApi.git
cd lightningfast-whisperApi
```

---

### 2. Environment Setup

Run the interactive launcher:

- **Windows:**  
  Double-click [`run_setup.bat`](run_setup.bat) or run:
  ```bat
  run_setup.bat
  ```

- **Linux / macOS / WSL:**  
  ```bash
  bash run_setup.sh
  ```

Or run the setup script directly:
```bash
python setup_env.py
```

This will:
- Create a `.venv` virtual environment
- Install dependencies from `requirements.txt`
- Generate activation scripts for Windows (`activate_venv.ps1`) and Linux/macOS/WSL (`activate_venv.sh`)

---

### 3. Activate the Virtual Environment

- **Windows (PowerShell):**
  ```powershell
  .\activate_venv.ps1
  ```

- **Linux / macOS / WSL:**
  ```bash
  source activate_venv.sh
  ```

  > If needed, make the script executable:
  > ```bash
  > chmod +x activate_venv.sh
  > ```

---

### 4. Run the API Server

With the virtual environment activated:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health check: [http://localhost:8000/health](http://localhost:8000/health)

---

## 🧪 API Endpoints

### `POST /transcribe`

Upload an audio file and receive the **full transcript after processing**.

### `POST /transcribe/stream`

Upload an audio file and receive **streamed transcript chunks** as each part is transcribed.

#### Request Parameters

- `file` (form-data): The audio file to transcribe
- `language` (query): Language code (e.g. `en`, `bn`, `de`, etc.)

#### Example (cURL)

```bash
curl -X POST -F "file=@example.mp3" \
  "http://localhost:8000/transcribe?language=en"
```

---

## 🔧 Environment Variables

| Variable           | Description                       | Default                 |
|--------------------|-----------------------------------|-------------------------|
| `WHISPER_MODEL`    | HuggingFace model to use          | `openai/whisper-small`  |
| `CHUNK_SEC`        | Chunk size in seconds             | `60`                    |
| `WHISPER_DEVICE`   | Device to use: `cpu` or `cuda`    | `cpu`                   |
| `WORKER_COUNT`     | Max parallel transcription tasks  | `CPU cores - 1`         |

Set them in a `.env` file or export before running Uvicorn.

---

## 📁 Key Files

| File                   | Purpose                                         |
|------------------------|-------------------------------------------------|
| [`main.py`](main.py)   | Core FastAPI server with async Whisper logic    |
| [`setup_env.py`](setup_env.py) | Interactive environment & dependency manager |
| [`requirements.txt`](requirements.txt) | Python dependencies             |
| [`activate_venv.ps1`](activate_venv.ps1) | Windows venv activation script |
| `activate_venv.sh`     | Linux/macOS/WSL venv activation script          |
| [`run_setup.bat`](run_setup.bat) | Windows launcher for setup/activation/server |
| [`run_setup.sh`](run_setup.sh)   | Linux/macOS/WSL launcher for setup/venv     |

---

## 🐳 Docker

You can also run the project in a container:

```bash
docker-compose up --build
```

This will spin up the server with all dependencies including ffmpeg.

---

## 📝 Notes

- Requires **Python 3.10+**
- Make sure **ffmpeg** is installed and available in your system path
- To increase transcription accuracy, change the model via `WHISPER_MODEL` (e.g. `openai/whisper-base`, `openai/whisper-medium`)
- Supports both synchronous and streamed transcription endpoints
- Fully async for high concurrency and performance

---

## 🙌 Contributing

PRs welcome! Feel free to fork and suggest enhancements, especially around:

- API performance
- Streaming formats (e.g. SSE/NDJSON)
- UI or frontend integration
- Model selection and configuration

---