# Base Python image
FROM python:3.10-slim

# Install dependencies
RUN apt-get update && \
    apt-get install -y curl unzip git && \
    rm -rf /var/lib/apt/lists/*

# Install Ollama CLI
RUN curl -fsSL https://ollama.com/install.sh | bash

# Set working directory inside container
WORKDIR /app

# Copy Python dependencies first and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files into container
COPY . .

# Ensure entrypoint is executable
RUN chmod +x entrypoint.sh

# Expose Flask + Ollama ports
EXPOSE 5000

# Entrypoint to run Ollama + Flask
CMD ["./entrypoint.sh"]