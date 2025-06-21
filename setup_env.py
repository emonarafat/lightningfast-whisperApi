import os
import subprocess
import sys
import shutil
import webbrowser
import platform
import http.client
import time
from datetime import datetime

VENV_DIR = ".venv"
REQUIREMENTS = "requirements.txt"
TERMINAL_WIDTH = 100

class Style:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"
    GRAY = "\033[90m"

def log(msg, icon="🔹", color=Style.BLUE):
    timestamp = datetime.now().strftime("%H:%M:%S")
    line = f"[{timestamp}] {icon} {msg}"
    print(f"{Style.GRAY}{line.ljust(TERMINAL_WIDTH)}{Style.RESET}")

def show_banner():
    banner = f'''
{Style.CYAN}{Style.BOLD}
┌────────────────────────────────────────────────────────────────────────────┐
│                          APICAL ENVIRONMENT LAUNCHER                       │
├────────────────────────────────────────────────────────────────────────────┤
│  A streamlined CLI tool to bootstrap your Python environment with style.   │
│                                                                            │
│  Author : Yaseer Arafat                                                    │
│  Version: 1.0.0                                                            │
└────────────────────────────────────────────────────────────────────────────┘
{Style.RESET}'''
    print(banner)

def clean_previous_env(preserve: bool):
    if preserve:
        log("Preserve mode enabled. Skipping cleanup of environment/scripts.", "🔒", Style.YELLOW)
        return
    if os.path.exists(VENV_DIR):
        log(f"Removing virtual environment at '{VENV_DIR}'...", "🗑️", Style.YELLOW)
        shutil.rmtree(VENV_DIR)
    for script in ["activate_venv.ps1", "activate_venv.sh"]:
        if os.path.exists(script):
            log(f"Deleting activation script: {script}", "🧹", Style.YELLOW)
            os.remove(script)

def create_venv():
    log(f"Creating virtual environment in '{VENV_DIR}'...", "🔧", Style.CYAN)
    subprocess.run([sys.executable, "-m", "venv", VENV_DIR], check=True)

def get_python_path():
    return os.path.join(VENV_DIR, "Scripts" if os.name == "nt" else "bin", "python")

def install_dependencies():
    python_exec = get_python_path()
    try:
        log("Upgrading pip...", "⬆️", Style.MAGENTA)
        subprocess.run([python_exec, "-m", "pip", "install", "--upgrade", "pip"], check=True)
    except subprocess.CalledProcessError:
        log("Failed to upgrade pip. You may need to update manually.", "⚠️", Style.RED)

    if os.path.exists(REQUIREMENTS):
        log(f"Installing from '{REQUIREMENTS}'...", "📦", Style.MAGENTA)
        subprocess.run([python_exec, "-m", "pip", "install", "-r", REQUIREMENTS], check=True)
    else:
        log(f"'{REQUIREMENTS}' not found. Creating a sample file...", "⚠️", Style.YELLOW)
        with open(REQUIREMENTS, "w", encoding="utf-8") as f:
            f.write("# Add your packages here\nfastapi\nuvicorn\n")
        log("Sample requirements.txt created.", "📄", Style.GREEN)

def install_and_freeze():
    install_dependencies()
    python_exec = get_python_path()
    log("Freezing installed packages to requirements.txt...", "🧊", Style.CYAN)
    with open(REQUIREMENTS, "w", encoding="utf-8") as f:
        subprocess.run([python_exec, "-m", "pip", "freeze"], stdout=f, check=True)
    log("Updated requirements.txt with currently installed packages.", "📄", Style.GREEN)

def write_activation_script():
    filename = "activate_venv.ps1" if os.name == "nt" else "activate_venv.sh"
    content = (
        f'Write-Host "🔄 Activating virtual environment..."\n& "{VENV_DIR}\\Scripts\\Activate.ps1"\n'
        if os.name == "nt"
        else f'#!/bin/bash\necho "🔄 Activating virtual environment..."\nsource {VENV_DIR}/bin/activate\nexec "$SHELL"\n'
    )
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    os.chmod(filename, 0o755)
    log(f"Activation script created: {filename}", "🚀", Style.CYAN)

