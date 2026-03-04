#!/usr/bin/env bash
set -e

echo "==> NEXUS — Local Setup"

# 1. Python venv
echo "--> Setting up Python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "    Python deps installed."

# 2. Copy .env
if [ ! -f .env ]; then
  cp .env.example .env
  echo "    .env created from .env.example — please fill in your API keys."
else
  echo "    .env already exists, skipping."
fi

# 3. Initialize DB
echo "--> Initializing database..."
python -c "import asyncio; from src.db.database import init_db; asyncio.run(init_db())"
echo "    Database initialized."

# 4. Frontend
echo "--> Installing frontend dependencies..."
cd frontend && npm install && cd ..
echo "    Frontend deps installed."

# 5. Ollama check
if command -v ollama &>/dev/null; then
  echo "--> Ollama found. Run 'ollama pull qwen2.5:14b' if you haven't already."
else
  echo "--> Ollama not found. Install from https://ollama.ai and run 'ollama pull qwen2.5:14b'"
fi

echo ""
echo "==> Setup complete! To start:"
echo "    ollama serve                              # Terminal 1"
echo "    source .venv/bin/activate && uvicorn src.main:app --reload --port 8000  # Terminal 2"
echo "    cd frontend && npm run dev                # Terminal 3"
