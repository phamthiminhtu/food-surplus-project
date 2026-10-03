from PIL import Image
import io


def extract_text_from_image(image_bytes: bytes) -> str:
    """Try pytesseract first, fall back to easyocr, return empty string on failure."""
    try:
        import pytesseract
        image = Image.open(io.BytesIO(image_bytes))
        return pytesseract.image_to_string(image).strip()
    except Exception:
        pass

    try:
        import easyocr
        import numpy as np
        reader = easyocr.Reader(["en"], verbose=False)
        image = Image.open(io.BytesIO(image_bytes))
        results = reader.readtext(np.array(image), detail=0)
        return " ".join(results).strip()
    except Exception:
        pass

    return ""
