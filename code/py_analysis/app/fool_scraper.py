import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from typing import Dict

# Attempt to infer the fiscal quarter from the transcript URL
def detect_quarter_from_url(url: str) -> str:
    match = re.search(r"q([1-4])-(\d{4})", url.lower())
    if match:
        return f"Q{match.group(1)} {match.group(2)}"
    return "Unknown"

# Extract the date in YYYY-MM-DD format from the URL path
def extract_date_from_url(url: str) -> str:
    match = re.search(r"/(\d{4})/(\d{2})/(\d{2})/", url)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    return datetime.today().strftime("%Y-%m-%d")

# Scrape and extract transcript sections from a Motley Fool article
def scrape_transcript_from_url(url: str) -> Dict | None:
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        # Attempt to locate the main article content
        content_div = soup.find("div", class_="article-content")
        if not content_div:
            # Fallback: search for a <div> with "content" in its class name
            for div in soup.find_all("div"):
                classes = div.get("class", [])
                if any("content" in c.lower() for c in classes):
                    content_div = div
                    break

        if not content_div:
            print(f"[WARN] No content found at {url}")
            return None

        # Extract text from all relevant tags
        text_blocks = [tag.get_text(strip=True) for tag in content_div.find_all(["p", "h2", "strong"]) if tag.get_text(strip=True)]
        full_text = "\n".join(text_blocks)

        # Locate section headers using regular expressions
        prepared_header = re.search(r"(?i)Prepared Remarks:?", full_text)
        qa_header = re.search(r"(?i)Questions & Answers:?", full_text)
        end_header = re.search(r"(?i)Call Participants:?", full_text)

        if not prepared_header or not qa_header:
            print(f"[WARN] Could not locate all sections in {url}")
            return None

        # Determine text boundaries
        start_prepared = prepared_header.end()
        start_qa = qa_header.end()
        end_idx = end_header.start() if end_header else len(full_text)

        operator_intro = full_text[:prepared_header.start()].strip()
        prepared_remarks = full_text[start_prepared:qa_header.start()].strip()
        qa_section = full_text[start_qa:end_idx].strip()

        return {
            "quarter": detect_quarter_from_url(url),
            "date": extract_date_from_url(url),
            "transcript": f"{prepared_remarks}\n\n{qa_section}".strip(),
            "prepared_remarks": prepared_remarks,
            "qa_section": qa_section,
            "operator_intro": operator_intro,
            "source": url
        }

    except Exception as e:
        print(f"[ERROR] Failed to scrape {url}: {e}")
        return None