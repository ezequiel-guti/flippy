from app.modules.documents import services
from app.modules.documents.chunking import Chunk


def test_embed_in_batches_splits_by_token_limit(monkeypatch):
    calls: list[list[str]] = []

    def fake_embed_texts(texts):
        calls.append(list(texts))
        return [[0.0] for _ in texts]

    monkeypatch.setattr(services, "embed_texts", fake_embed_texts)

    # Two chunks that together exceed the batch token limit must go in separate calls.
    big = services.EMBEDDING_BATCH_TOKEN_LIMIT - 100
    chunks = [
        Chunk(content="a", chunk_index=0, token_count=big),
        Chunk(content="b", chunk_index=1, token_count=big),
    ]

    embeddings = services._embed_in_batches(chunks)

    assert len(embeddings) == 2
    assert len(calls) == 2
    assert calls[0] == ["a"]
    assert calls[1] == ["b"]


def test_embed_in_batches_groups_small_chunks_in_one_call(monkeypatch):
    calls: list[list[str]] = []

    def fake_embed_texts(texts):
        calls.append(list(texts))
        return [[0.0] for _ in texts]

    monkeypatch.setattr(services, "embed_texts", fake_embed_texts)

    chunks = [Chunk(content=f"chunk-{i}", chunk_index=i, token_count=10) for i in range(5)]

    embeddings = services._embed_in_batches(chunks)

    assert len(embeddings) == 5
    assert len(calls) == 1
    assert calls[0] == [f"chunk-{i}" for i in range(5)]


def test_embed_in_batches_respects_max_items_per_batch(monkeypatch):
    calls: list[list[str]] = []

    def fake_embed_texts(texts):
        calls.append(list(texts))
        return [[0.0] for _ in texts]

    monkeypatch.setattr(services, "embed_texts", fake_embed_texts)

    count = services.EMBEDDING_BATCH_MAX_ITEMS + 1
    chunks = [Chunk(content=str(i), chunk_index=i, token_count=1) for i in range(count)]

    embeddings = services._embed_in_batches(chunks)

    assert len(embeddings) == count
    assert len(calls) == 2
    assert len(calls[0]) == services.EMBEDDING_BATCH_MAX_ITEMS
    assert len(calls[1]) == 1
