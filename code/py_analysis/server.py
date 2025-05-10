from flask import Flask, request, jsonify
from app.analyze import analyze_with_ollama, analyze_with_openai

app = Flask(__name__)

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.json
    transcript = data.get("transcript", "")
    provider = data.get("provider", "ollama").lower()

    if provider == "ollama":
        result = analyze_with_ollama(transcript)
    elif provider == "openai":
        result = analyze_with_openai(transcript)
    else:
        return jsonify({"error": "Invalid provider"}), 400

    return jsonify(result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)