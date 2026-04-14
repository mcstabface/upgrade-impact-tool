import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";

import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";
import StatusHelp from "../components/StatusHelp";
import {
  getFindingDetail,
  resolveFinding,
  type FindingDetailResponse,
} from "../services/findings";

export default function FindingDetailPage() {
  const { id } = useParams();
  const [searchParams] = useSearchParams();

  const [data, setData] = useState<FindingDetailResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [resolutionNote, setResolutionNote] = useState(
    "Reviewed manually; no further action required for current scope.",
  );
  const [resolving, setResolving] = useState(false);
  const [resolveMessage, setResolveMessage] = useState<string | null>(null);

  const analysisId = searchParams.get("analysisId");
  const applicationId = searchParams.get("applicationId");

  useEffect(() => {
    if (!id) return;
    getFindingDetail(id).then(setData).catch((err: Error) => setError(err.message));
  }, [id]);

  async function handleResolve(event: React.FormEvent) {
    event.preventDefault();
    if (!id) return;

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

  if (error) return <ErrorState message={error} />;
  if (!data) return <LoadingState />;

  const canResolve =
    data.status === "UNKNOWN" ||
    data.status === "REQUIRES_REVIEW" ||
    data.status === "BLOCKED";

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
      <p>Status: {data.status}</p>
      <StatusHelp status={data.status} />
      <p>Severity: {data.severity}</p>
      <p>Taxonomy: {data.change_taxonomy}</p>
      <p>Application: {data.application_name}</p>
      <p>Module: {data.module_name ?? "N/A"}</p>
      <p>
        Version Range: {data.version_range.from_version ?? "N/A"} →{" "}
        {data.version_range.to_version ?? "N/A"}
      </p>

      <h2>What Changed</h2>
      <p>{data.plain_language_summary}</p>

      {data.business_impact_summary && (
        <>
          <h2>Why It Matters</h2>
          <p>{data.business_impact_summary}</p>
        </>
      )}

      {data.technical_impact_summary && (
        <>
          <h2>Technical Impact</h2>
          <p>{data.technical_impact_summary}</p>
        </>
      )}

      {data.recommended_action && (
        <>
          <h2>Recommended Action</h2>
          <p>{data.recommended_action}</p>
        </>
      )}

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

      {canResolve && (
        <>
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
        </>
      )}

      {resolveMessage && <p>{resolveMessage}</p>}

      <h2>Source Evidence</h2>
      <p>KB Article: {data.evidence.kb_article_number}</p>
      <p>Title: {data.evidence.kb_title}</p>
      <p>Published: {data.evidence.publication_date}</p>
      <p>Excerpt: {data.evidence.evidence_excerpt}</p>
      {data.evidence.reference_section && <p>Reference Section: {data.evidence.reference_section}</p>}
      <a href={data.evidence.kb_url} target="_blank" rel="noreferrer">
        Open Source Link
      </a>
    </main>
  );
}