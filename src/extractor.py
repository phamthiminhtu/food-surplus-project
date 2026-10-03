import json
import re

from .models import DonationData


class DonationExtractor:
    """Extracts structured donation data from raw text using an LLM."""

    OLLAMA_URL = "http://localhost:11434/api/generate"
    MODEL = "qwen2.5:3b"
    PROMPT_TEMPLATE = """Extract food donation details from this description. Return ONLY valid JSON, no explanation.

Description:
{text}

JSON format:
{{
  "product_name": "string",
  "product_description": "string",
  "category": "one of: bakery / fruit_veg / chilled / ambient / other",
  "quantity": number,
  "unit": "one of: each / kg / pack",
  "available_from": "YYYY-MM-DDTHH:MM:SS or empty string if unknown",
  "available_until": "YYYY-MM-DDTHH:MM:SS or empty string if unknown",
  "best_before_date": "YYYY-MM-DD or empty string if unknown",
  "store_id": "string or empty string if unknown",
  "weight_kg": "number or null",
  "unit_price": "number or null",
  "total_value": "number or null",
  "surplus_reason": "string or empty string if unknown"
}}"""

    def extract(self, raw_text: str) -> DonationData:
        """Send raw_text to the LLM and return a DonationData instance."""
        raise NotImplementedError

    def _parse_llm_response(self, raw_response: str) -> dict:
        """Extract the first JSON object from a raw LLM response string."""
        match = re.search(r"\{.*\}", raw_response, re.DOTALL)
        if not match:
            raise ValueError(f"No JSON in LLM response: {raw_response}")
        return json.loads(match.group())
