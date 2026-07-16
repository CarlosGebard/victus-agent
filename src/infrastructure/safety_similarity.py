from __future__ import annotations

import math
import os
import sys
import threading
import time
from collections.abc import Iterable, Iterator, Mapping, Sequence
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import dataclass
from itertools import chain, islice
from pathlib import Path
from time import perf_counter
from typing import Any, Protocol, TypeAlias, cast

import numpy as np


DATASET_NAME = "nvidia/Nemotron-3.5-Content-Safety-Dataset"
BGE_M3_MODEL_ID = "BAAI/bge-m3"
DEFAULT_SPLIT = "train"
DEFAULT_COLLECTION_NAME = "nemotron_safety_bge"
DEFAULT_CHROMA_PATH = Path("./chroma_db")
DEFAULT_BATCH_SIZE = 32
DEFAULT_WORKERS = 4
DEFAULT_LIMIT = 10_000
BGE_M3_DIMENSIONS = 1024
DEFAULT_MAX_ATTEMPTS = 3

MetadataValue: TypeAlias = str | int | float | bool
Metadata: TypeAlias = dict[str, MetadataValue]


class Embedder(Protocol):
    """Port implemented by providers that return one dense vector per input text."""

    def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Embed a non-empty batch of texts while preserving input order."""


class ChromaCollection(Protocol):
    """Minimal Chroma collection surface used by the indexing pipeline."""

    def upsert(
        self,
        *,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[Metadata],
    ) -> Any:
        """Insert or replace a batch by stable identifiers."""

    def query(
        self,
        *,
        query_embeddings: list[list[float]],
        n_results: int,
        include: list[str],
    ) -> Mapping[str, Any]:
        """Return nearest documents and cosine distances."""

    def count(self) -> int:
        """Return the number of stored records."""


@dataclass(frozen=True)
class IndexRecord:
    """A normalized dataset row ready for embedding and persistence."""

    record_id: str
    document: str
    metadata: Metadata


@dataclass(frozen=True)
class BatchResult:
    """Outcome of one worker batch after retries are exhausted or it succeeds."""

    rows: int
    attempts: int
    error: str | None = None

    @property
    def succeeded(self) -> bool:
        """Whether the complete batch was persisted."""

        return self.error is None


@dataclass(frozen=True)
class IndexingReport:
    """Aggregate result of a bounded streaming indexing run."""

    submitted_batches: int
    indexed_rows: int
    failed_batches: int
    failed_rows: int
    skipped_rows: int
    errors: tuple[str, ...]


@dataclass(frozen=True)
class SimilarPrompt:
    """One semantic match returned from the local vector database."""

    document: str
    cosine_similarity: float
    metadata: Mapping[str, Any]


class EndpointEmbedder:
    """BGE-M3 adapter for a dedicated Hugging Face Inference Endpoint.

    The endpoint must expose Hugging Face's feature-extraction task and return one pooled,
    1024-dimensional float vector per input text. Authentication data remains in memory and is
    never written to Chroma metadata.
    """

    def __init__(
        self,
        endpoint_url: str,
        hf_token: str,
        *,
        timeout_seconds: float = 120.0,
        expected_dimensions: int = BGE_M3_DIMENSIONS,
    ) -> None:
        """Create an endpoint client and define the expected dense-vector shape."""

        if not endpoint_url.strip():
            raise ValueError("endpoint_url must be non-empty")
        if not hf_token.strip():
            raise ValueError("hf_token must be non-empty")
        if expected_dimensions <= 0:
            raise ValueError("expected_dimensions must be positive")

        try:
            from huggingface_hub import InferenceClient
        except ImportError as exc:  # pragma: no cover - exercised without the optional extra
            raise RuntimeError(
                "Endpoint embeddings require the safety-index dependencies. "
                "Run: uv sync --extra safety-index"
            ) from exc

        self.endpoint_url = endpoint_url.rstrip("/")
        self.expected_dimensions = expected_dimensions
        self._client = InferenceClient(
            model=self.endpoint_url,
            token=hf_token,
            timeout=timeout_seconds,
        )

    def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Return a validated BGE-M3 embedding for every text in the batch.

        Raises:
            ValueError: If the batch is empty or contains blank/non-string items.
            RuntimeError: If the endpoint returns an unexpected batch count or vector shape.
        """

        if not texts:
            raise ValueError("texts must contain at least one item")
        if any(not isinstance(text, str) or not text.strip() for text in texts):
            raise ValueError("texts must contain only non-empty strings")

        raw = self._client.feature_extraction(texts, truncate=True)
        embeddings = np.asarray(raw, dtype=np.float32)
        if embeddings.ndim == 1 and len(texts) == 1:
            embeddings = embeddings.reshape(1, -1)
        if embeddings.ndim != 2:
            raise RuntimeError(
                "BGE-M3 endpoint must return pooled 2D embeddings; "
                f"received shape {embeddings.shape}"
            )
        if embeddings.shape[0] != len(texts):
            raise RuntimeError(
                f"endpoint returned {embeddings.shape[0]} embeddings for {len(texts)} texts"
            )
        if embeddings.shape[1] != self.expected_dimensions:
            raise RuntimeError(
                f"endpoint returned {embeddings.shape[1]} dimensions; "
                f"expected {self.expected_dimensions} for BGE-M3"
            )
        if not np.isfinite(embeddings).all():
            raise RuntimeError("endpoint returned NaN or infinite embedding values")
        return embeddings.tolist()


