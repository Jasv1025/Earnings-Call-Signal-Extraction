import os
import re
import json
import time
from pathlib import Path
import requests
from dotenv import load_dotenv
from typing import List

load_dotenv()

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mixtral")
CACHE_DIR = f"cache_{OLLAMA_MODEL}"
PROGRESS_PATH = "progress.json"

os.makedirs(CACHE_DIR, exist_ok=True)

def update_progress(message: str):
    with open(PROGRESS_PATH, "w", encoding="utf-8") as f:
        json.dump({"status": message, "timestamp": time.time()}, f)
        print(message)

def _cache_path(prompt: str, company: str, quarter: str, section_index: int = None, is_summary: int = 0, custom_suffix: str = None) -> Path:
    sanitized_company = re.sub(r'\W+', '', company.lower())
    sanitized_quarter = re.sub(r'\W+', '', quarter.upper())

    if custom_suffix:
        filename = f"{sanitized_company}_{sanitized_quarter}_{custom_suffix}.json"
    elif is_summary == 1:
        filename = f"{sanitized_company}_{sanitized_quarter}_summary.json"
    elif is_summary == 2:
        filename = f"{sanitized_company}_{sanitized_quarter}_tone.json"
    else:
        filename = f"{sanitized_company}_{sanitized_quarter}_{section_index}.json"

    return Path(CACHE_DIR) / filename

def _cached_or_call(prompt: str, path: Path) -> str:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)["content"]

    update_progress("Calling Mistral via Ollama...")

    response = requests.post(OLLAMA_URL, json={
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    })
    response.raise_for_status()

    try:
        content = response.json().get("response") or response.json().get("message", {}).get("content") or ""
    except Exception as e:
        print("Failed to parse Ollama response:", e)
        content = ""

    with open(path, "w", encoding="utf-8") as f:
        json.dump({"content": content}, f, indent=2)

    return content

def preprocess_transcript(text: str) -> str:
    cleaned = re.sub(r"You're reading a free article.*?Learn More", "", text, flags=re.DOTALL)
    cleaned = re.sub(r"\n{2,}", "\n", cleaned).strip()
    return cleaned

def split_long_text(text: str, max_len: int = 4000, min_len: int = 0) -> list:
    if len(text) <= max_len:
        return [text.strip()]

    parts = re.split(r"\n(?=\S)", text)
    chunks, current = [], ""

    for part in parts:
        if len(current) + len(part) < max_len:
            current += part + "\n"
        else:
            if len(current.strip()) >= min_len:
                chunks.append(current.strip())
            current = part + "\n"

    if len(current.strip()) >= min_len:
        chunks.append(current.strip())

    return chunks

