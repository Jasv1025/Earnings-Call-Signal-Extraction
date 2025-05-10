import requests
import openai

# Config (or load from env)
openai.api_key = "YOUR_API_KEY"

def analyze_with_ollama(transcript: str) -> dict:
    response = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": "mixtral",
            "messages": [
                {"role": "user", "content": f"Analyze this NVIDIA earnings call for sentiment and strategic themes:\n\n{transcript}"}
            ],
            "stream": False
        }
    )
    return {"provider": "ollama", "result": response.json()["message"]["content"]}


def analyze_with_openai(transcript: str) -> dict:
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a financial NLP expert."},
            {"role": "user", "content": f"Analyze this NVIDIA earnings call for sentiment and strategic themes:\n\n{transcript}"}
        ]
    )
    return {"provider": "openai", "result": response["choices"][0]["message"]["content"]}