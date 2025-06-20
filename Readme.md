# Fastest Whisper API

A FastAPI-based streaming transcription API using OpenAI Whisper models.

## 🚀 Local Setup

### 1. Clone the Repository

```sh
git clone <your-repo-url>
cd fastest-whisper
```

### 2. Create Virtual Environment & Install Dependencies

Run the setup script:

```sh
python setup_env.py
```

This will:
- Create a `.venv` virtual environment in the project directory
- Install all dependencies from [`requirements.txt`](requirements.txt)
- Generate an activation script ([`activate_venv.bat`](activate_venv.bat) for Windows)

### 3. Activate the Virtual Environment

- **On Windows:**
  ```sh
  activate_venv.bat
  ```
- **On Linux/macOS:**
  ```sh
  source activate_venv.sh
  ```

### 4. Start the API Server

```sh
uvicorn main:app --reload
```

The API will be available at [http://localhost:8000](http://localhost:8000).

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health check: [http://localhost:8000/health](http://localhost:8000/health)

---

## 📝 Notes

- Requires Python 3.10+.
- Make sure `ffmpeg` is installed (the Dockerfile installs it for containers).
- For GPU support, set the `WHISPER_DEVICE` environment variable accordingly.

---

## 📄 Files

- [`main.py`](main.py): FastAPI app and transcription logic
- [`setup_env.py`](setup_env.py): Local environment setup script
- [`requirements.txt`](requirements.txt): Python dependencies
- [`activate_venv.bat`](activate_venv.bat): Windows venv activation script

---

## 🐳 Docker

Alternatively, you can use Docker:

```sh
docker-compose up --build
```