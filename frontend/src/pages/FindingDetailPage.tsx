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
    <main style={{ padding: "2rem", fontFamily: "sans-serif" }}>
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
      <p>Application: {data.application_name}</p>
      <p>Module: {data.module_name ?? "N/A"}</p>

      {data.reason_for_status && (
        <>
          <h2>Reason for Status</h2>
          <p>{data.reason_for_status}</p>
        </>
      )}

      <h2>Summary</h2>
      <p>{data.plain_language_summary}</p>

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

      <h2>Evidence</h2>
      <p>{data.evidence.kb_article_number}</p>
      <p>{data.evidence.kb_title}</p>
      <p>{data.evidence.evidence_excerpt}</p>
      <a href={data.evidence.kb_url} target="_blank" rel="noreferrer">
        Source Link
      </a>
    </main>
  );
}