# Title
Upgrade Impact Tool — Session Artifact — Phase 0 through Phase 2 MVP Build and UX Hardening

## Date
2026-04-14

## Status
- **completed**: Phase 0 foundation, Phase 1 MVP truth path, and a substantial Phase 2 UX pass were built in this session.
- **verified**: End-to-end user path from intake creation through analysis, drilldown, review queue, and manual resolution was exercised with live API/DB/UI checks.
- **in progress**: Phase 2 final closure / clean handoff is pending; Phase 2 completion artifact content was drafted in-chat but was not independently verified as committed in this session.
- **deferred**: Phase 3 planning and all larger workflow/reporting/automation follow-ons.

## Session scope
This session covered actual implementation and verification work in the `upgrade-impact-tool` repo across backend, frontend, database bootstrap, seeded data, synchronous analysis execution, review queue behavior, recompute behavior after resolution, and major Phase 2 UX refinement.

This artifact includes only work that actually happened in this session. It does not claim completion for items that were only discussed.

## Objective
Build the documented roadmap in order, starting from the repo shells and contracts, until the system had a real user-facing MVP path:
- intake
- validation
- immutable snapshot persistence
- synchronous analysis execution
- persisted findings and evidence
- results overview
- application and finding drilldown
- review queue
- manual resolution with recompute
- dashboard / overview / application / finding UX hardening

## Completed work

### completed — Phase 0
- Backend bootstrap was made runnable.
- Frontend bootstrap was made runnable.
- Core constants/enums/meta endpoint were implemented and verified.
- Alembic migration foundation was initialized and applied.
- Seed data load path was implemented and verified.
- Initial API skeleton and route shells were implemented.
- Frontend route shells for dashboard, overview, application detail, and finding detail were implemented and bound to live API responses.
- ADR / decision-log work for Phase 0 was created and pushed.

### completed — Phase 1
- Deterministic intake validation service was implemented.
- Intake create / patch / validate / start-analysis path was implemented.
- Immutable customer snapshot persistence was implemented.
- Snapshot creation was wired into analysis start so the system no longer hardcoded the seeded snapshot.
- Seed-loading sequence reset logic was added after discovering sequence drift from explicit seeded IDs.
- KB provenance validation service was added.
- Deterministic applicability evaluation and findings generation were implemented.
- Findings persistence and evidence persistence were implemented.
- Analysis finalization was implemented with counts, status transitions, `completed_utc`, and `duration_ms`.
- Retrieval endpoints were updated to read live generated analysis truth, not only seed assumptions.
- Synchronous API-driven execution path was implemented so `POST /intakes/{id}/analyses` creates, executes, and finalizes the run in one backend flow.
- Review queue endpoint was implemented.
- Finding resolve endpoint was implemented.
- Recompute service was implemented so resolving the last unresolved finding can move parent application and analysis to `READY`.
- Phase 1 completion/checkpoint docs were added during the session.

### completed — Phase 2
- Dashboard was refined with:
  - latest completed analysis
  - active/incomplete analyses
  - completed history
  - top risks
  - top actions
  - summary metrics strip
  - status filter
  - unresolved-only toggle
  - active filter chips
- Analysis overview was refined with:
  - summary metric cards
  - top actions
  - assumptions / missing inputs / derived risks
  - clearer application list
  - readable time formatting
  - human-readable statuses
- Application detail was refined with:
  - readable finding cards
  - priority ordering by status/severity
  - status/severity filters
  - text search
  - active filter chips
  - no-results state
  - status banners
- Finding detail was refined with:
  - structured explanation layout
  - transparency section
  - evidence trust card
  - copy KB reference action
  - status banners
  - resolve flow in-page
- Review queue was refined with:
  - filter/search
  - status banners
  - no-results handling
- Shared UX utilities/components were added or updated:
  - status label formatter
  - status help
  - status banner
  - loading / error / empty state components
- Phase 2 midpoint checkpoint doc was added during the session.

## Verified behavior

### verified — environment / foundation
- Backend health endpoint returned `{"status":"ok"}`.
- Frontend was made to load against the local backend after fixing Vite/config/API issues.
- Enum metadata endpoint returned the expected status/taxonomy/environment values.
- Alembic migration ran successfully.
- Seed load ran successfully and inserted the expected base rows.

