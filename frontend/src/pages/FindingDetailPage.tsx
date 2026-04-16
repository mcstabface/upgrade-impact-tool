import { useCallback, useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";

import { canManageReviews, getCurrentRole } from "../auth/role";
import { formatStatusLabel } from "../utils/status";
import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";
import StatusHelp from "../components/StatusHelp";
import StatusBanner from "../components/StatusBanner";
import {
  getFindingDetail,
  resolveFinding,
  type FindingDetailResponse,
} from "../services/findings";
import { createReviewItem } from "../services/reviewItems";

export default function FindingDetailPage() {
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const currentRole = getCurrentRole();
  const canManageReviewWork = canManageReviews(currentRole);

  const [data, setData] = useState<FindingDetailResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [resolutionNote, setResolutionNote] = useState(
    "Reviewed manually; no further action required for current scope.",
  );
  const [resolving, setResolving] = useState(false);
  const [resolveMessage, setResolveMessage] = useState<string | null>(null);
  const [copyMessage, setCopyMessage] = useState<string | null>(null);
  const [reviewReason, setReviewReason] = useState(
    "Manual review required before implementation decision.",
  );
  const [assignedOwnerUserId, setAssignedOwnerUserId] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [creatingReviewItem, setCreatingReviewItem] = useState(false);
  const [reviewItemMessage, setReviewItemMessage] = useState<string | null>(null);

  const analysisId = searchParams.get("analysisId");
  const applicationId = searchParams.get("applicationId");

  const loadFindingDetail = useCallback(async () => {
    if (!id) return;

    setError(null);

    try {
      const result = await getFindingDetail(id);
      setData(result);
    } catch (err) {
      setError((err as Error).message);
    }
  }, [id]);

  useEffect(() => {
    loadFindingDetail();
  }, [loadFindingDetail]);

  async function handleResolve(event: React.FormEvent) {
    event.preventDefault();
    if (!id || !canManageReviewWork) return;

    setResolving(true);
    setError(null);
    setResolveMessage(null);

    try {
      const result = await resolveFinding(id, resolutionNote);

      setData((current) =>
        current
          ? {
              ...current,
              status: result.finding_status,
              reason_for_status: result.resolution_note,
            }
          : current,
      );

      setResolveMessage("Finding resolved.");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setResolving(false);
    }
  }

  async function handleCreateReviewItem(event: React.FormEvent) {
    event.preventDefault();
    if (!id || !data || !canManageReviewWork) return;

    const trimmedReason = reviewReason.trim();
    const trimmedOwner = assignedOwnerUserId.trim();
    const trimmedDueDate = dueDate.trim();

    setReviewItemMessage(null);
    setError(null);

    if (!trimmedReason) {
      setError("Review reason is required.");
      return;
    }

    if (!trimmedOwner) {
      setError("Assigned owner is required.");
      return;
    }

    if (!trimmedDueDate) {
      setError("Due date is required.");
      return;
    }

    setCreatingReviewItem(true);

    try {
      const result = await createReviewItem({
        finding_id: data.finding_id,
        review_reason: trimmedReason,
        assigned_owner_user_id: trimmedOwner,
        due_date: trimmedDueDate,
      });

      setReviewItemMessage(
        `Review item ${result.review_item_id} created with status ${result.review_status}.`,
      );
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setCreatingReviewItem(false);
    }
  }

  async function handleCopyKbReference() {
    if (!data) return;

    const kbReference = `${data.evidence.kb_article_number} — ${data.evidence.kb_title}`;

    try {
      await navigator.clipboard.writeText(kbReference);
      setCopyMessage("KB reference copied.");
    } catch {
      setCopyMessage("Could not copy KB reference.");
    }
  }

  if (error) {
    return (
      <ErrorState
        title="Could not load finding detail"
        message={error}
        onRetry={loadFindingDetail}
        retryLabel="Retry Load"
      />
    );
  }

  if (!data) return <LoadingState />;

  const canResolve =
    canManageReviewWork &&
    (
      data.status === "UNKNOWN" ||
      data.status === "REQUIRES_REVIEW" ||
      data.status === "BLOCKED"
    );

  return (
    <main style={{ padding: "2rem", fontFamily: "sans-serif", maxWidth: "56rem" }}>
      <p>
        {analysisId && applicationId ? (
          <Link to={`/analyses/${analysisId}/applications/${applicationId}`}>
            Back to Application Detail
          </Link>
        ) : (
          <Link to="/dashboard">Back to Dashboard</Link>
        )}
      </p>

      <h1>{data.headline}</h1>
      <p>Status: {formatStatusLabel(data.status)}</p>
      <StatusHelp status={data.status} />
      <StatusBanner status={data.status} />
      <p>Severity: {data.severity}</p>
      <p>Taxonomy: {data.change_taxonomy}</p>
      <p>Application: {data.application_name}</p>
      <p>Module: {data.module_name ?? "N/A"}</p>
      <p>
        Version Range: {data.version_range.from_version ?? "N/A"} →{" "}
        {data.version_range.to_version ?? "N/A"}
      </p>

      <section style={{ marginBottom: "2rem" }}>
        <h2>What Changed</h2>
        <p>{data.plain_language_summary}</p>
      </section>

      {data.business_impact_summary && (
        <section style={{ marginBottom: "2rem" }}>
          <h2>Why It Matters</h2>
          <p>{data.business_impact_summary}</p>
        </section>
      )}

      {data.technical_impact_summary && (
        <section style={{ marginBottom: "2rem" }}>
          <h2>Technical Impact</h2>
          <p>{data.technical_impact_summary}</p>
        </section>
      )}

      {data.recommended_action && (
        <section style={{ marginBottom: "2rem" }}>
          <h2>Recommended Action</h2>
          <p>{data.recommended_action}</p>
        </section>
      )}

      <section style={{ marginBottom: "2rem" }}>
        <h2>Transparency</h2>

        {data.reason_for_status && (
          <>
            <h3>Reason for Status</h3>
            <p>{data.reason_for_status}</p>
          </>
        )}

        {data.assumptions.length > 0 && (
          <>
            <h3>Assumptions</h3>
            <ul>
              {data.assumptions.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </>
        )}

        {data.missing_inputs.length > 0 && (
          <>
            <h3>Missing Inputs</h3>
            <ul>
              {data.missing_inputs.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </>
        )}
      </section>

      {canResolve ? (
        <section style={{ marginBottom: "2rem" }}>
          <h2>Resolve Finding</h2>
          <form onSubmit={handleResolve}>
            <div>
              <label>Resolution Note </label>
              <input
                value={resolutionNote}
                onChange={(e) => setResolutionNote(e.target.value)}
                style={{ width: "32rem", maxWidth: "100%" }}
              />
            </div>
            <div style={{ marginTop: "1rem" }}>
              <button type="submit" disabled={resolving}>
                {resolving ? "Resolving..." : "Resolve Finding"}
              </button>
            </div>
          </form>
          {resolveMessage && <p>{resolveMessage}</p>}
        </section>
      ) : (
        <section style={{ marginBottom: "2rem" }}>
          <h2>Resolve Finding</h2>
          <p>Reviewer or admin role is required to resolve findings.</p>
        </section>
      )}

      {canManageReviewWork ? (
        <section style={{ marginBottom: "2rem" }}>
          <h2>Create Review Item</h2>
          <form onSubmit={handleCreateReviewItem}>
            <div style={{ marginBottom: "1rem" }}>
              <label>Review Reason </label>
              <input
                value={reviewReason}
                onChange={(e) => setReviewReason(e.target.value)}
                style={{ width: "32rem", maxWidth: "100%" }}
              />
            </div>

            <div style={{ marginBottom: "1rem" }}>
              <label>Assigned Owner </label>
              <input
                value={assignedOwnerUserId}
                onChange={(e) => setAssignedOwnerUserId(e.target.value)}
                placeholder="owner_user_id"
                style={{ width: "20rem", maxWidth: "100%" }}
              />
            </div>

            <div style={{ marginBottom: "1rem" }}>
              <label>Due Date </label>
              <input
                type="date"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
              />
            </div>

            <button type="submit" disabled={creatingReviewItem}>
              {creatingReviewItem ? "Creating..." : "Create Review Item"}
            </button>
          </form>

          {reviewItemMessage && <p>{reviewItemMessage}</p>}
        </section>
      ) : (
        <section style={{ marginBottom: "2rem" }}>
          <h2>Create Review Item</h2>
          <p>Reviewer or admin role is required to create review items.</p>
        </section>
      )}

      <section
        style={{
          border: "1px solid #ccc",
          padding: "1rem",
          marginBottom: "2rem",
        }}
      >
        <h2 style={{ marginTop: 0 }}>Source Evidence</h2>
        <p>
          <strong>KB Article:</strong> {data.evidence.kb_article_number}
        </p>
        <p>
          <strong>Title:</strong> {data.evidence.kb_title}
        </p>
        <p>
          <strong>Published:</strong> {data.evidence.publication_date}
        </p>
        <p>
          <strong>Excerpt:</strong> {data.evidence.evidence_excerpt}
        </p>
        {data.evidence.reference_section && (
          <p>
            <strong>Reference Section:</strong> {data.evidence.reference_section}
          </p>
        )}

        <div style={{ marginTop: "1rem" }}>
          <button type="button" onClick={handleCopyKbReference}>
            Copy KB Reference
          </button>
        </div>

        {copyMessage && <p>{copyMessage}</p>}

        <p style={{ marginTop: "1rem" }}>
          <a href={data.evidence.kb_url} target="_blank" rel="noreferrer">
            Open Source Link
          </a>
        </p>
      </section>
    </main>
  );
}