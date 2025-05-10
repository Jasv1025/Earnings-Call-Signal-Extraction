# Base image
FROM python:3.10-slim

# ---- Install Ollama dependencies ----
RUN apt-get update && \
    apt-get install -y curl unzip git && \
    rm -rf /var/lib/apt/lists/*

# ---- Install Ollama ----
RUN curl -fsSL https://ollama.com/install.sh | bash

# ---- Install Python dependencies ----
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Copy the rest of the Python code ----
COPY . .

# ---- Pull model so it's ready at startup ----
RUN ollama pull mixtral

# ---- Run both Ollama and Flask ----
# You can use a process manager to run both, like `bash -c`
CMD bash -c "ollama serve & python server.py"