def analyze_labeled_sections(prepared: str, qa: str, company: str = "NVIDIA", quarter: str = "QX", provider: str = "ollama") -> dict:
    update_progress("Preprocessing labeled sections")

    final_analysis = {
        "company": company,
        "provider": provider,
        "model": OLLAMA_MODEL,
        "signal": "labeled_analysis",
        "result": {}
    }

    labeled_inputs = {
        "management_sentiment": split_long_text(prepared),
        "qa_sentiment": split_long_text(qa),
    }

    section_outputs = {}

    for label, chunks in labeled_inputs.items():
        update_progress(f"Analyzing {label} ({len(chunks)} chunks)")
        outputs = []
        for i, chunk in enumerate(chunks):
            score_info = score_chunk_for_summary(chunk)

            update_progress(f"{label}: chunk {i + 1} of {len(chunks)}")
            #print(f"[INFO] {label} chunk {i}: score={score_info['score']} ({score_info['tag']}) — {score_info['reason']}")

            if label == "management_sentiment":
                prompt = f"""
                    You are an AI analyst evaluating this MANAGEMENT chunk from an earnings call for {company}.

                    Analyze it in detail and provide:
                    1. The overall tone (e.g., optimistic, confident, cautious, neutral). Briefly justify with phrases or language used.
                    2. The sentiment (Positive, Neutral, or Negative). Justify based on outlook, phrasing, or executive framing.
                    3. Any strategic themes or initiatives discussed — mention specific products, markets, or investments if applicable.
                    4. Any emotional cues (e.g., pride, urgency, excitement, concern).

                    Chunk:
                    {chunk}
                """
            elif label == "qa_sentiment":
                prompt = f"""
                    You are an AI analyst evaluating this Q&A chunk from an earnings call for {company}.

                    Analyze it in detail and provide:
                    1. The tone of the interaction (e.g., constructive, defensive, candid, optimistic).
                    2. The sentiment (Positive, Neutral, or Negative). Justify your rating.
                    3. What kind of question is being asked — is it challenging, supportive, financial, strategic?
                    4. How management responded — with confidence, ambiguity, enthusiasm, etc.
                    5. Any strategic signals or concerns that came up (e.g., costs, expansion, regulation).

                    Chunk:
                    {chunk}
                """

            path = _cache_path(prompt, company, quarter, i, is_summary=0)
            response = _cached_or_call(prompt, path) if provider == "ollama" else "[Only Ollama supported]"

            outputs.append({
                "summary": response,
                "score": score_info["score"],
                "reason": score_info["reason"],
                "chunk": chunk
            })

        section_outputs[label] = outputs

    strategy_chunks = [o["summary"] for o in section_outputs.get("management_sentiment", []) if o["score"] > 0]
    strategy_prompt = summarize_responses_prompt(strategy_chunks, "strategic_focuses", company)
    strategy_path = _cache_path(strategy_prompt, company, quarter, custom_suffix="strategic_summary", is_summary=1)
    strategic_summary = _cached_or_call(strategy_prompt, strategy_path)
    final_analysis["result"]["strategic_focuses"] = strategic_summary

    for label, outputs in section_outputs.items():
        filtered_outputs = [o["summary"] for o in outputs if o["score"] > 0]
        if not filtered_outputs:
            print(f"[WARN] No high-signal chunks found for {label}, skipping summary.")
            final_analysis["result"][label] = "No high-quality input found for summary."
            continue

        summary_prompt = summarize_responses_prompt(filtered_outputs, label, company)
        summary_path = _cache_path(summary_prompt, company, quarter, custom_suffix=f"{label}_summary", is_summary=1)
        summary = _cached_or_call(summary_prompt, summary_path)
        final_analysis["result"][label] = summary

    overall_prompt = f"""
        You are a financial analyst summarizing the {quarter} earnings call for {company}.

        Use the following summaries to craft a cohesive 4-5 paragraph overview:

        MANAGEMENT SENTIMENT:
        {final_analysis['result']['management_sentiment']}

        Q&A SENTIMENT:
        {final_analysis['result']['qa_sentiment']}

        STRATEGIC THEMES:
        {final_analysis['result']['strategic_focuses']}
    """
    overall_path = _cache_path(overall_prompt, company, quarter, is_summary=1)
    overall_summary = _cached_or_call(overall_prompt, overall_path)
    final_analysis["result"]["summary"] = overall_summary

    return final_analysis

def score_chunk_for_summary(chunk_text: str) -> dict:
    text = chunk_text.strip().lower()
    if re.match(r"^operator[\\s,:]", text) or "conference operator" in text or "all lines have been placed on mute" in text:
        return {
            "score": 0,
            "tag": "operator_logistics",
            "reason": "Procedural intro — not exec content"
        }

    exec_names = ["jensen huang", "colette kress", "cfo", "ceo"]
    mentions_exec = any(name in text for name in exec_names)

    strategy_terms = [
        "ai", "training", "inference", "data center", "cloud", "enterprise", "gross margin", "supply chain",
        "export", "regulation", "autonomous", "sovereign", "robotics", "simulation", "digital twin",
        "infrastructure", "platform", "ecosystem", "open source", "scaling", "monetization", "networking",
        "demand", "growth", "revenue", "market", "segment", "margin", "tariff", "customers", "csp",
        "cost", "throughput", "ramp", "manufacturing"
    ]
    match_count = sum(term in text for term in strategy_terms)

    financial_cues = [
        "revenue", "guidance", "fiscal", "quarter", "sequential", "yoy", "qoq", "dollars", "billion"
    ]
    financial_weight = sum(term in text for term in financial_cues)

    tone_terms = [
        "confident", "excited", "optimistic", "cautious", "challenging", "strong", "headwinds", "visibility"
    ]
    tone_weight = sum(term in text for term in tone_terms)

    score = (2 if mentions_exec else 0) + match_count + financial_weight + tone_weight
    tag = "high" if score >= 6 else "medium" if score >= 3 else "low"

    return {
        "score": score,
        "tag": tag,
        "reason": f"{'Exec mentioned. ' if mentions_exec else ''}{match_count} strategy terms, {financial_weight} financial cues, {tone_weight} tone cues"
    }