def print_env_summary():
    log(f"Python version: {sys.version.split()[0]}", "🐍", Style.GRAY)
    log(f"Platform: {platform.system()} {platform.release()}", "💻", Style.GRAY)
    script_hint = "activate_venv.ps1" if os.name == "nt" else "source activate_venv.sh"
    log(f"To activate the environment, run: {script_hint}", "👉", Style.YELLOW)

def run_web_server():
    log("Starting Whisper API with Uvicorn...", "🌐", Style.CYAN)
    python_exec = os.path.join(VENV_DIR, "Scripts", "python.exe") if os.name == "nt" else os.path.join(VENV_DIR, "bin", "python")
    if not os.path.exists(python_exec):
        log("❌ Virtual environment not found. Please run setup first.", "⚠️", Style.RED)
        return

    def is_server_running():
        try:
            conn = http.client.HTTPConnection("localhost", 8000, timeout=2)
            conn.request("GET", "/health")
            response = conn.getresponse()
            return response.status == 200
        except:
            return False

    if is_server_running():
        log("✅ Whisper API is already running at http://localhost:8000", "🟢", Style.GREEN)
        try:
            webbrowser.open("http://localhost:8000/docs")
        except:
            pass
        return

    try:
        subprocess.Popen([
            python_exec, "-m", "uvicorn",
            "main:app", "--host", "0.0.0.0", "--port", "8000"
        ])
        log("⏳ Waiting for server to start...", "⏱️", Style.YELLOW)
        for _ in range(10):
            if is_server_running():
                log("✅ Whisper API is live at http://localhost:8000", "🚀", Style.GREEN)
                try:
                    webbrowser.open("http://localhost:8000/docs")
                except:
                    pass
                return
            time.sleep(1)
        log("⚠️ Server did not respond in time. Check logs for issues.", "⌛", Style.RED)
    except Exception as e:
        log(f"❌ Failed to launch API server: {e}", "🚫", Style.RED)

def interactive_menu():
    show_banner()
    while True:
        print(f"""\n{Style.BOLD}{Style.CYAN}=== Python Env Setup Menu ==={Style.RESET}
  1. Fresh Setup (delete venv + rebuild)
  2. Preserve existing environment
  3. Refresh requirements.txt (install + freeze)
  4. Start Whisper API server 🌐
  0. Exit
""")
        choice = input("Select an option (0–4): ").strip()
        if choice == "1":
            clean_previous_env(preserve=False)
            create_venv()
            write_activation_script()
            install_dependencies()
            print_env_summary()
            log("Setup complete.", "✅", Style.GREEN)
        elif choice == "2":
            clean_previous_env(preserve=True)
            if not os.path.exists(VENV_DIR):
                create_venv()
            write_activation_script()
            install_dependencies()
            print_env_summary()
            log("Preserved setup complete.", "✅", Style.GREEN)
        elif choice == "3":
            if os.path.exists(REQUIREMENTS):
                edit = input("📄 Edit requirements.txt before installing? [y/N]: ").strip().lower()
                if edit == "y":
                    try:
                        if os.name == "nt":
                            os.system(f'start "" "{REQUIREMENTS}"')
                        elif sys.platform == "darwin":
                            os.system(f"open {REQUIREMENTS}")
                        else:
                            os.system(f"xdg-open {REQUIREMENTS}")
                        input("📝 Press Enter when done editing...")
                    except Exception as e:
                        log(f"Could not open file: {e}", "⚠️", Style.RED)
                else:
                    print("\n📦 Add packages interactively. Press Enter to skip.")
                    while True:
                        pkg = input("➕ Add package (or leave blank to finish): ").strip()
                        if not pkg:
                            break
                        with open(REQUIREMENTS, "a", encoding="utf-8") as f:
                            f.write(f"{pkg}\n")
            else:
                print("\n📦 No requirements.txt found. Let's add packages:")
                with open(REQUIREMENTS, "