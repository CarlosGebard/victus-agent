from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from infrastructure.safety_classifier import (
    LogisticSafetyClassifier,
    classify_safety_query,
    load_training_dataset,
    train_classifier,
)
from infrastructure.safety_similarity import BGE_M3_DIMENSIONS, get_chroma_collection


class StaticEmbedder:
    def __init__(self, vector: list[float]) -> None:
        self.vector = vector

    def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        assert len(texts) == 1
        return [self.vector]


def _unit_vector(index: int, sign: float = 1.0) -> list[float]:
    vector = [0.0] * BGE_M3_DIMENSIONS
    vector[index] = sign
    return vector


def test_training_loader_filters_non_binary_image_and_topic_rows(tmp_path: Path) -> None:
    collection = get_chroma_collection(tmp_path)
    collection.upsert(
        ids=["safe", "unsafe", "image", "topic", "unknown"],
        documents=["safe", "unsafe", "image", "topic", "unknown"],
        embeddings=[_unit_vector(index) for index in range(5)],
        metadatas=[
            {"task_type": "safety", "input_label": "safe", "has_image": False, "language": "en"},
            {"task_type": "safety", "input_label": "unsafe", "has_image": False, "language": "es"},
            {"task_type": "safety", "input_label": "unsafe", "has_image": True, "language": "en"},
            {"task_type": "topic_following", "input_label": "on-topic", "has_image": False},
            {"task_type": "safety", "input_label": "unknown", "has_image": False},
        ],
    )

    dataset = load_training_dataset(collection)

    assert dataset.usable_rows == 2
    assert dataset.labels.tolist() == [0, 1]
    assert dataset.languages == ("en", "es")
    assert dataset.skipped_reasons == {
        "image_dependent": 1,
        "non_binary_label": 1,
        "non_safety_task": 1,
    }


def test_train_export_load_and_query_classifier(tmp_path: Path) -> None:
    collection = get_chroma_collection(tmp_path / "chroma")
    ids: list[str] = []
    documents: list[str] = []
    embeddings: list[list[float]] = []
    metadatas: list[dict[str, str | bool]] = []
    rng = np.random.default_rng(7)
    for index in range(160):
        unsafe = index % 2 == 1
        vector = rng.normal(0.0, 0.02, BGE_M3_DIMENSIONS).astype(np.float32)
        vector[0] += 1.0 if unsafe else -1.0
        vector /= np.linalg.norm(vector)
        ids.append(f"row-{index}")
        documents.append(f"prompt-{index}")
        embeddings.append(vector.tolist())
        metadatas.append(
            {
                "task_type": "safety",
                "input_label": "unsafe" if unsafe else "safe",
                "has_image": False,
                "language": "en" if index % 4 else "es",
            }
        )
    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    artifact_dir = tmp_path / "artifact"

    manifest = train_classifier(
        collection,
        artifact_dir=artifact_dir,
        c_values=(0.1, 1.0),
        target_unsafe_recall=0.95,
    )
    loaded = LogisticSafetyClassifier.load(artifact_dir)
    unsafe_result = classify_safety_query(
        "unsafe query",
        artifact_dir=artifact_dir,
        embedder=StaticEmbedder(_unit_vector(0, 1.0)),
    )
    safe_result = loaded.predict_vector(_unit_vector(0, -1.0))

    assert manifest["dataset"]["usable_rows"] == 160
    assert manifest["validation_metrics"]["unsafe_recall"] >= 0.95
    assert manifest["test_metrics"]["balanced_accuracy"] >= 0.85
    assert unsafe_result.label == "unsafe"
    assert unsafe_result.unsafe_probability > unsafe_result.threshold
    assert safe_result.label == "safe"
    assert safe_result.unsafe_probability < safe_result.threshold
    assert (artifact_dir / "model.npz").exists()
    assert (artifact_dir / "manifest.json").exists()


def test_classifier_rejects_wrong_embedding_dimension() -> None:
    classifier = LogisticSafetyClassifier(
        weights=np.zeros(BGE_M3_DIMENSIONS, dtype=np.float32),
        intercept=0.0,
        threshold=0.5,
    )

    with pytest.raises(ValueError, match="query embedding must have shape"):
        classifier.predict_vector([1.0, 0.0])
