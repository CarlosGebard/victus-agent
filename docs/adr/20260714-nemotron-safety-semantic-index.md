# ADR: Isolate the Nemotron semantic safety index

- Status: accepted
- Date: 2026-07-14

## Context

Victus needs a persistent semantic index of Nemotron content-safety prompts using BGE-M3. The
existing safety precheck and Llama Guard adapters are an active graph path with a different
classification contract. Combining ingestion, retrieval, and graph classification would couple a
cost-sensitive batch process to request-time safety behavior.

## Decision

Implement the Nemotron/BGE-M3/Chroma workflow as a standalone infrastructure module. It reads the
dataset in streaming mode, bounds concurrent batches, stores prompt embeddings in a dedicated
cosine collection, and exposes local similarity retrieval. It is not imported by or wired into the
agent graph. Endpoint credentials are environment-only runtime inputs. A binary logistic model may
be trained from text-only safety rows and exported as checksum-bound NumPy/JSON so request-time
classification does not require scikit-learn or Chroma. Bulk embedding uses the dedicated endpoint;
request-time query embedding uses `hf-inference` with `HF_TOKEN` so scale-to-zero does not make the
classifier unavailable.

## Consequences

- Bulk indexing can be run, retried, and paid for independently of agent requests.
- Stable dataset `row_id` values make indexing idempotent through Chroma upserts.
- Query embeddings use the `hf-inference` provider without changing GuardLlama.
- Logistic training excludes topic-following and image-dependent examples and treats `unsafe` as
  the positive class.
- The logistic model is an experimental baseline until it passes official validation/test splits.
- Runtime safety routing will not use these similarities until a separate integration decision is
  made and validated.
