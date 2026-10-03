import json
import re
from datetime import date

import requests

from .models import DonationData
from .ocr import OcrReader


class DonationExtractor:
    """Extracts structured donation data from raw text or images using an LLM."""

    OLLAMA_URL = "http://localhost:11434/api/generate"
    TEXT_MODEL = "llama3.2:3b"
    JSON_SCHEMA = """{
  "food_name": "string",
  "quantity": "string, e.g. '10 kg' or '5 packs'",
  "expiry_date": "YYYY-MM-DD or \"\" if unknown",
  "allergens": ["list", "of", "allergens"],
  "storage": "storage conditions or \"\" if unknown",
  "confidence": "high / medium / low"
}"""
    @property
    def TEXT_PROMPT_PREFIX(self):
        return (
            f"Today's date is {date.today()}. "
            "Extract food donation details from this description. Return ONLY valid JSON, no explanation.\n\n"
            "Description:\n"
        )
    TEXT_PROMPT_SUFFIX = "\n\nJSON format:\n" + JSON_SCHEMA

    def extract(self, raw_text: str) -> DonationData:
        """Send raw_text to Ollama text model and return a DonationData instance."""
        prompt = self.TEXT_PROMPT_PREFIX + raw_text + self.TEXT_PROMPT_SUFFIX
        response = requests.post(
            self.OLLAMA_URL,
            json={"model": self.TEXT_MODEL, "prompt": prompt, "stream": False, "format": "json"},
            timeout=60,
        )
        response.raise_for_status()
        raw_response = response.json()["response"]
        return DonationData.from_dict(self._parse_llm_response(raw_response))

    def extract_from_image(self, image_bytes: bytes) -> DonationData:
        """Run OCR on image bytes, then extract donation data with the text model."""
        ocr_text = OcrReader().extract_text(image_bytes)
        return self.extract(ocr_text)

    def _parse_llm_response(self, raw_response: str) -> dict:
        """Extract the first valid JSON object from a raw LLM response string."""
        # Strip markdown code fences (```json ... ``` or ``` ... ```)
        text = re.sub(r"```(?:json)?", "", raw_response).strip()
        decoder = json.JSONDecoder()
        for match in re.finditer(r"\{", text):
            try:
                obj, _ = decoder.raw_decode(text, match.start())
                if isinstance(obj, dict):
                    return obj
            except json.JSONDecodeError:
                continue
        raise ValueError(f"No JSON in LLM response: {raw_response!r}")
