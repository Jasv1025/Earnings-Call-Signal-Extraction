#!/bin/bash
set -e

echo "Cache directory contents:"
ls -l /app/cache_mistral

# Ensure Python can resolve `app/` as a package
export PYTHONPATH=/app

# Start Flask backend with Waitress
echo "Starting Flask server with Waitress..."
python server.py