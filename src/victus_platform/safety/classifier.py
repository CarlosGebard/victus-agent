from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any, Protocol, cast

import numpy as np

from victus_platform.safety.similarity import (
    BGE_M3_DIMENSIONS,
    DEFAULT_CHROMA_PATH,
    DEFAULT_COLLECTION_NAME,
    Embedder,
    _chroma_path_from_env,
    get_chroma_collection,
    inference_provider_embedder_from_env,
)


DEFAULT_ARTIFACT_DIR = Path("data/runtime/safety_classifier")
MODEL_FILENAME = "model.npz"
MANIFEST_FILENAME = "manifest.json"
ARTIFACT_SCHEMA_VERSION = 1
POSITIVE_LABEL = "unsafe"
NEGATIVE_LABEL = "safe"
DEFAULT_TARGET_UNSAFE_RECALL = 0.95
DEFAULT_RANDOM_SEED = 42
DEFAULT_C_VALUES = (0.01, 0.1, 1.0, 10.0)


class TrainingCollection(Protocol):
    """Minimal Chroma read surface needed to construct a training matrix."""

    def count(self) -> int:
        """Return the number of records in the collection."""

    def get(
        self,
        *,
        limit: int,
        offset: int,
        include: list[str],
    ) -> Mapping[str, Any]:
        """Read one bounded page containing embeddings and metadata."""


@dataclass(frozen=True)
class TrainingDataset:
    """Filtered, normalized examples and their audit dimensions."""

    features: np.ndarray
    labels: np.ndarray
    languages: tuple[str, ...]
    record_ids: tuple[str, ...]
    scanned_rows: int
    skipped_reasons: Mapping[str, int]

    @property
    def usable_rows(self) -> int:
        """Return the number of examples accepted for binary training."""

        return int(self.features.shape[0])


@dataclass(frozen=True)
class DatasetPartition:
    """One deterministic train, validation, or test partition."""

    features: np.ndarray
    labels: np.ndarray
    languages: tuple[str, ...]
    record_ids: tuple[str, ...]


@dataclass(frozen=True)
class SafetyClassification:
    """Runtime logistic-regression result for one prompt embedding."""

    label: str
    unsafe_probability: float
    threshold: float


@dataclass(frozen=True)
class LogisticSafetyClassifier:
    """Portable NumPy-only binary classifier over normalized BGE-M3 vectors."""

    weights: np.ndarray
    intercept: float
    threshold: float
    dimensions: int = BGE_M3_DIMENSIONS

    def __post_init__(self) -> None:
        weights = np.asarray(self.weights, dtype=np.float32)
        if weights.shape != (self.dimensions,):
            raise ValueError(
                f"classifier weights must have shape ({self.dimensions},), got {weights.shape}"
            )
        if not np.isfinite(weights).all() or not math.isfinite(self.intercept):
            raise ValueError("classifier weights and intercept must be finite")
        if not 0.0 <= self.threshold <= 1.0:
            raise ValueError("classifier threshold must be between 0 and 1")
        object.__setattr__(self, "weights", weights)

    def predict_vector(self, embedding: Sequence[float]) -> SafetyClassification:
        """Normalize one embedding and classify it using the persisted policy threshold."""

        vector = np.asarray(embedding, dtype=np.float32)
        if vector.shape != (self.dimensions,):
            raise ValueError(
                f"query embedding must have shape ({self.dimensions},), got {vector.shape}"
            )
        if not np.isfinite(vector).all():
            raise ValueError("query embedding contains NaN or infinite values")
        norm = float(np.linalg.norm(vector))
        if norm <= 0.0:
            raise ValueError("query embedding must have a positive norm")
        vector /= norm
        logit = float(vector @ self.weights + self.intercept)
        probability = _sigmoid(logit)
        label = POSITIVE_LABEL if probability >= self.threshold else NEGATIVE_LABEL
        return SafetyClassification(
            label=label,
            unsafe_probability=probability,
            threshold=self.threshold,
        )

    def classify_text(self, query_text: str, embedder: Embedder) -> SafetyClassification:
        """Embed and classify one non-empty query using the supplied BGE-M3 adapter."""

        if not query_text.strip():
            raise ValueError("query_text must be non-empty")
        embeddings = embedder.get_embeddings([query_text])
        if len(embeddings) != 1:
            raise RuntimeError(f"embedder returned {len(embeddings)} vectors for one query")
        return self.predict_vector(embeddings[0])

    @classmethod
    def load(cls, artifact_dir: str | Path = DEFAULT_ARTIFACT_DIR) -> LogisticSafetyClassifier:
        """Load and validate a NumPy/JSON artifact without enabling pickle deserialization."""

        directory = Path(artifact_dir)
        manifest_path = directory / MANIFEST_FILENAME
        model_path = directory / MODEL_FILENAME
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise RuntimeError(f"classifier artifact is missing: {manifest_path}") from exc
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"classifier manifest is invalid JSON: {manifest_path}") from exc
        if manifest.get("schema_version") != ARTIFACT_SCHEMA_VERSION:
            raise RuntimeError(
                f"unsupported classifier schema version: {manifest.get('schema_version')!r}"
            )
        expected_hash = manifest.get("model_sha256")
        if not isinstance(expected_hash, str) or _sha256(model_path) != expected_hash:
            raise RuntimeError("classifier model checksum does not match its manifest")

        with np.load(model_path, allow_pickle=False) as data:
            weights = np.asarray(data["weights"], dtype=np.float32)
            intercept = float(np.asarray(data["intercept"]).item())
            threshold = float(np.asarray(data["threshold"]).item())
            dimensions = int(np.asarray(data["dimensions"]).item())
        return cls(
            weights=weights,
            intercept=intercept,
            threshold=threshold,
            dimensions=dimensions,
        )


