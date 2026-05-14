# Gate 18Z Disabled Vector Draft Generator Adapter Build Plan

System: Upgrade Impact Analysis Tool  
Phase: Disabled Vector Draft Generator Adapter  
Status: Proposed  
Generated: 2026-05-14

## Purpose

Gate 18Z adds a disabled vector draft generator adapter that consumes the Gate 18Y generation contract and refuses draft generation.

This gate does not enable production semantic retrieval, does not call an embedding model, does not call an LLM, and does not generate impact prose.

## Files

| File | Purpose |
|---|---|
| `backend/app/scripts/disabled_vector_draft_generator_adapter.py` | Defines disabled vector draft generator request/result schema and refusal adapter |
| `backend/app/scripts/validate_disabled_vector_draft_generator_adapter.py` | Validates refusal behavior, fail-closed invalid contract handling, unknown adapter rejection, and no draft output |
| `backend/app/scripts/run_gate18z_disabled_vector_draft_generator_adapter.py` | Gate runner |

## Source Artifact

Gate 18Z consumes:

```text
kbs/retrieval/kb_fixture_vector_draft_generation_contract.v1.json
```

If the generation contract is absent in a clean checkout, Gate 18Z bootstraps the deterministic local skeleton fixture and generation contract through the Gate 18Y contract path.

Gate 18Z writes locally:

```text
kbs/retrieval/kb_fixture_vector_disabled_generator.v1.json
```

Gate 18Z must not write:

```text
kbs/retrieval/kb_fixture_vector_generated_draft.v1.json
```

## Adapter Behavior

A ready disabled contract produces:

```text
status=REFUSED
reason=DISABLED_ADAPTER_REFUSES_DRAFT_GENERATION
would_generate=false
draft_generation_enabled=false
llm_call_allowed=false
llm_call_performed=false
generated_text=""
```

Invalid contract inputs produce:

```text
status=REFUSED
reason=DISABLED_ADAPTER_INPUTS_INVALID
```

Unknown adapters fail closed.

## Validation Command

From `backend`:

```bash
python -m app.scripts.run_gate18z_disabled_vector_draft_generator_adapter
```

Expected output:

```text
[gate18z:disabled-generator] OK
[gate18z:disabled-generator] ready_contract=refused
[gate18z:disabled-generator] invalid_contract=fail_closed
[gate18z:disabled-generator] unknown_adapter=fail_closed
[gate18z:disabled-generator] llm_call_performed=false
```

Recommended next gate: **Gate 19A — Hybrid Retrieval Design Contract**.