### verified — Phase 1 truth path
- Intake create returned a draft intake ID.
- Intake patch worked against the intended intake.
- Intake validate returned `INTAKE_VALIDATED` for complete payloads and `BLOCKED` for incomplete ones.
- Starting analysis created a new snapshot (`snapshot_id > 1`) for a materially different intake.
- `analysis_runs` correctly pointed to the new snapshot.
- Findings generation created persisted findings for live analyses.
- Evidence rows were persisted and retrievable.
- Analysis finalization updated counts and moved analyses into final states such as `REVIEW_REQUIRED`.
- `POST /intakes/{id}/analyses` was corrected to return the actual final status instead of stale `ANALYSIS_RUNNING`.
- `completed_utc` and `duration_ms` were written for completed runs.
- Overview, application detail, and finding detail endpoints returned live generated data for non-seed analyses.

### verified — review workflow
- Review queue endpoint returned unresolved `UNKNOWN` / `REQUIRES_REVIEW` items.
- Resolving a finding via API changed that finding to `RESOLVED`.
- Resolved items disappeared from the review queue.
- Recompute updated parent `analysis_applications` and `analysis_runs` rollups.
- Resolving the final unresolved item for a run moved application and analysis to `READY`.
- Overview support data was corrected so resolved findings no longer polluted `missing_inputs`, `derived_risks`, `top_risks`, or `top_actions` where inappropriate.

### verified — frontend user path
Verified via live browser screenshots and API checks in this session:
- `/dashboard`
- `/intakes/new`
- `/analyses/{analysis_id}`
- `/analyses/{analysis_id}/applications/{analysis_application_id}`
- `/findings/{finding_id}`
- `/review-queue`
- finding resolution from finding detail UI
- updated parent state after resolution

### verified — UX hardening
- Human-readable status labels replaced raw enum strings in major surfaces.
- Status banners render for `UNKNOWN`, `REQUIRES_REVIEW`, and `BLOCKED`.
- Reusable loading/error/empty states are in use.
- Dashboard filters, application filters, and review-queue filters all functioned in the UI.

## Files or modules touched
The exact full file list is large; below are the important files/modules known to have been created or materially changed in this session.

### backend
- `backend/app/api/v1/health.py`
- `backend/app/api/v1/intake.py`
- `backend/app/api/v1/intakes.py`
- `backend/app/api/v1/review_queue.py`
- `backend/app/api/v1/review_actions.py`
- `backend/app/core/constants.py`
- `backend/app/core/enums.py`
- `backend/app/core/config.py`
- `backend/app/main.py`
- `backend/app/repositories/intake_repository.py`
- `backend/app/repositories/analysis_repository.py`
- `backend/app/repositories/dashboard_repository.py`
- `backend/app/repositories/review_queue_repository.py`
- `backend/app/schemas/common.py`
- `backend/app/schemas/intake_api.py`
- `backend/app/schemas/validation.py`
- `backend/app/schemas/analysis.py`
- `backend/app/schemas/dashboard.py`
- `backend/app/schemas/review_queue.py`
- `backend/app/schemas/review_actions.py`
- `backend/app/services/intake_validation_service.py`
- `backend/app/services/intake_workflow_service.py`
- `backend/app/services/snapshot_service.py`
- `backend/app/services/kb_provenance_service.py`
- `backend/app/services/versioning.py`
- `backend/app/services/applicability_service.py`
- `backend/app/services/findings_service.py`
- `backend/app/services/analysis_results_service.py`
- `backend/app/services/analysis_execution_service.py`
- `backend/app/services/analysis_recompute_service.py`
- `backend/app/services/review_queue_service.py`
- `backend/app/services/review_action_service.py`
- `backend/scripts/load_seed.sh`
- `backend/seeds/seed_001.sql`
- `backend/alembic.ini`
- `backend/migrations/...`

### frontend
- `frontend/src/pages/DashboardPage.tsx`
- `frontend/src/pages/IntakeNewPage.tsx`
- `frontend/src/pages/AnalysisOverviewPage.tsx`
- `frontend/src/pages/ApplicationDetailPage.tsx`
- `frontend/src/pages/FindingDetailPage.tsx`
- `frontend/src/pages/ReviewQueuePage.tsx`
- `frontend/src/routes/index.tsx`
- `frontend/src/services/intakes.ts`
- `frontend/src/services/analyses.ts`
- `frontend/src/services/findings.ts`
- `frontend/src/services/dashboard.ts`
- `frontend/src/services/reviewQueue.ts`
- `frontend/src/components/LoadingState.tsx`
- `frontend/src/components/ErrorState.tsx`
- `frontend/src/components/EmptyState.tsx`
- `frontend/src/components/StatusHelp.tsx`
- `frontend/src/components/StatusBanner.tsx`
- `frontend/src/utils/time.ts`
- `frontend/src/utils/status.ts`
- `frontend/src/types/common.ts`

