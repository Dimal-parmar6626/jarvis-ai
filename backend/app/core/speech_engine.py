"""Speech engine: speech-to-text and text-to-speech."""

import io
import logging
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class SpeechEngine:
    """Handles speech-to-text and text-to-speech operations."""

    def __init__(self, language: str = "en-US", tts_voice: str = "default"):
        self.language = language
        self.tts_voice = tts_voice
        self._recognizer = None
        self._tts_engine = None

    # ------------------------------------------------------------------
    # Speech-to-Text
    # ------------------------------------------------------------------

    def transcribe_audio_bytes(self, audio_bytes: bytes) -> str:
        """Transcribe raw audio bytes to text using Google Speech Recognition.

        Falls back to an empty string on any recognition error.
        """
        try:
            import speech_recognition as sr  # type: ignore

            recognizer = self._get_recognizer()
            audio_file = io.BytesIO(audio_bytes)
            with sr.AudioFile(audio_file) as source:
                audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language=self.language)
            logger.info("Transcribed audio: %s", text)
            return text
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Speech recognition failed: %s", exc)
            return ""

    def transcribe_audio_file(self, file_path: str) -> str:
        """Transcribe an audio file to text."""
        try:
            import speech_recognition as sr  # type: ignore

            recognizer = self._get_recognizer()
            with sr.AudioFile(file_path) as source:
                audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language=self.language)
            logger.info("Transcribed file %s: %s", file_path, text)
            return text
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Failed to transcribe file %s: %s", file_path, exc)
            return ""

    # ------------------------------------------------------------------
    # Text-to-Speech
    # ------------------------------------------------------------------

    def synthesize_to_bytes(self, text: str) -> bytes:
        """Convert text to speech and return audio bytes (mp3 via gTTS)."""
        try:
            from gtts import gTTS  # type: ignore

            lang_code = self.language.split("-")[0]
            tts = gTTS(text=text, lang=lang_code, slow=False)
            buffer = io.BytesIO()
            tts.write_to_fp(buffer)
            buffer.seek(0)
            return buffer.read()
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("gTTS synthesis failed: %s", exc)
            return b""

    def speak(self, text: str) -> None:
        """Speak text aloud using pyttsx3 (blocking)."""
        try:
            engine = self._get_tts_engine()
            engine.say(text)
            engine.runAndWait()
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("pyttsx3 speak failed: %s", exc)

    def save_speech(self, text: str, output_path: str) -> bool:
        """Save synthesized speech to a file."""
        try:
            engine = self._get_tts_engine()
            engine.save_to_file(text, output_path)
            engine.runAndWait()
            return True
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Failed to save speech: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_recognizer(self):
        if self._recognizer is None:
            import speech_recognition as sr  # type: ignore

            self._recognizer = sr.Recognizer()
            self._recognizer.energy_threshold = 300
            self._recognizer.dynamic_energy_threshold = True
        return self._recognizer

    def _get_tts_engine(self):
        if self._tts_engine is None:
            import pyttsx3  # type: ignore

            self._tts_engine = pyttsx3.init()
            voices = self._tts_engine.getProperty("voices")
            if voices:
                self._tts_engine.setProperty("voice", voices[0].id)
            self._tts_engine.setProperty("rate", 175)
            self._tts_engine.setProperty("volume", 0.9)
        return self._tts_engine
