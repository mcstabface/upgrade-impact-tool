# Gate 18A Embedding Manifest Vector Store Design Spec

System: Upgrade Impact Analysis Tool  
Phase: Embedding Manifest and Vector Store Design  
Status: Proposed design  
Generated: 2026-05-13

## Purpose

Gate 18A defines the embedding manifest and vector store design before generating embeddings.

This gate is design-only. It does not call an embedding model, does not create vectors, does not replace BM25 retrieval, and does not change impact draft generation.

## Baseline

Gate 18A starts after the deterministic retrieval and review/auth work:

- Gate 2 completed deterministic source text extraction and chunking.
- Gate 3 completed lexical retrieval index and query.
- Gate 4 completed retrieval diagnostics and controls.
- Gate 5 completed deterministic BM25 ranking and evaluation.
- Gate 6 completed evidence-only impact context assembly.
- Gate 17M completed adapter config health plus existing mutation smoke.

## Design Goals

Embedding support must be:

- deterministic at the manifest level,
- reproducible from chunk identity and model metadata,
- cacheable,
- invalidatable when source chunks change,
- comparable against BM25 before adoption,
- additive to existing retrieval,
- citation preserving,
- disabled until validation passes.

## Non-Goals

Gate 18A does not implement:

- embedding API calls,
- local embedding generation,
- vector similarity search,
- hybrid retrieval ranking,
- retrieval behavior changes,
- LLM draft generation changes.

## Proposed Embedding Manifest

Future manifest path:

```text
kbs/retrieval/kb_embedding_manifest.v1.json
```

Proposed shape:

```json
{
  "manifest_version": "1",
  "status": "DESIGN_ONLY_NOT_EMBEDDED",
  "source_chunk_manifest": "kbs/search/kb_search_chunks.v1.json",
  "source_chunk_manifest_sha256": "...",
  "embedding_provider": "openai",
  "embedding_model": "text-embedding-3-small",
  "embedding_dimensions": 1536,
  "embedding_input_policy": "chunk_text_with_stable_metadata_prefix_v1",
  "embedding_cache_key_policy": "sha256(model|dimensions|input_policy|chunk_id|chunk_text_sha256)",
  "vector_store": {
    "kind": "local_jsonl_float32",
    "path": "kbs/retrieval/kb_vectors.v1.jsonl",
    "index_path": "kbs/retrieval/kb_vector_index.v1.json"
  },
  "created_at_utc": null,
  "chunks": []
}
```

The exact source chunk manifest path must be confirmed by a future implementation gate before vectors are generated.

## Chunk Record Contract

Each embedded chunk record should include:

```json
{
  "chunk_id": "stable chunk id",
  "source_id": "source evidence id",
  "source_path": "source file or extracted text artifact",
  "source_span": {
    "start": 0,
    "end": 0
  },
  "chunk_text_sha256": "...",
  "embedding_input_sha256": "...",
  "embedding_cache_key": "...",
  "vector_record_id": "...",
  "citation_payload": {}
}
```

Chunk identity must come from the existing deterministic chunking layer. Embeddings must not invent new chunk IDs.

## Embedding Input Policy

Embedding input must be stable and auditable.

Proposed policy:

```text
chunk_text_with_stable_metadata_prefix_v1
```

Input format:

```text
source_id: <source_id>
chunk_id: <chunk_id>
text:
<chunk_text>
```

The metadata prefix is included to reduce collision ambiguity while preserving deterministic input hashing.

## Cache Key Policy

Cache key formula:

```text
sha256(model|dimensions|input_policy|chunk_id|chunk_text_sha256)
```

Changing any of these must invalidate the cached vector:

- embedding model,
- configured dimensions,
- input policy,
- chunk ID,
- chunk text hash.

## Vector Store Design

Initial store should be local and inspectable:

```text
kbs/retrieval/kb_vectors.v1.jsonl
```

One JSONL row per vector:

```json
{
  "vector_record_id": "...",
  "embedding_cache_key": "...",
  "chunk_id": "...",
  "model": "text-embedding-3-small",
  "dimensions": 1536,
  "vector": [0.0]
}
```

A companion index should map chunk IDs and cache keys to row offsets or record IDs:

```text
kbs/retrieval/kb_vector_index.v1.json
```

A later implementation may replace JSONL with SQLite or FAISS, but Gate 18B should begin with local JSONL for transparency.

## Retrieval Integration Policy

Embeddings must be introduced as an additive candidate source.

Required future comparison modes:

```text
bm25_only
vector_only
hybrid_bm25_vector
```

Hybrid retrieval should not replace BM25 until evaluation proves it improves recall without degrading citation precision.

## Evaluation Requirements

A future embedding implementation must compare:

- top-k overlap with BM25,
- evidence group coverage,
- citation-bearing result count,
- missing expected evidence cases,
- false-positive semantic neighbors,
- latency and storage size.

The first hybrid evaluation should reuse the existing Gate 5 retrieval evaluation queries when possible.

## Safety and Governance Requirements

Embedding artifacts must preserve:

- source traceability,
- citation payloads,
- deterministic source hashes,
- no generated claims,
- no mutation of reviewed artifacts,
- no finalization.

Embedding generation must be a separate explicit command. It must not run implicitly during review mutation or draft generation.

## Required Test Matrix Before Implementation

A future implementation gate must test:

- missing source chunk manifest fails,
- chunk records without stable IDs fail,
- chunk text hash changes invalidate cache keys,
- model change invalidates cache keys,
- dimension change invalidates cache keys,
- vector count equals embedded chunk count,
- vector dimensions match configured dimensions,
- citation payload survives vector indexing,
- BM25-only retrieval remains available,
- hybrid retrieval can be evaluated without changing draft generation.

## Recommended Next Gate

Recommended next gate:

**Gate 18B — Embedding Manifest Skeleton and Validator**

Gate 18B should add a manifest dataclass, deterministic cache-key helper, and validator. It should not call an embedding model or write vectors.
