#!/bin/bash
set -e

# Ensure Python can resolve `app/` as a package
export PYTHONPATH=/app

# Start Flask backend with Waitress
echo "Starting Flask server with Waitress..."
python server.py