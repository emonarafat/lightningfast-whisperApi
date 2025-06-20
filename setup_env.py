import os
import subprocess
import sys
import platform

VENV_DIR = ".venv"
REQUIREMENTS = "requirements.txt"

def create_venv():
    print(f"🔧 Creating virtual environment in '{VENV_DIR}'...")
    subprocess.run([sys.executable, "-m", "venv", VENV_DIR], check=True)

def get_shell_activation_command():
    if os.name == "nt":
        return f"{VENV_DIR}\\Scripts\\activate"
    else:
        return f"source {VENV_DIR}/bin/activate"

def install_dependencies():
    pip_exec = os.path.join(VENV_DIR, "Scripts" if os.name == "nt" else "bin", "pip")

    if os.path.exists(REQUIREMENTS):
        print(f"\n📦 Installing dependencies from {REQUIREMENTS}...")
        subprocess.run([pip_exec, "install", "-r", REQUIREMENTS], check=True)
    else:
        print(f"\n⚠️ No {REQUIREMENTS} found. Creating a starter file...")
        with open(REQUIREMENTS, "w") as f:
            f.write("# Add your packages here\nfastapi\nuvicorn\n")
        print("📄 Created sample requirements.txt")

def write_activation_helper():
    filename = "activate_venv"
    if os.name == "nt":
        filename += ".bat"
        content = f"@echo off\ncall {VENV_DIR}\\Scripts\\activate.bat\ncmd"
    else:
        filename += ".sh"
        content = f"#!/bin/bash\nsource {VENV_DIR}/bin/activate\nexec \"$SHELL\""

    with open(filename, "w") as f:
        f.write(content)
    os.chmod(filename, 0o755)

    print(f"\n🚀 Run this to activate your venv: ./{filename}")

def main():
    create_venv()
    install_dependencies()
    write_activation_helper()

if __name__ == "__main__":
    main()
