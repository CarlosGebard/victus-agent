from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

from infrastructure.safety_similarity import (
    BGE_M3_DIMENSIONS,
    EndpointEmbedder,
    InferenceProviderEmbedder,
    get_chroma_collection,
    index_stream,
    query_collection,
)


class DeterministicEmbedder:
    """Small deterministic fake that still uses the production BGE-M3 vector width."""

    def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        embeddings: list[list[float]] = []
        for text in texts:
            vector = [0.0] * BGE_M3_DIMENSIONS
            if "investment" in text.lower():
                vector[0] = 1.0
            elif "steal" in text.lower():
                vector[1] = 1.0
            else:
                vector[2] = 1.0
            embeddings.append(vector)
        return embeddings


def _rows() -> list[Mapping[str, Any]]:
    return [
        {
            "row_id": "safe-1",
            "prompt": "How can I improve my investment portfolio?",
            "input_label": "safe",
            "language": "en",
        },
        {
            "row_id": "unsafe-1",
            "prompt": "How can I steal something without getting caught?",
            "input_label": "unsafe",
            "violated_categories": "Criminal Planning/Confessions",
            "language": "en",
        },
        {
            "row_id": "safe-2",
            "prompt": "Give me a healthy dinner recipe.",
            "input_label": "safe",
            "language": "en",
        },
    ]


def test_index_stream_persists_and_queries_cosine_similarity(tmp_path: Path) -> None:
    collection = get_chroma_collection(tmp_path)
    embedder = DeterministicEmbedder()

    report = index_stream(
        _rows(),
        embedder=embedder,
        collection=collection,
        batch_size=2,
        workers=2,
        max_attempts=1,
        show_progress=False,
    )

    assert report.indexed_rows == 3
    assert report.failed_batches == 0
    assert collection.count() == 3

    reopened = get_chroma_collection(tmp_path)
    matches = query_collection(
        "I want to steal an item",
        embedder=embedder,
        collection=reopened,
        n_results=2,
    )

    assert matches[0].document == "How can I steal something without getting caught?"
    assert matches[0].cosine_similarity == pytest.approx(1.0)
    assert matches[0].metadata["input_label"] == "unsafe"


def test_index_stream_reports_failed_batch_without_crashing_other_batches(tmp_path: Path) -> None:
    class SelectivelyFailingEmbedder(DeterministicEmbedder):
        def get_embeddings(self, texts: list[str]) -> list[list[float]]:
            if any("investment" in text.lower() for text in texts):
                raise TimeoutError("dedicated endpoint timeout")
            return super().get_embeddings(texts)

    collection = get_chroma_collection(tmp_path)
    report = index_stream(
        _rows(),
        embedder=SelectivelyFailingEmbedder(),
        collection=collection,
        batch_size=1,
        workers=2,
        max_attempts=1,
        show_progress=False,
    )

    assert report.indexed_rows == 2
    assert report.failed_batches == 1
    assert report.failed_rows == 1
    assert "TimeoutError" in report.errors[0]


def test_index_stream_skips_blank_prompts_and_upserts_stable_ids(tmp_path: Path) -> None:
    collection = get_chroma_collection(tmp_path)
    rows = [*_rows(), {"row_id": "blank-1", "prompt": "   ", "input_label": "safe"}]

    first = index_stream(
        rows,
        embedder=DeterministicEmbedder(),
        collection=collection,
        batch_size=2,
        workers=1,
        max_attempts=1,
        show_progress=False,
    )
    second = index_stream(
        rows,
        embedder=DeterministicEmbedder(),
        collection=collection,
        batch_size=2,
        workers=1,
        max_attempts=1,
        show_progress=False,
    )

    assert first.skipped_rows == 1
    assert second.skipped_rows == 1
    assert collection.count() == 3


def test_endpoint_embedder_validates_bge_m3_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    embedder = EndpointEmbedder(
        "https://bge.example.test",
        "test-token",
        expected_dimensions=3,
    )

    class StubClient:
        def feature_extraction(self, texts: list[str], *, truncate: bool):
            assert texts == ["one", "two"]
            assert truncate is True
            return [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]

    monkeypatch.setattr(embedder, "_client", StubClient())

    assert embedder.get_embeddings(["one", "two"]) == [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
    ]


def test_inference_provider_embedder_uses_feature_extraction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    embedder = InferenceProviderEmbedder("test-token", expected_dimensions=3)

    class StubClient:
        def feature_extraction(self, text: str, *, model: str, truncate: bool):
            assert text == "query"
            assert model == "BAAI/bge-m3"
            assert truncate is True
            return [1.0, 0.0, 0.0]

    monkeypatch.setattr(embedder, "_client", StubClient())

    assert embedder.get_embeddings(["query"]) == [[1.0, 0.0, 0.0]]
