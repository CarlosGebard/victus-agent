# Nemotron safety semantic index

This standalone pipeline does not run inside the Victus agent graph and does not replace the
current Llama Guard safety precheck.

## Prerequisites

Install the optional dependencies and provide the dedicated BGE-M3 endpoint credentials:

```bash
uv sync --extra safety-index
export HUGGING_FACE_ENDPOINT="https://your-dedicated-endpoint"
export HF_TOKEN="your-token"
```

Do not commit the endpoint token. `CHROMA_DB_PATH` optionally overrides the default `./chroma_db`.

## First 10,000-row run

```bash
uv run --extra safety-index python -m infrastructure.safety_similarity
```

The command prints two compact dataset rows before the first endpoint request, streams the `train`
split, submits batches of 32 to four workers, persists to `nemotron_safety_bge`, and runs one local
cosine query. The reported query time measures only the local Chroma lookup after the remote query
embedding is available. Failed batches are retried three times and reported; a non-zero exit means
at least one batch did not persist.

Re-running is safe because records use `train_<row_id>` identifiers and Chroma `upsert`.

## Validation without a paid endpoint

```bash
uv run --extra test --extra safety-index pytest tests/infrastructure/test_safety_similarity.py
uv run --extra test --extra safety-index python -m compileall src tests
```

The tests use deterministic local embeddings and a temporary persistent Chroma directory; they do
not download the dataset or call Hugging Face.

## Train the logistic baseline

Training reads the persisted vectors locally and makes no endpoint calls:

```bash
uv run --extra safety-index --extra safety-training \
  python -m infrastructure.safety_classifier train
```

The command excludes topic-following and image-dependent rows, creates deterministic 70/15/15
stratified partitions, selects L2 regularization and a threshold targeting 95% validation recall
for `unsafe`, then writes `model.npz` and `manifest.json` under
`data/runtime/safety_classifier/`.

Classify one query through the `hf-inference` provider. Only `HF_TOKEN` is required; the dedicated
bulk endpoint may be paused:

```bash
uv run --env-file .env --extra safety-index \
  python -m infrastructure.safety_classifier query "How can I steal money?"
```

The runtime calls `feature_extraction` because the logistic model requires a 1024-dimensional
vector; `sentence_similarity` returns pairwise scores and is not used by this classifier. It loads
NumPy arrays with checksum validation and does not require scikit-learn. See
`docs/contracts/safety-logistic-artifact-v1.md` for the artifact contract.

## Recovery

- Reduce `DEFAULT_BATCH_SIZE` if the endpoint rejects 32 texts per request.
- Reduce `DEFAULT_WORKERS` if the endpoint throttles four concurrent requests.
- Re-run after transient failures; successful IDs are updated in place.
- If the embedding dimension or metric changes, use a new collection name. Do not reuse an
  incompatible collection.
