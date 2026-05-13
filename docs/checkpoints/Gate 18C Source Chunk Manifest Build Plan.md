# Gate 18C Source Chunk Manifest Build Plan

System: Upgrade Impact Analysis Tool  
Phase: Source Chunk Manifest Discovery and Skeleton Manifest Build  
Status: Proposed  
Generated: 2026-05-13

## Purpose

Gate 18C discovers the real Gate 2 chunk manifest and normalizes real chunk collections into the Gate 18B embedding manifest skeleton.

This gate does not call an embedding model and does not create vector files.

## Files

| File | Purpose |
|---|---|
| `backend/app/scripts/build_embedding_manifest_from_chunks.py` | Loads Gate 2 chunk collections and builds an embedding manifest skeleton |
| `backend/app/scripts/validate_gate18c_source_chunk_manifest_build.py` | Validates discovery and temporary skeleton manifest build |
| `backend/app/scripts/run_gate18c_source_chunk_manifest_build.py` | Gate runner |

## Source Artifacts

Gate 18C uses:

```text
kbs/manifests/kb_search_context_chunks_manifest.json
kbs/search_context_chunks/
```

The output contract targets:

```text
kbs/retrieval/kb_embedding_manifest.v1.json
```

## Validation Command

From `backend`:

```bash
python -m app.scripts.run_gate18c_source_chunk_manifest_build
```

Expected output:

```text
[gate18c:chunks] OK
[gate18c:chunks] source_chunk_manifest=discovered
[gate18c:chunks] real_chunks=normalized
[gate18c:chunks] skeleton_manifest=written
[gate18c:chunks] vectors=not_created
```

Recommended next gate: **Gate 18D — Persist Full Embedding Manifest Skeleton**.
