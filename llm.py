import json
import re
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:3b"

PROMPT_TEMPLATE = """Extract food donation details from this description. Return ONLY valid JSON, no explanation.

Description:
{text}

JSON format:
{{
  "food_name": "string",
  "quantity": "string (e.g. 5 kg, 20 units)",
  "expiry_date": "YYYY-MM-DD or empty string if unknown",
  "allergens": ["list of allergens, empty array if none"],
  "storage": "e.g. refrigerated, room temperature, frozen",
  "confidence": "high or low"
}}"""


def extract_donation(text: str) -> dict:
    payload = {
        "model": MODEL,
        "prompt": PROMPT_TEMPLATE.format(text=text),
        "stream": False,
    }
    response = requests.post(OLLAMA_URL, json=payload, timeout=60)
    response.raise_for_status()
    raw = response.json()["response"]

    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON in LLM response: {raw}")

    return json.loads(match.group())
