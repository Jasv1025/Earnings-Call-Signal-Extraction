from flask import Flask, jsonify, request
from flask_cors import CORS
from app.analyze import analyze_labeled_sections, compare_tone, _cache_path
from app.fool_scraper import scrape_transcript_from_url
import json
import time

# Initialize Flask app and enable CORS for development
app = Flask(__name__)
CORS(app, origins=["https://nvidia-frontend-7ojt.onrender.com", "http://localhost:3000"])

# Static list of earnings call transcript URLs (Motley Fool)
TRANSCRIPT_URLS = [
    "https://www.fool.com/earnings/call-transcripts/2025/02/26/nvidia-nvda-q4-2025-earnings-call-transcript/",
    "https://www.fool.com/earnings/call-transcripts/2024/11/20/nvidia-nvda-q3-2025-earnings-call-transcript/",
    "https://www.fool.com/earnings/call-transcripts/2024/08/28/nvidia-nvda-q2-2025-earnings-call-transcript/",
    "https://www.fool.com/earnings/call-transcripts/2024/05/29/nvidia-nvda-q1-2025-earnings-call-transcript/",
]

# Run analysis on the latest four transcripts and package results
def run_analyze_last_four(company="NVIDIA", provider="ollama"):
    raw_transcripts = [scrape_transcript_from_url(url) for url in TRANSCRIPT_URLS]
    results = []
    for t in raw_transcripts:
        quarter = t.get("quarter", "QX")
        analysis = analyze_labeled_sections(
            prepared=t.get("prepared_remarks", ""),
            qa=t.get("qa_section", ""),
            company=company,
            quarter=quarter,
            provider=provider
        )
        results.append({
            "quarter": t["quarter"],
            "date": t["date"],
            "analysis": {
                **analysis,
                "result": {
                    **analysis["result"],
                    "transcript": t.get("transcript", "")
                }
            }
        })
    return results

# Compute tone shift between adjacent quarters using cached summaries
def run_tone_shift(company="NVIDIA", provider="ollama"):
    def parse_quarter(quarter_str):
        q, year = quarter_str.upper().split()
        return int(year), int(q[1])

    scraped = [scrape_transcript_from_url(url) for url in TRANSCRIPT_URLS]
    scraped = [s for s in scraped if s is not None]
    scraped = sorted(scraped, key=lambda d: parse_quarter(d["quarter"]))
    comparisons = []

    for i in range(len(scraped) - 1):
        q1 = scraped[i]["quarter"]
        q2 = scraped[i + 1]["quarter"]

        path1 = _cache_path("", company, q1, None, is_summary=1)
        path2 = _cache_path("", company, q2, None, is_summary=1)

        if not path1.exists() or not path2.exists():
            print(f"[WARN] Missing summary cache for {q1} or {q2}, skipping...")
            continue

        with open(path1, "r", encoding="utf-8") as f1:
            summary1 = json.load(f1)["content"]

        with open(path2, "r", encoding="utf-8") as f2:
            summary2 = json.load(f2)["content"]

        result = compare_tone(summary1, summary2, company, q1, q2)

        comparisons.append({
            "from": q1,
            "to": q2,
            "result": result
        })

    return {
        "company": company,
        "signal": "tone_shift",
        "comparisons": comparisons
    }

# Route: root - returns both last-four analysis and tone shift
@app.route("/", methods=["GET"])
def analyze_all():
    print("[LOG] / route called")
    company = request.args.get("company", "NVIDIA")
    provider = request.args.get("provider", "ollama")
    last_four = run_analyze_last_four(company, provider)
    tone_shift = run_tone_shift(company, provider)
    return jsonify({
        "results": last_four,
        "tone_shift": tone_shift
    })

# Route: /analyze/last-four - returns structured analysis for each quarter
@app.route("/analyze/last-four", methods=["GET"])
def analyze_last_four():
    print('[LOG] /analyze/last-four called')
    company = request.args.get("company", "NVIDIA")
    provider = request.args.get("provider", "ollama")
    last_four = run_analyze_last_four(company, provider)
    return jsonify({
        "company": company,
        "results": last_four
    })

# Route: /analyze/tone-shift - returns comparison summaries
@app.route("/analyze/tone-shift", methods=["GET"])
def analyze_tone_shift():
    company = request.args.get("company", "NVIDIA")
    provider = request.args.get("provider", "ollama")
    return jsonify(run_tone_shift(company, provider))

# Route: /progress - returns JSON indicating current backend progress state
@app.route("/progress", methods=["GET"])
def progress():
    try:
        with open("progress.json", "r", encoding="utf-8") as f:
            return jsonify(json.load(f))
    except FileNotFoundError:
        return jsonify({"status": "Starting up...", "timestamp": time.time()})
    except Exception as e:
        return jsonify({"status": f"Error: {str(e)}", "timestamp": time.time()})

# Entry point: run Flask app with Waitress in production context
if __name__ == "__main__":
    from waitress import serve
    import os
    port = int(os.environ.get("PORT", 5000))
    print(f"[STARTUP] Waitress serving on port {port}...")
    print("[STARTUP] Registered routes:")
    serve(app, host="0.0.0.0", port=port)