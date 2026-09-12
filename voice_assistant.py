"""
Voice input wrapper. Designed to degrade gracefully: if the microphone
library or hardware is unavailable, the app continues to work with text
input only — no feature is blocked.
"""
import logging

logger = logging.getLogger("smart_health.voice")


def is_voice_available() -> bool:
    try:
        import speech_recognition  # noqa: F401
        return True
    except ImportError:
        return False


def transcribe_audio_bytes(audio_bytes: bytes) -> tuple[bool, str]:
    """
    Attempts to transcribe recorded audio to text.
    Returns (success, text_or_error_message).
    """
    if not is_voice_available():
        return False, "Voice recognition is not available in this environment. Please type your question instead."

    try:
        import speech_recognition as sr
        import io

        recognizer = sr.Recognizer()
        with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
            audio = recognizer.record(source)
        text = recognizer.recognize_google(audio)
        return True, text
    except sr.UnknownValueError:
        return False, "Sorry, I couldn't understand the audio. Please try again or type your question."
    except sr.RequestError:
        return False, "Voice recognition service is unavailable right now. Please type your question instead."
    except Exception as e:
        logger.warning("Voice transcription failed: %s", e)
        return False, "Something went wrong processing the audio. Please type your question instead."
