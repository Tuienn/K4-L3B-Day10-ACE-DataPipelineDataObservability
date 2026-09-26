from __future__ import annotations

from functools import lru_cache

from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer


@lru_cache(maxsize=4)
def _load_model(model_name: str) -> SentenceTransformer:
    return SentenceTransformer(model_name)


@lru_cache(maxsize=32)
def _encode(model_name: str, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]:
    # Immutable cache: baseline/repaired batches and repeated queries reuse vectors.
    vectors = _load_model(model_name).encode(list(texts), normalize_embeddings=True)
    return tuple(tuple(row) for row in vectors.tolist())


class MiniLMEmbeddings(Embeddings):
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = _load_model(model_name)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return [list(row) for row in _encode(self.model_name, tuple(texts))]

    def embed_query(self, text: str) -> list[float]:
        return list(_encode(self.model_name, (text,))[0])