### docs / roadmap / artifacts
- `docs/decisions/...` ADR files for Phase 0
- `docs/Phase 1 MVP Checkpoint.md`
- `docs/Phase 1 Completion Artifact.md`
- `docs/Phase 2 Midpoint Checkpoint.md`
- `docs/Phase 2 Completion Artifact.md` was discussed and drafted in-chat, but this artifact does **not** assert it was verified as committed unless the repo confirms it in the next chat.

## Important implementation details
- Analysis execution is synchronous in the current MVP path.
- Snapshot persistence is immutable; analyses bind to the `snapshot_id` used at execution time.
- Seed loading required explicit sequence reset because seeded explicit IDs caused Postgres sequence drift.
- Parent rollups can go stale if findings are mutated outside the recompute path; `AnalysisRecomputeService` is the intended correction mechanism after review actions.
- Overview support queries were corrected so resolved findings no longer drive unresolved-state messaging.
- Dashboard top-risk/top-action queries were deduplicated to avoid repeated headlines/actions dominating the panels.
- Human-readable status formatting is frontend-side via a shared utility.
- Status-specific explanatory banners are frontend-side and currently cover `UNKNOWN`, `REQUIRES_REVIEW`, and `BLOCKED`.

## Current system state
- The system is now credible as a user-facing MVP.
- The core user path is coherent:
  - create intake
  - validate
  - run analysis
  - inspect dashboard / overview / application / finding detail
  - inspect review queue
  - resolve unresolved items
  - parent rollups update
- Dashboard, overview, application detail, finding detail, and review queue are all functional and have received meaningful UX hardening.
- Search/filter/prioritization exists on dashboard, application detail, and review queue.
- The product is still not fully operationalized for enterprise workflow depth.

## Known issues / remaining work

### in progress
- Phase 2 is functionally very close to complete, but a final verified closure pass and authoritative completion handoff should still be done deliberately.

### deferred
- No global search entrypoint.
- No server-side filtering for application detail.
- No overview-level application filtering.
- No review assignment workflow.
- No comments/history workflow for review items.
- No notification system.
- No export/reporting hardening beyond current MVP surfaces.
- No refresh/delta orchestration.
- No full KB parser automation.
- No admin trace viewer.

### plain uncertainties
- Some docs/artifacts were drafted in-chat and the user indicated they were added/pushed, but this artifact does not independently re-audit every pushed doc file from the repo.
- This session did not perform a final comprehensive regression sweep across every route after the last UI refinements.

## Recommended next step
Do **not** continue random UI polishing from memory.

Recommended next step for the next chat:
1. verify whether `docs/Phase 2 Completion Artifact.md` exists in-repo and matches the intended closure state
2. perform a short targeted regression pass on:
   - dashboard filters
   - overview top actions / assumptions / timing
   - application filters/chips
   - finding resolve flow
   - review queue filters
3. if that passes, formally close Phase 2 and write a bounded **Phase 3 plan artifact** before any more code

## Safe stopping point
Safe to stop here.

The repo now has a coherent Phase 1 MVP truth path and a substantial Phase 2 UX layer. The next chat should start from artifact/doc verification and Phase 3 planning rather than more implementation drift.

## Resume instruction
Resume from the current repo state and authoritative docs only.

First, verify the Phase 2 closure state in the repo, especially the existence/content of the Phase 2 completion artifact and the current frontend/backend files involved in dashboard, overview, application detail, finding detail, and review queue.

Do not redesign architecture.
Do not add new workflow systems until Phase 3 is explicitly planned.
Prefer a short regression/verification pass, then produce a bounded Phase 3 planning artifact.

## Recommended filename
`docs/upgrade-impact-tool_session_artifact_2026-04-14_phase0_to_phase2.md`

## Bottom line
This session took the Upgrade Impact Tool from scaffolded contracts and shells to a real, verified MVP path with deterministic backend execution, immutable snapshotting, evidence-backed findings, review resolution with recompute, and a substantially hardened user-facing UI across dashboard, overview, application detail, finding detail, and review queue. The right next move is not more improvised implementation; it is to verify final Phase 2 closure and then plan Phase 3 cleanly.