def load_training_dataset(
    collection: TrainingCollection,
    *,
    chunk_size: int = 1_000,
    expected_dimensions: int = BGE_M3_DIMENSIONS,
) -> TrainingDataset:
    """Read Chroma in bounded pages and keep only text-only binary safety examples."""

    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    features: list[np.ndarray] = []
    labels: list[int] = []
    languages: list[str] = []
    record_ids: list[str] = []
    skipped: Counter[str] = Counter()
    total = collection.count()
    scanned = 0

    for offset in range(0, total, chunk_size):
        result = collection.get(
            limit=min(chunk_size, total - offset),
            offset=offset,
            include=["embeddings", "metadatas"],
        )
        raw_embeddings = result.get("embeddings")
        raw_metadatas = result.get("metadatas")
        raw_ids = result.get("ids")
        if raw_embeddings is None or raw_metadatas is None or raw_ids is None:
            raise RuntimeError("Chroma page omitted embeddings, metadatas, or ids")
        embeddings = np.asarray(raw_embeddings, dtype=np.float32)
        if embeddings.ndim != 2 or embeddings.shape[1] != expected_dimensions:
            raise RuntimeError(
                f"Chroma embeddings must have shape (n, {expected_dimensions}); "
                f"received {embeddings.shape}"
            )
        if len(raw_metadatas) != embeddings.shape[0] or len(raw_ids) != embeddings.shape[0]:
            raise RuntimeError("Chroma page returned inconsistent row counts")

        for embedding, metadata, record_id in zip(
            embeddings, raw_metadatas, raw_ids, strict=True
        ):
            scanned += 1
            if not isinstance(metadata, Mapping):
                skipped["missing_metadata"] += 1
                continue
            if metadata.get("task_type") != "safety":
                skipped["non_safety_task"] += 1
                continue
            label = metadata.get("input_label")
            if label not in {NEGATIVE_LABEL, POSITIVE_LABEL}:
                skipped["non_binary_label"] += 1
                continue
            if bool(metadata.get("has_image")):
                skipped["image_dependent"] += 1
                continue
            if not np.isfinite(embedding).all():
                raise RuntimeError(f"embedding {record_id!r} contains non-finite values")
            norm = float(np.linalg.norm(embedding))
            if norm <= 0.0:
                raise RuntimeError(f"embedding {record_id!r} has zero norm")
            features.append(embedding / norm)
            labels.append(1 if label == POSITIVE_LABEL else 0)
            languages.append(str(metadata.get("language") or "unknown"))
            record_ids.append(str(record_id))

    if not features:
        raise RuntimeError("no usable text-only binary safety examples were found")
    matrix = np.asarray(features, dtype=np.float32)
    targets = np.asarray(labels, dtype=np.int8)
    if len(np.unique(targets)) != 2:
        raise RuntimeError("training data must contain both safe and unsafe labels")
    return TrainingDataset(
        features=matrix,
        labels=targets,
        languages=tuple(languages),
        record_ids=tuple(record_ids),
        scanned_rows=scanned,
        skipped_reasons=dict(sorted(skipped.items())),
    )


