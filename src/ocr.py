class OcrReader:
    """Extracts text from image bytes, trying pytesseract then easyocr."""

    def extract_text(self, image_bytes: bytes) -> str:
        """Try pytesseract first, fall back to easyocr, return empty string on failure."""
        text = self._try_pytesseract(image_bytes)
        if text:
            return text
        return self._try_easyocr(image_bytes)

    def _try_pytesseract(self, image_bytes: bytes) -> str:
        """Extract text using pytesseract OCR."""
        try:
            import io
            import pytesseract
            from PIL import Image

            image = Image.open(io.BytesIO(image_bytes))
            return pytesseract.image_to_string(image).strip()
        except Exception:
            return ""

    def _try_easyocr(self, image_bytes: bytes) -> str:
        """Extract text using easyocr."""
        try:
            import io
            import numpy as np
            import easyocr
            from PIL import Image

            reader = easyocr.Reader(["en"], verbose=False)
            image = Image.open(io.BytesIO(image_bytes))
            results = reader.readtext(np.array(image), detail=0)
            return " ".join(results).strip()
        except Exception:
            return ""
