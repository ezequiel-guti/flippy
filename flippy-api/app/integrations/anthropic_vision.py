"""Thin streaming wrapper over Anthropic Claude 3.5 Sonnet (Messages API), used only for
user-uploaded image analysis (F-04). Text-only chat stays on Gemini (see gemini.py)."""
import json
from typing import Iterator

import httpx

from app.core.config import settings

MODEL = "claude-3-5-sonnet-20241022"
BASE_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
MAX_TOKENS = 1024


class AnthropicError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(message)


def stream_vision(system_prompt: str, messages: list[dict]) -> Iterator[str]:
    """Yields incremental text chunks from Claude's streaming response (SSE)."""
    payload = {
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "system": system_prompt,
        "messages": messages,
        "stream": True,
    }

    with httpx.stream(
        "POST",
        BASE_URL,
        headers={
            "x-api-key": settings.anthropic_api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        },
        json=payload,
        timeout=60,
    ) as response:
        if response.status_code >= 400:
            response.read()
            raise AnthropicError(response.status_code, response.text)

        buffer = b""
        for raw_bytes in response.iter_bytes():
            buffer += raw_bytes
            while b"\n" in buffer:
                line_bytes, buffer = buffer.split(b"\n", 1)
                line = line_bytes.decode("utf-8").rstrip("\r")
                if not line or not line.startswith("data: "):
                    continue
                event = json.loads(line[len("data: ") :])
                if event.get("type") == "content_block_delta":
                    delta = event.get("delta", {})
                    if delta.get("type") == "text_delta":
                        text = delta.get("text")
                        if text:
                            yield text
                elif event.get("type") == "message_stop":
                    return
