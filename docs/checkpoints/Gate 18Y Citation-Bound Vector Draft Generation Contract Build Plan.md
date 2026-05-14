# Gate 18Y Citation-Bound Vector Draft Generation Contract Build Plan

System: Upgrade Impact Analysis Tool  
Phase: Citation-Bound Vector Draft Generation Contract  
Status: Proposed  
Generated: 2026-05-14

## Purpose

Gate 18Y defines the citation-bound vector draft generation contract while keeping generation disabled.

This gate does not enable production semantic retrieval, does not call an embedding model, does not call an LLM, and does not generate impact prose.

## Files

| File | Purpose |
|---|---|
| `backend/app/scripts/citation_bound_vector_draft_generation_contract.py` | Builds disabled generation contract from citation-bound vector draft skeleton |
| `backend/app/scripts/validate_citation_bound_vector_draft_generation_contract.py` | Validates ready and blocked generation contract behavior |
| `backend/app/scripts/run_gate18y_citation_bound_vector_draft_generation_contract.py` | Gate runner |

## Source Artifact

Gate 18Y requires:

```text
kbs/retrieval/kb_fixture_vector_draft_skeleton.v1.json
```

Gate 18Y writes locally:

```text
kbs/retrieval/kb_fixture_vector_draft_generation_contract.v1.json
```

## Contract Behavior

A valid skeleton produces:

```text
status=GENERATION_DISABLED_CONTRACT_READY
generation_adapter=disabled
draft_generation_enabled=false
llm_call_allowed=false
llm_call_performed=false
```

Blocked cases include:

```text
draft_generation_enabled=true
generated_text already present in evidence-bound sections
missing evidence IDs or citation labels
bad skeleton status
```

## Validation Coverage

Gate 18Y validates:

```text
skeleton status must be VECTOR_DRAFT_SKELETON_READY
production_retrieval_enabled remains false
draft_generation_enabled remains false
llm_call_performed remains false
sections are present
generated_text remains empty
evidence bindings are present
generation-enabled skeleton blocks contract
generated-text skeleton blocks contract
llm_call_allowed=false
```

## Validation Command

From `backend`:

```bash
python -m app.scripts.run_gate18y_citation_bound_vector_draft_generation_contract
```

Expected output:

```text
[gate18y:generation-contract] OK
[gate18y:generation-contract] disabled_contract=ready
[gate18y:generation-contract] generation_enabled=blocked
[gate18y:generation-contract] generated_text=blocked
[gate18y:generation-contract] llm_call_allowed=false
```

Recommended next gate: **Gate 18Z — Disabled Vector Draft Generator Adapter**.