def summarize_responses_prompt(chunks: List[str], section_type: str, company: str = "NVIDIA") -> str:
    prompt_header = {
        "management_sentiment": f"""You are given multiple sentiment evaluations from different sections of the MANAGEMENT portion of a quarterly earnings call for {company}.

            Your task is to synthesize a comprehensive summary that includes:

            1. The overall tone and sentiment expressed by executives — label this as Positive, Neutral, or Negative.
            2. Specific quotes or paraphrased language that reflect emotional cues such as confidence, excitement, or concern.
            3. A breakdown of strategic themes mentioned repeatedly, including product launches, market outlook, and investment priorities.
            4. Any shifts in tone within the section (e.g., early optimism followed by cautious remarks).
            5. Any external factors (e.g. macroeconomy, regulation) mentioned as influencing company direction.

            Responses:
            """,

        "qa_sentiment": f"""You are given multiple sentiment evaluations from the Q&A section of a quarterly earnings call for {company}.

            Please write a detailed summary that includes:

            1. The overall sentiment and tone expressed during the Q&A — label this as Positive, Neutral, or Negative.
            2. The nature of the questions asked — were they optimistic, critical, skeptical, etc.?
            3. How the executives responded — were they confident, defensive, vague, transparent?
            4. Any recurring concerns raised by analysts (e.g. supply constraints, margins).
            5. Quotes or phrasing that show tone shifts or reinforce sentiment.

            Responses:
            """,

        "strategic_focuses": f"""You are given a set of raw executive statements from the MANAGEMENT portion of a quarterly earnings call for {company}.
        
            **Do not** list analyst questions or repeat what was asked. **Do not ask any questions yourself**. The information provided is all that is avalible. There should not be a single question in the response.

            Your job is to identify and rank the 4–6 most prominent strategic themes or initiatives discussed.

            For each theme:
            1. Create a short, clear **title** for each strategic theme (e.g., “AI Factory Expansion”, “Automotive Platform Growth”).
            2. Write a concise **1–2 sentence summary** of what was said about it, combining multiple mentions if relevant.
            3. Specify whether it is a **Current Achievement**, a **Future Initiative**, or **Both**.

            Prioritize themes that appear multiple times, are emphasized by executives, or are tied to specific products, partnerships, or markets.
            **Focus on what NVIDIA emphasized as their goals or direction**, not what analysts asked about.
            Responses:
            """
    }
    
    body = "\n\n".join([f"{i+1}. {text.strip()}" for i, text in enumerate(chunks)])
    return prompt_header.get(section_type, "Responses:\n") + body

def compare_tone(summary1: str, summary2: str, company: str = "NVIDIA", quarter1: str = "Q1", quarter2: str = "Q2") -> str:
    prompt = f"""
        Compare the tone between these two quarterly earnings call excerpts for {company}.
        Summarize how the tone has changed — is it more optimistic, cautious, aggressive, concerned, etc.?

        {quarter1}:
        {summary1}

        {quarter2}:
        {summary2}
    """

    cache_id = f"{quarter1}_vs_{quarter2}"
    path = _cache_path(prompt, company, cache_id, None, is_summary=2)
    result = _cached_or_call(prompt, path)
    return result