def split_training_dataset(
    dataset: TrainingDataset,
    *,
    random_seed: int = DEFAULT_RANDOM_SEED,
) -> tuple[DatasetPartition, DatasetPartition, DatasetPartition]:
    """Create deterministic 70/15/15 stratified train, validation, and test partitions."""

    train_test_split, _ = _training_dependencies()
    indices = np.arange(dataset.usable_rows)
    train_indices, remainder_indices = train_test_split(
        indices,
        test_size=0.30,
        random_state=random_seed,
        stratify=dataset.labels,
    )
    validation_indices, test_indices = train_test_split(
        remainder_indices,
        test_size=0.50,
        random_state=random_seed,
        stratify=dataset.labels[remainder_indices],
    )
    return tuple(
        _partition(dataset, selected)
        for selected in (train_indices, validation_indices, test_indices)
    )  # type: ignore[return-value]


def train_classifier(
    collection: TrainingCollection,
    *,
    artifact_dir: str | Path = DEFAULT_ARTIFACT_DIR,
    target_unsafe_recall: float = DEFAULT_TARGET_UNSAFE_RECALL,
    c_values: Sequence[float] = DEFAULT_C_VALUES,
    random_seed: int = DEFAULT_RANDOM_SEED,
) -> Mapping[str, Any]:
    """Train candidate logistic models, evaluate the winner, and persist a portable artifact."""

    if not 0.0 < target_unsafe_recall <= 1.0:
        raise ValueError("target_unsafe_recall must be in (0, 1]")
    if not c_values or any(value <= 0 for value in c_values):
        raise ValueError("c_values must contain positive regularization values")
    _, LogisticRegression = _training_dependencies()
    dataset = load_training_dataset(collection)
    train, validation, test = split_training_dataset(dataset, random_seed=random_seed)

    best: tuple[tuple[float, float, float], Any, float, Mapping[str, Any], float] | None = None
    candidates: list[Mapping[str, Any]] = []
    for c_value in c_values:
        model = LogisticRegression(
            C=float(c_value),
            class_weight="balanced",
            max_iter=2_000,
            random_state=random_seed,
            solver="lbfgs",
        )
        model.fit(train.features, train.labels)
        probabilities = model.predict_proba(validation.features)[:, 1]
        threshold = select_unsafe_threshold(
            validation.labels,
            probabilities,
            target_recall=target_unsafe_recall,
        )
        metrics = evaluate_predictions(validation.labels, probabilities, threshold)
        candidate = {
            "c": float(c_value),
            "threshold": threshold,
            "validation": metrics,
        }
        candidates.append(candidate)
        score = (
            float(metrics["balanced_accuracy"]),
            float(metrics["safe_recall"]),
            -float(c_value),
        )
        if best is None or score > best[0]:
            best = (score, model, threshold, metrics, float(c_value))

    assert best is not None
    _, model, threshold, validation_metrics, selected_c = best
    test_probabilities = model.predict_proba(test.features)[:, 1]
    test_metrics = evaluate_predictions(test.labels, test_probabilities, threshold)
    language_metrics = evaluate_by_language(
        test.labels,
        test_probabilities,
        test.languages,
        threshold,
    )
    weights = np.asarray(model.coef_[0], dtype=np.float32)
    intercept = float(model.intercept_[0])
    manifest: dict[str, Any] = {
        "schema_version": ARTIFACT_SCHEMA_VERSION,
        "created_at": datetime.now(UTC).isoformat(),
        "model_type": "binary_logistic_regression",
        "embedding_model": "BAAI/bge-m3",
        "embedding_dimensions": int(weights.shape[0]),
        "embedding_normalization": "l2",
        "positive_label": POSITIVE_LABEL,
        "negative_label": NEGATIVE_LABEL,
        "threshold": threshold,
        "target_unsafe_recall": target_unsafe_recall,
        "selected_c": selected_c,
        "class_weight": "balanced",
        "random_seed": random_seed,
        "source_collection": DEFAULT_COLLECTION_NAME,
        "filters": {
            "task_type": "safety",
            "input_label": [NEGATIVE_LABEL, POSITIVE_LABEL],
            "has_image": False,
        },
        "dataset": {
            "scanned_rows": dataset.scanned_rows,
            "usable_rows": dataset.usable_rows,
            "safe_rows": int(np.sum(dataset.labels == 0)),
            "unsafe_rows": int(np.sum(dataset.labels == 1)),
            "skipped_reasons": dataset.skipped_reasons,
            "train_rows": len(train.labels),
            "validation_rows": len(validation.labels),
            "test_rows": len(test.labels),
        },
        "candidate_models": candidates,
        "validation_metrics": validation_metrics,
        "test_metrics": test_metrics,
        "test_metrics_by_language": language_metrics,
        "limitations": [
            "Evaluation uses held-out rows from a 10,000-row train subset.",
            "Official validation and test splits are required before production use.",
            "The classifier excludes examples whose label depends on an image.",
        ],
    }
    save_classifier_artifact(
        LogisticSafetyClassifier(
            weights=weights,
            intercept=intercept,
            threshold=threshold,
            dimensions=int(weights.shape[0]),
        ),
        manifest,
        artifact_dir,
    )
    return manifest


