"""
Single point of contact with the Groq API. Every AI-powered feature routes
through this module — no other file imports the Groq SDK directly.

Handles: missing/invalid key, timeouts, network errors, empty/invalid
responses, and retries. Converts all failures into typed exceptions the
UI layer can catch and show a friendly message for.
"""
import json
import logging
import time
from typing import Optional

import config

logger = logging.getLogger("smart_health.ai_client")


class AIError(Exception):
    """Base class for AI-related failures."""


class AIKeyMissingError(AIError):
    pass


class AIUnavailableError(AIError):
    pass


class AIInvalidResponseError(AIError):
    pass


def _get_client():
    if not config.GROQ_API_KEY:
        raise AIKeyMissingError(
            "The AI assistant is not configured. Please set GROQ_API_KEY in your .env file."
        )
    try:
        from groq import Groq
    except ImportError as e:
        raise AIUnavailableError("The 'groq' package is not installed.") from e
    return Groq(api_key=config.GROQ_API_KEY, timeout=config.AI_REQUEST_TIMEOUT)


def chat(system_prompt: str, user_prompt: str, model: Optional[str] = None,
         temperature: float = 0.5, json_mode: bool = False) -> str:
    """
    Sends a single-turn structured request to Groq. Returns the raw text
    content. Raises AIError subclasses on any failure — callers must catch.
    """
    client = _get_client()
    model = model or config.GROQ_TEXT_MODEL

    last_error = None
    for attempt in range(config.AI_MAX_RETRIES + 1):
        try:
            kwargs = dict(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=1500,
            )
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}

            response = client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content
            if not content or not content.strip():
                raise AIInvalidResponseError("The AI returned an empty response.")
            return content.strip()

        except AIInvalidResponseError:
            raise
        except Exception as e:  # broad: covers groq.APIError, timeouts, connection errors
            last_error = e
            logger.warning("AI call failed (attempt %s/%s): %s", attempt + 1, config.AI_MAX_RETRIES + 1, e)
            if attempt < config.AI_MAX_RETRIES:
                time.sleep(1.2 * (attempt + 1))
                continue

    raise AIUnavailableError(
        "The AI assistant is temporarily unavailable. Please try again in a moment."
    ) from last_error


def chat_json(system_prompt: str, user_prompt: str, model: Optional[str] = None,
              temperature: float = 0.4) -> dict:
    """Same as chat(), but parses and validates a JSON object response."""
    raw = chat(system_prompt, user_prompt, model=model, temperature=temperature, json_mode=True)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Attempt to salvage JSON embedded in extra text
        start, end = raw.find("{"), raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(raw[start:end + 1])
            except json.JSONDecodeError:
                pass
        raise AIInvalidResponseError("The AI response could not be parsed as structured data.")


def analyze_image(system_prompt: str, user_prompt: str, image_b64: str,
                   mime_type: str = "image/jpeg") -> str:
    """Vision-capable request for the meal analyzer."""
    client = _get_client()
    try:
        response = client.chat.completions.create(
            model=config.GROQ_VISION_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_b64}"}},
                    ],
                },
            ],
            temperature=0.3,
            max_tokens=1000,
        )
        content = response.choices[0].message.content
        if not content or not content.strip():
            raise AIInvalidResponseError("The AI returned an empty response for this image.")
        return content.strip()
    except AIInvalidResponseError:
        raise
    except Exception as e:
        logger.warning("Image analysis failed: %s", e)
        raise AIUnavailableError("Image analysis is temporarily unavailable. Please try again.") from e
