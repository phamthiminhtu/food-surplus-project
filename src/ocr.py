import io

from PIL import Image, ImageFilter, ImageEnhance, ExifTags
from pillow_heif import register_heif_opener

class OcrReader:
    """Extracts text from image bytes using pytesseract."""

    @staticmethod
    def _open_image(image_bytes: bytes) -> Image.Image:
        """Open image bytes and correct EXIF rotation."""
        image = Image.open(io.BytesIO(image_bytes))

        try:
            exif = image.getexif()
            orientation_tag = next(k for k, v in ExifTags.TAGS.items() if v == "Orientation")
            orientation = exif.get(orientation_tag)
            rotations = {3: 180, 6: 270, 8: 90}
            if orientation in rotations:
                image = image.rotate(rotations[orientation], expand=True)
        except (StopIteration, AttributeError):
            pass

        return image

    def extract_text(self, image_bytes: bytes) -> str:
        """Extract text via pytesseract with contrast/sharpness preprocessing."""
        import pytesseract

        image = self._open_image(image_bytes).convert("L")
        image = ImageEnhance.Contrast(image).enhance(2.0)
        image = image.filter(ImageFilter.SHARPEN)
        return pytesseract.image_to_string(image, config="--psm 6").strip()