class InferenceProviderEmbedder:
    """BGE-M3 query adapter using Hugging Face's serverless HF Inference provider."""

    def __init__(
        self,
        hf_token: str,
        *,
        model: str = BGE_M3_MODEL_ID,
        provider: str = "hf-inference",
        timeout_seconds: float = 60.0,
        expected_dimensions: int = BGE_M3_DIMENSIONS,
    ) -> None:
        """Create a provider client without depending on a dedicated endpoint URL."""

        if not hf_token.strip():
            raise ValueError("hf_token must be non-empty")
        if not model.strip() or not provider.strip():
            raise ValueError("model and provider must be non-empty")
        try:
            from huggingface_hub import InferenceClient
        except ImportError as exc:  # pragma: no cover - exercised without the optional extra
            raise RuntimeError(
                "Inference Provider embeddings require the safety-index dependencies. "
                "Run: uv sync --extra safety-index"
            ) from exc
        self.model = model
        self.provider = provider
        self.expected_dimensions = expected_dimensions
        self._client = InferenceClient(
            provider=provider,
            api_key=hf_token,
            timeout=timeout_seconds,
        )

    def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Return validated provider embeddings while preserving batch order."""

        if not texts:
            raise ValueError("texts must contain at least one item")
        if any(not isinstance(text, str) or not text.strip() for text in texts):
            raise ValueError("texts must contain only non-empty strings")
        provider_input: str | list[str] = texts[0] if len(texts) == 1 else texts
        raw = self._client.feature_extraction(
            provider_input,
            model=self.model,
            truncate=True,
        )
        embeddings = np.asarray(raw, dtype=np.float32)
        if embeddings.ndim == 1 and len(texts) == 1:
            embeddings = embeddings.reshape(1, -1)
        if embeddings.ndim != 2:
            raise RuntimeError(
                "Inference Provider must return pooled 2D embeddings; "
                f"received shape {embeddings.shape}"
            )
        if embeddings.shape != (len(texts), self.expected_dimensions):
            raise RuntimeError(
                f"provider returned shape {embeddings.shape}; expected "
                f"({len(texts)}, {self.expected_dimensions})"
            )
        if not np.isfinite(embeddings).all():
            raise RuntimeError("provider returned NaN or infinite embedding values")
        return embeddings.tolist()


def get_chroma_collection(
    db_path: str | Path = DEFAULT_CHROMA_PATH,
    collection_name: str = DEFAULT_COLLECTION_NAME,
) -> ChromaCollection:
    """Open a persistent local Chroma collection configured for cosine distance."""

    if not collection_name:
        raise ValueError("collection_name must be non-empty")
    try:
        import chromadb
    except ImportError as exc:  # pragma: no cover - exercised without the optional extra
        raise RuntimeError(
            "Chroma requires the safety-index dependencies. Run: uv sync --extra safety-index"
        ) from exc

    client = chromadb.PersistentClient(path=str(db_path))
    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=None,
        configuration={"hnsw": {"space": "cosine"}},
    )
    return cast(ChromaCollection, collection)


def load_dataset_stream(split: str = DEFAULT_SPLIT) -> Iterable[Mapping[str, Any]]:
    """Load one Nemotron split lazily with Hugging Face streaming enabled."""

    try:
        from datasets import load_dataset
    except ImportError as exc:  # pragma: no cover - exercised without the optional extra
        raise RuntimeError(
            "Dataset streaming requires the safety-index dependencies. "
            "Run: uv sync --extra safety-index"
        ) from exc
    return cast(
        Iterable[Mapping[str, Any]],
        load_dataset(DATASET_NAME, split=split, streaming=True),
    )


def preview_rows(
    rows: Iterator[Mapping[str, Any]],
    *,
    count: int = 2,
) -> tuple[list[Mapping[str, Any]], Iterator[Mapping[str, Any]]]:
    """Print a compact preview and return a replayable iterator containing those rows."""

    if count < 1:
        raise ValueError("count must be positive")
    preview = list(islice(rows, count))
    print("Dataset preview before indexing:")
    for position, row in enumerate(preview):
        prompt = str(row.get("prompt") or "")
        compact_prompt = " ".join(prompt.split())
        if len(compact_prompt) > 240:
            compact_prompt = f"{compact_prompt[:237]}..."
        print(
            f"  row[{position}] row_id={row.get('row_id')!r} "
            f"input_label={row.get('input_label')!r} language={row.get('language')!r} "
            f"prompt={compact_prompt!r}"
        )
    return preview, chain(preview, rows)


def index_stream(
    rows: Iterable[Mapping[str, Any]],
    *,
    embedder: Embedder,
    collection: ChromaCollection,
    split: str = DEFAULT_SPLIT,
    batch_size: int = DEFAULT_BATCH_SIZE,
    workers: int = DEFAULT_WORKERS,
    limit: int | None = None,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    max_in_flight: int | None = None,
    show_progress: bool = True,
) -> IndexingReport:
    """Embed and persist a streaming row source with bounded concurrent memory use.

    At most ``max_in_flight`` complete batches are retained by worker futures. Failed batches are
    retried independently and reported instead of terminating the remaining stream.
    """

    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    if workers <= 0:
        raise ValueError("workers must be positive")
    if limit is not None and limit <= 0:
        raise ValueError("limit must be positive when provided")
    if max_attempts <= 0:
        raise ValueError("max_attempts must be positive")
    in_flight_limit = max_in_flight if max_in_flight is not None else workers * 2
    if in_flight_limit < workers:
        raise ValueError("max_in_flight must be at least the worker count")

    progress = _create_progress(
        total=math.ceil(limit / batch_size) if limit is not None else None,
        enabled=show_progress,
    )
    write_lock = threading.Lock()
    pending: set[Future[BatchResult]] = set()
    submitted_batches = 0
    indexed_rows = 0
    failed_batches = 0
    failed_rows = 0
    skipped_rows = 0
    errors: list[str] = []

    def consume(completed: Iterable[Future[BatchResult]]) -> None:
        nonlocal indexed_rows, failed_batches, failed_rows
        for future in completed:
            result = future.result()
            progress.update(1)
            if result.succeeded:
                indexed_rows += result.rows
            else:
                failed_batches += 1
                failed_rows += result.rows
                errors.append(result.error or "unknown batch failure")
                progress.write(f"Batch failed after {result.attempts} attempts: {result.error}")

    try:
        with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="bge-index") as executor:
            for batch, batch_skipped in _iter_batches(rows, split, batch_size, limit):
                skipped_rows += batch_skipped
                if not batch:
                    continue
                pending.add(
                    executor.submit(
                        _index_batch,
                        batch,
                        embedder,
                        collection,
                        write_lock,
                        max_attempts,
                    )
                )
                submitted_batches += 1
                if len(pending) >= in_flight_limit:
                    completed, pending = wait(pending, return_when=FIRST_COMPLETED)
                    consume(completed)

            while pending:
                completed, pending = wait(pending, return_when=FIRST_COMPLETED)
                consume(completed)
    finally:
        progress.close()

    return IndexingReport(
        submitted_batches=submitted_batches,
        indexed_rows=indexed_rows,
        failed_batches=failed_batches,
        failed_rows=failed_rows,
        skipped_rows=skipped_rows,
        errors=tuple(errors),
    )


def query_collection(
    query_text: str,
    *,
    embedder: Embedder,
    collection: ChromaCollection,
    n_results: int = 5,
) -> list[SimilarPrompt]:
    """Embed a query and return local Chroma matches with ``1 - cosine_distance`` scores."""

    if not query_text.strip():
        raise ValueError("query_text must be non-empty")
    if n_results <= 0:
        raise ValueError("n_results must be positive")
    available = collection.count()
    if available == 0:
        return []

    query_embedding = embedder.get_embeddings([query_text])
    return _query_by_embedding(
        query_embedding,
        collection=collection,
        n_results=min(n_results, available),
    )


def _query_by_embedding(
    query_embedding: list[list[float]],
    *,
    collection: ChromaCollection,
    n_results: int,
) -> list[SimilarPrompt]:
    """Query Chroma with an already computed vector and map cosine distances."""

    result = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results,
        include=["documents", "distances", "metadatas"],
    )
    documents = _first_result_list(result, "documents")
    distances = _first_result_list(result, "distances")
    metadatas = _first_result_list(result, "metadatas")
    matches: list[SimilarPrompt] = []
    for document, distance, metadata in zip(documents, distances, metadatas, strict=True):
        similarity = 1.0 - float(distance)
        matches.append(
            SimilarPrompt(
                document=str(document),
                cosine_similarity=similarity,
                metadata=metadata if isinstance(metadata, Mapping) else {},
            )
        )
    return matches


def query_similar_prompts(query_text: str, n_results: int = 5) -> list[SimilarPrompt]:
    """Query the default persisted collection using endpoint credentials from the environment.

    Required variables are ``HUGGING_FACE_ENDPOINT`` (or ``BGE_M3_ENDPOINT_URL``) and
    ``HF_TOKEN`` (or ``HUGGING_FACE_TOKEN``). ``CHROMA_DB_PATH`` can override ``./chroma_db``.
    """

    embedder = _embedder_from_env()
    collection = get_chroma_collection(_chroma_path_from_env())
    available = collection.count()
    if available == 0:
        print("Query returned 0 matches: the collection is empty.")
        return []
    query_embedding = embedder.get_embeddings([query_text])
    started = perf_counter()
    matches = _query_by_embedding(
        query_embedding,
        collection=collection,
        n_results=min(n_results, available),
    )
    elapsed_ms = (perf_counter() - started) * 1_000
    print(f"Query returned {len(matches)} matches in {elapsed_ms:.2f} ms:")
    for position, match in enumerate(matches, start=1):
        print(
            f"  {position}. similarity={match.cosine_similarity:.6f} "
            f"label={match.metadata.get('input_label', '')!r} document={match.document!r}"
        )
    return matches


def _iter_batches(
    rows: Iterable[Mapping[str, Any]],
    split: str,
    batch_size: int,
    limit: int | None,
) -> Iterator[tuple[list[IndexRecord], int]]:
    batch: list[IndexRecord] = []
    skipped = 0
    source = islice(rows, limit) if limit is not None else iter(rows)
    for stream_index, row in enumerate(source):
        record = _record_from_row(row, split=split, stream_index=stream_index)
        if record is None:
            skipped += 1
            continue
        batch.append(record)
        if len(batch) == batch_size:
            yield batch, skipped
            batch = []
            skipped = 0
    if batch:
        yield batch, skipped
    elif skipped:
        yield [], skipped


def _record_from_row(
    row: Mapping[str, Any],
    *,
    split: str,
    stream_index: int,
) -> IndexRecord | None:
    prompt = row.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        return None
    source_row_id = row.get("row_id")
    row_id = str(source_row_id) if source_row_id else f"id_{stream_index}"
    metadata: Metadata = {"split": split, "row_id": row_id}
    for key in (
        "input_label",
        "response_label",
        "violated_categories",
        "language",
        "dataset_source",
        "provenance",
        "task_type",
    ):
        value = row.get(key)
        if isinstance(value, (str, int, float, bool)):
            metadata[key] = value
    metadata["has_response"] = bool(row.get("response"))
    metadata["has_image"] = bool(row.get("image_path"))
    return IndexRecord(
        record_id=f"{split}_{row_id}",
        document=prompt.strip(),
        metadata=metadata,
    )


def _index_batch(
    batch: Sequence[IndexRecord],
    embedder: Embedder,
    collection: ChromaCollection,
    write_lock: threading.Lock,
    max_attempts: int,
) -> BatchResult:
    texts = [record.document for record in batch]
    for attempt in range(1, max_attempts + 1):
        try:
            embeddings = embedder.get_embeddings(texts)
            if len(embeddings) != len(batch):
                raise RuntimeError(
                    f"embedder returned {len(embeddings)} embeddings for {len(batch)} records"
                )
            with write_lock:
                collection.upsert(
                    ids=[record.record_id for record in batch],
                    documents=texts,
                    embeddings=embeddings,
                    metadatas=[record.metadata for record in batch],
                )
            return BatchResult(rows=len(batch), attempts=attempt)
        except Exception as exc:  # worker boundary must isolate provider/storage failures
            if attempt == max_attempts:
                return BatchResult(
                    rows=len(batch),
                    attempts=attempt,
                    error=f"{type(exc).__name__}: {exc}",
                )
            time.sleep(min(2 ** (attempt - 1), 4))
    raise AssertionError("unreachable")


def _first_result_list(result: Mapping[str, Any], key: str) -> list[Any]:
    value = result.get(key)
    if not isinstance(value, list) or not value or not isinstance(value[0], list):
        return []
    return cast(list[Any], value[0])


def _create_progress(*, total: int | None, enabled: bool) -> Any:
    try:
        from tqdm import tqdm
    except ImportError as exc:  # pragma: no cover - exercised without the optional extra
        raise RuntimeError(
            "Progress monitoring requires the safety-index dependencies. "
            "Run: uv sync --extra safety-index"
        ) from exc
    return tqdm(total=total, unit="batch", desc="Indexing Nemotron", disable=not enabled)


def _embedder_from_env() -> EndpointEmbedder:
    endpoint_url = os.getenv("HUGGING_FACE_ENDPOINT") or os.getenv("BGE_M3_ENDPOINT_URL") or ""
    hf_token = os.getenv("HF_TOKEN") or os.getenv("HUGGING_FACE_TOKEN") or ""
    if not endpoint_url:
        raise RuntimeError("HUGGING_FACE_ENDPOINT or BGE_M3_ENDPOINT_URL is required")
    if not hf_token:
        raise RuntimeError("HF_TOKEN or HUGGING_FACE_TOKEN is required")
    return EndpointEmbedder(endpoint_url, hf_token)


def inference_provider_embedder_from_env() -> InferenceProviderEmbedder:
    """Build the query embedder from an HF token without requiring a dedicated endpoint."""

    hf_token = os.getenv("HF_TOKEN") or os.getenv("HUGGING_FACE_TOKEN") or ""
    if not hf_token:
        raise RuntimeError("HF_TOKEN or HUGGING_FACE_TOKEN is required")
    return InferenceProviderEmbedder(hf_token)


def _chroma_path_from_env() -> Path:
    return Path(os.getenv("CHROMA_DB_PATH") or str(DEFAULT_CHROMA_PATH))


def main() -> int:
    """Index 10,000 streamed rows, then demonstrate a persisted local cosine query."""

    try:
        embedder = _embedder_from_env()
        collection = get_chroma_collection(_chroma_path_from_env())
        dataset_rows = iter(load_dataset_stream(DEFAULT_SPLIT))
        _, replayable_rows = preview_rows(dataset_rows, count=2)
        report = index_stream(
            replayable_rows,
            embedder=embedder,
            collection=collection,
            split=DEFAULT_SPLIT,
            batch_size=DEFAULT_BATCH_SIZE,
            workers=DEFAULT_WORKERS,
            limit=DEFAULT_LIMIT,
        )
        print(f"Indexing report: {report}")
        if report.indexed_rows == 0:
            print("No rows were indexed; query demonstration skipped.", file=sys.stderr)
            return 1
        query_similar_prompts("How can I steal something without getting caught?", n_results=5)
    except (RuntimeError, ValueError) as exc:
        print(f"Safety similarity pipeline failed: {exc}", file=sys.stderr)
        return 1
    return 0 if report.failed_batches == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
