# NVIDIA Earnings Call Signal Extraction

This project is a full-stack AI-powered web application for retrieving, analyzing, and visualizing NVIDIA's earnings call transcripts from the last four quarters. It extracts management sentiment, Q&A sentiment, tone change between quarters, and strategic business focuses using LLM-based text analysis.

## Features

- **Automated Transcript Retrieval**: Scrapes full call transcripts from public sources (Motley Fool).
- **AI Signal Extraction**: Uses LLM (e.g., Mistral via Ollama) to analyze and summarize earnings calls.
- **Four Signal Types**:
  - Management Sentiment
  - Q&A Sentiment
  - Quarter-over-Quarter Tone Change
  - Strategic Focuses
- **Web Interface**: React + Tailwind-based dashboard for navigating signal types.
- **Backend Analysis Pipeline**: Flask server with modular NLP logic and caching.

## Directory Structure

```
Earnings-Call-Signal-Extraction/
├── code/
│   ├── pages/                  # Frontend pages (Next.js)
│   ├── styles/                 # Tailwind global styles
│   ├── py_analysis/            # Backend Flask + analysis engine
│   │   ├── app/
│   │   │   ├── analyze.py      # LLM analysis and tone modeling
│   │   │   ├── fool_scraper.py # Transcript scraper
│   │   └── server.py           # Flask API
│   ├── .env.local              # API endpoint for frontend (not committed)
│   ├── Dockerfile              # Shared Dockerfile for frontend/backend
│   └── docker-compose.yml      # Compose setup for dev environment
```

## Getting Started

### 1. Clone and Setup

```bash
git clone https://github.com/username/Earnings-Call-Signal-Extraction.git
cd Earnings-Call-Signal-Extraction
cp .env.local.example .env.local
```

### 2. Start the Application

```bash
docker-compose up --build
```

Access the frontend at: [http://localhost:3000](http://localhost:3000)  
Backend API will be served at: [http://localhost:5000](http://localhost:5000)

## .env.local Example

Create this in the root `code/` folder:

```env
NEXT_PUBLIC_API_URL=http://localhost:5000
```

## Technologies Used

- **Frontend**: Next.js, React, Tailwind CSS, Chart.js
- **Backend**: Flask, Ollama (Mistral), BeautifulSoup, dotenv
- **NLP Engine**: Local LLM via Ollama (default: `mixtral`)
- **Deployment**: Docker + Docker Compose

## API Endpoints

| Endpoint                  | Method | Description                                 |
|--------------------------|--------|---------------------------------------------|
| `/analyze/last-four`     | GET    | Returns structured analysis for 4 quarters  |
| `/analyze/tone-shift`    | GET    | Returns tone shift between adjacent quarters|
| `/progress`              | GET    | Reports current backend processing status   |

## Notes

- All analysis results are cached to disk by default.
- Full transcripts are scraped live; no API keys are required.
- LLM calls use `ollama` locally; ensure `ollama serve` is available inside the container.

## Caching System

To reduce response time and minimize unnecessary LLM usage, all generated content is cached locally on disk under the directory:

```
/code/py_analysis/cache_<model_name>/
```

Each prompt issued to the language model is hashed into a filename and saved with its generated response. This includes chunk-level outputs, strategic summaries, and tone comparisons.

### Notes on Cache Behavior

- Cached results will be reused automatically on subsequent runs.
- To force a fresh generation, **the cache directory must be manually deleted**.
- A full raw run (uncached), using the local `mixtral` model via Ollama, can take **approximately 4 hours** to complete due to hardware and model size constraints.

## License

This project is licensed under the MIT License.