def select_unsafe_threshold(
    labels: np.ndarray,
    probabilities: np.ndarray,
    *,
    target_recall: float,
) -> float:
    """Choose the highest validation threshold that meets the unsafe-recall target."""

    targets = np.asarray(labels, dtype=np.int8)
    scores = np.asarray(probabilities, dtype=np.float64)
    if targets.shape != scores.shape or targets.ndim != 1:
        raise ValueError("labels and probabilities must be one-dimensional with matching shapes")
    unsafe_scores = scores[targets == 1]
    if unsafe_scores.size == 0:
        raise ValueError("threshold selection requires unsafe validation examples")
    valid: list[float] = []
    for threshold in np.unique(np.concatenate(([0.0], scores, [1.0]))):
        recall = float(np.mean(unsafe_scores >= threshold))
        if recall >= target_recall:
            valid.append(float(threshold))
    return max(valid) if valid else 0.0


def evaluate_predictions(
    labels: np.ndarray,
    probabilities: np.ndarray,
    threshold: float,
) -> Mapping[str, Any]:
    """Compute safety-oriented binary metrics for a fixed decision threshold."""

    _, _, metrics = _training_dependencies(include_metrics=True)
    targets = np.asarray(labels, dtype=np.int8)
    scores = np.asarray(probabilities, dtype=np.float64)
    predictions = (scores >= threshold).astype(np.int8)
    tn, fp, fn, tp = metrics.confusion_matrix(targets, predictions, labels=[0, 1]).ravel()
    result: dict[str, Any] = {
        "rows": int(len(targets)),
        "threshold": float(threshold),
        "accuracy": float(metrics.accuracy_score(targets, predictions)),
        "balanced_accuracy": float(metrics.balanced_accuracy_score(targets, predictions)),
        "unsafe_precision": float(metrics.precision_score(targets, predictions, zero_division=0)),
        "unsafe_recall": float(metrics.recall_score(targets, predictions, zero_division=0)),
        "unsafe_f1": float(metrics.f1_score(targets, predictions, zero_division=0)),
        "safe_recall": float(tn / (tn + fp)) if tn + fp else 0.0,
        "brier_score": float(metrics.brier_score_loss(targets, scores)),
        "confusion": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
    }
    if len(np.unique(targets)) == 2:
        result["roc_auc"] = float(metrics.roc_auc_score(targets, scores))
        result["average_precision"] = float(metrics.average_precision_score(targets, scores))
    return result


def evaluate_by_language(
    labels: np.ndarray,
    probabilities: np.ndarray,
    languages: Sequence[str],
    threshold: float,
) -> Mapping[str, Any]:
    """Report test metrics per language when at least five rows are available."""

    language_array = np.asarray(languages, dtype=str)
    output: dict[str, Any] = {}
    for language in sorted(set(languages)):
        mask = language_array == language
        if int(np.sum(mask)) < 5:
            continue
        output[language] = evaluate_predictions(labels[mask], probabilities[mask], threshold)
    return output


