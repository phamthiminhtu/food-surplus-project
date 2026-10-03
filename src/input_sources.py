from abc import ABC, abstractmethod

from .ocr import OcrReader


class InputSource(ABC):
    """Abstract base class for all input sources."""

    @abstractmethod
    def get_text(self, raw_input=None) -> str:
        """Return raw text extracted from this input source."""


class ImageInputSource(InputSource):
    """Extracts text from image bytes via OCR."""

    def __init__(self):
        self.ocr_reader = OcrReader()

    def get_text(self, raw_input: bytes) -> str:
        """Extract text from image bytes using OcrReader."""
        raise NotImplementedError


class TextInputSource(InputSource):
    """Returns the text input directly."""

    def get_text(self, raw_input: str) -> str:
        """Strip and return the raw text input."""
        return raw_input.strip()


class VoiceInputSource(InputSource):
    """Captures audio from the microphone and transcribes it."""

    def get_text(self, raw_input=None) -> str:
        """Record from microphone for 5 seconds and return transcribed text."""
        raise NotImplementedError
