from __future__ import annotations

import hashlib
import math
import re
from collections.abc import Iterable
from typing import Protocol


class Embedder(Protocol):
    def embed(self, text: str) -> list[float]:
        ...


class DeterministicHashEmbedder:
    """Dependency-free deterministic embedding suitable for CI and smoke tests."""

    def __init__(self, dimensions: int = 128) -> None:
        if dimensions <= 0:
            raise ValueError("dimensions must be positive")
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = _tokens(text)
        if not tokens:
            return vector

        for token in tokens:
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            bucket = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[bucket] += sign

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]


class SentenceTransformersEmbedder:
    """Optional sentence-transformers adapter. Defaults to BGE-M3."""

    def __init__(self, model_name: str = "BAAI/bge-m3") -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers is not installed. Install the optional embeddings "
                "dependency or use --embedder hash."
            ) from exc

        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def embed(self, text: str) -> list[float]:
        embedding = self.model.encode(text, normalize_embeddings=True)
        return [float(value) for value in embedding]


def embed_many(embedder: Embedder, texts: Iterable[str]) -> list[list[float]]:
    return [embedder.embed(text) for text in texts]


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())
