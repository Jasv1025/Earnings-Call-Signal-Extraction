#!/bin/bash
set -e

# Start Ollama in background
ollama serve &
echo "Ollama started..."

# Wait until Ollama is ready to accept requests
until curl -s http://localhost:11434 > /dev/null; do
  echo "Waiting for Ollama to be ready..."
  sleep 1
done

# Pull the Mixtral model
MODEL=${OLLAMA_MODEL:-mistral}
if ! curl -s http://localhost:11434/api/tags | grep -q "$MODEL"; then
  echo "Pulling model: $MODEL"
  ollama pull "$MODEL"
else
  echo "Model '$MODEL' already pulled."
fi

# Ensure Python can resolve `app/` as a package
export PYTHONPATH=/app

# Start Flask backend with Waitress
echo "Starting Flask server with Waitress..."
python server.py