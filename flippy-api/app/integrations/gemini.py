"""Thin streaming wrapper over Google Gemini 2.0 Flash (Generative Language API)."""
import json
from typing import Iterator

import httpx

from app.core.config import settings

MODEL = "gemini-2.5-flash"
BASE_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:streamGenerateContent"


class GeminiError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(message)


def stream_chat(system_prompt: str, contents: list[dict]) -> Iterator[str]:
    """Yields incremental text chunks from Gemini's streaming response (SSE)."""
    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": contents,
    }

    with httpx.stream(
        "POST",
        BASE_URL,
        params={"key": settings.google_api_key, "alt": "sse"},
        json=payload,
        timeout=60,
    ) as response:
        if response.status_code >= 400:
            response.read()
            raise GeminiError(response.status_code, response.text)

        # Decode UTF-8 explicitly at the byte level: httpx's iter_lines() auto-detects
        # encoding per chunk and can mis-guess it for small SSE fragments, corrupting
        # accented characters. Buffering raw bytes until each full line avoids that.
        buffer = b""
        for raw_bytes in response.iter_bytes():
            buffer += raw_bytes
            while b"\n" in buffer:
                line_bytes, buffer = buffer.split(b"\n", 1)
                line = line_bytes.decode("utf-8").rstrip("\r")
                if not line or not line.startswith("data: "):
                    continue
                raw = line[len("data: ") :]
                if raw.strip() == "[DONE]":
                    return
                chunk = json.loads(raw)
                for candidate in chunk.get("candidates", []):
                    for part in candidate.get("content", {}).get("parts", []):
                        text = part.get("text")
                        if text:
                            yield text
