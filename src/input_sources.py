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
        return self.ocr_reader.extract_text(raw_input)


class TextInputSource(InputSource):
    """Returns the text input directly."""

    def get_text(self, raw_input: str) -> str:
        """Strip and return the raw text input."""
        return raw_input.strip()


class VoiceInputSource(InputSource):
    """Captures audio from the microphone and transcribes it."""

    PHRASE_TIME_LIMIT = 15

    def get_text(self, raw_input=None) -> str:
        """Record from microphone (up to 15 seconds) and return transcribed text."""
        import speech_recognition as sr

        recognizer = sr.Recognizer()
        recognizer.pause_threshold = 1.0  # seconds of silence before stopping
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, phrase_time_limit=self.PHRASE_TIME_LIMIT)
        return recognizer.recognize_google(audio)
