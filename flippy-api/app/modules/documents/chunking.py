"""Chunking: 500 tokens per chunk, 50 token overlap, cut on paragraph boundaries
when possible (SPEC.md §5 Pipeline RAG)."""
import tiktoken

CHUNK_SIZE_TOKENS = 500
OVERLAP_TOKENS = 50

_encoding = tiktoken.get_encoding("cl100k_base")


def chunk_text(text: str) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        return []

    chunks: list[str] = []
    current_tokens: list[int] = []

    for paragraph in paragraphs:
        paragraph_tokens = _encoding.encode(paragraph)

        if len(current_tokens) + len(paragraph_tokens) <= CHUNK_SIZE_TOKENS:
            current_tokens.extend(paragraph_tokens)
            continue

        if current_tokens:
            chunks.append(_encoding.decode(current_tokens))
            current_tokens = current_tokens[-OVERLAP_TOKENS:]

        if len(paragraph_tokens) > CHUNK_SIZE_TOKENS:
            for i in range(0, len(paragraph_tokens), CHUNK_SIZE_TOKENS - OVERLAP_TOKENS):
                piece = paragraph_tokens[i : i + CHUNK_SIZE_TOKENS]
                chunks.append(_encoding.decode(piece))
            current_tokens = []
        else:
            current_tokens.extend(paragraph_tokens)

    if current_tokens:
        chunks.append(_encoding.decode(current_tokens))

    return chunks
