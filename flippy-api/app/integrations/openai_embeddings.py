"""Thin wrapper over OpenAI's embeddings endpoint."""
import httpx

from app.core.config import settings

MODEL = "text-embedding-3-small"
DIMENSIONS = 1536


class OpenAIEmbeddingsError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(message)


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    response = httpx.post(
        "https://api.openai.com/v1/embeddings",
        headers={
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        },
        json={"model": MODEL, "input": texts},
        timeout=30,
    )
    if response.status_code >= 400:
        raise OpenAIEmbeddingsError(response.status_code, response.text)

    data = response.json()["data"]
    return [item["embedding"] for item in data]


def embed_text(text: str) -> list[float]:
    return embed_texts([text])[0]
