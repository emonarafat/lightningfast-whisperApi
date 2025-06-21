#!/bin/bash

clear
echo "============================================="
echo "        Python Env Setup Launcher (WSL)"
echo "============================================="
echo
echo "  [1] Run setup_env.py"
echo "  [2] Activate virtual environment"
echo "  [0] Exit"
echo
read -p "Enter your choice (0–2): " choice

if [ "$choice" == "1" ]; then
  echo
  echo "Running setup_env.py..."
  python3 setup_env.py

elif [ "$choice" == "2" ]; then
  echo
  echo "Activating virtual environment..."
  source .venv/bin/activate
  echo
  echo "✅ Virtual environment activated."
  echo "ℹ️ To start the Whisper API server, run:"
  echo
  echo "   uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
  echo
  exec "$SHELL"

elif [ "$choice" == "0" ]; then
  echo "Exiting..."
  exit 0

else
  echo "Invalid option"
fi