def save_classifier_artifact(
    classifier: LogisticSafetyClassifier,
    manifest: Mapping[str, Any],
    artifact_dir: str | Path = DEFAULT_ARTIFACT_DIR,
) -> None:
    """Atomically persist model arrays and a checksum-bound JSON manifest."""

    directory = Path(artifact_dir)
    directory.mkdir(parents=True, exist_ok=True)
    model_path = directory / MODEL_FILENAME
    model_temp = directory / f".{MODEL_FILENAME}.tmp.npz"
    np.savez_compressed(
        model_temp,
        weights=classifier.weights,
        intercept=np.asarray(classifier.intercept, dtype=np.float64),
        threshold=np.asarray(classifier.threshold, dtype=np.float64),
        dimensions=np.asarray(classifier.dimensions, dtype=np.int32),
    )
    os.replace(model_temp, model_path)
    serialized_manifest = dict(manifest)
    serialized_manifest["schema_version"] = ARTIFACT_SCHEMA_VERSION
    serialized_manifest["model_file"] = MODEL_FILENAME
    serialized_manifest["model_sha256"] = _sha256(model_path)
    manifest_path = directory / MANIFEST_FILENAME
    manifest_temp = directory / f".{MANIFEST_FILENAME}.tmp"
    manifest_temp.write_text(
        json.dumps(serialized_manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(manifest_temp, manifest_path)


def classify_safety_query(
    query_text: str,
    *,
    artifact_dir: str | Path = DEFAULT_ARTIFACT_DIR,
    embedder: Embedder | None = None,
) -> SafetyClassification:
    """Load the portable classifier, embed one query, and return its binary result."""

    classifier = LogisticSafetyClassifier.load(artifact_dir)
    resolved_embedder = embedder if embedder is not None else inference_provider_embedder_from_env()
    return classifier.classify_text(query_text, resolved_embedder)


def _partition(dataset: TrainingDataset, indices: np.ndarray) -> DatasetPartition:
    selected = np.asarray(indices, dtype=np.int64)
    return DatasetPartition(
        features=dataset.features[selected],
        labels=dataset.labels[selected],
        languages=tuple(dataset.languages[index] for index in selected),
        record_ids=tuple(dataset.record_ids[index] for index in selected),
    )


def _training_dependencies(*, include_metrics: bool = False) -> tuple[Any, ...]:
    try:
        from sklearn import metrics
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import train_test_split
    except ImportError as exc:  # pragma: no cover - exercised without the optional extra
        raise RuntimeError(
            "Classifier training requires: uv sync --extra safety-index --extra safety-training"
        ) from exc
    if include_metrics:
        return train_test_split, LogisticRegression, metrics
    return train_test_split, LogisticRegression


def _sigmoid(value: float) -> float:
    if value >= 0.0:
        return 1.0 / (1.0 + math.exp(-value))
    exp_value = math.exp(value)
    return exp_value / (1.0 + exp_value)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(chunk)
    except FileNotFoundError as exc:
        raise RuntimeError(f"classifier model is missing: {path}") from exc
    return digest.hexdigest()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train or query the BGE-M3 safety classifier.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    train_parser = subparsers.add_parser("train", help="Train from the local Chroma collection.")
    train_parser.add_argument("--chroma-path", type=Path, default=_chroma_path_from_env())
    train_parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    train_parser.add_argument(
        "--target-unsafe-recall",
        type=float,
        default=DEFAULT_TARGET_UNSAFE_RECALL,
    )
    query_parser = subparsers.add_parser("query", help="Classify one query through BGE-M3.")
    query_parser.add_argument("query_text")
    query_parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    return parser


def main() -> int:
    """Run the local training command or one endpoint-backed query."""

    args = _build_parser().parse_args()
    try:
        if args.command == "train":
            collection = cast(TrainingCollection, get_chroma_collection(args.chroma_path))
            started = perf_counter()
            manifest = train_classifier(
                collection,
                artifact_dir=args.artifact_dir,
                target_unsafe_recall=args.target_unsafe_recall,
            )
            summary = {
                "artifact_dir": str(args.artifact_dir),
                "elapsed_seconds": round(perf_counter() - started, 3),
                "selected_c": manifest["selected_c"],
                "threshold": manifest["threshold"],
                "dataset": manifest["dataset"],
                "validation_metrics": manifest["validation_metrics"],
                "test_metrics": manifest["test_metrics"],
            }
            print(json.dumps(summary, ensure_ascii=False, indent=2))
            return 0
        started = perf_counter()
        result = classify_safety_query(args.query_text, artifact_dir=args.artifact_dir)
        print(
            json.dumps(
                {
                    "label": result.label,
                    "unsafe_probability": result.unsafe_probability,
                    "threshold": result.threshold,
                    "elapsed_seconds": round(perf_counter() - started, 3),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    except (RuntimeError, ValueError) as exc:
        print(f"Safety classifier failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
