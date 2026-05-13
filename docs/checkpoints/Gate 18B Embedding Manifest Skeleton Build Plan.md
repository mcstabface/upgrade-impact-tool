# Gate 18B Embedding Manifest Skeleton Build Plan

System: Upgrade Impact Analysis Tool  
Phase: Embedding Manifest Skeleton and Validator  
Status: Proposed  
Generated: 2026-05-13

## Purpose

Gate 18B adds the embedding manifest skeleton, deterministic embedding input builder, cache-key helper, and validator.

This gate does not call an embedding model, create vectors, replace BM25 retrieval, or change draft generation.

## Files

| File | Purpose |
|---|---|
| `backend/app/scripts/embedding_manifest_skeleton.py` | Manifest dataclasses, input builder, cache-key helper, writer, validator |
| `backend/app/scripts/validate_embedding_manifest_skeleton.py` | Validation cases |
| `backend/app/scripts/run_gate18b_embedding_manifest_skeleton.py` | Gate runner |

## Scope

In scope:

- deterministic embedding input text,
- deterministic chunk text hash,
- deterministic embedding cache key,
- deterministic vector record ID placeholder,
- manifest skeleton dataclass,
- skeleton manifest writer,
- duplicate chunk validation,
- cache-key invalidation for text/model/dimensions.

Out of scope:

- embedding API calls,
- vector files,
- vector search,
- hybrid retrieval,
- BM25 replacement,
- draft generation changes.

## Validation Command

From `backend`:

```bash
python -m app.scripts.run_gate18b_embedding_manifest_skeleton
```

Expected output:

```text
[gate18b:manifest] OK
[gate18b:manifest] cache_key=stable
[gate18b:manifest] invalidation=text_model_dimensions
[gate18b:manifest] manifest_skeleton=valid
[gate18b:manifest] embedding_calls=forbidden
```

Recommended next gate: **Gate 18C — Source Chunk Manifest Discovery and Skeleton Manifest Build**.
