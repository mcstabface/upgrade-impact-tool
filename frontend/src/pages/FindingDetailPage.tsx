import { useEffect, useState } from "react";
import { Link, useSearchParams, useParams } from "react-router-dom";

import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";
import { getFindingDetail, type FindingDetailResponse } from "../services/findings";

export default function FindingDetailPage() {
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const [data, setData] = useState<FindingDetailResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const analysisId = searchParams.get("analysisId");
  const applicationId = searchParams.get("applicationId");

  useEffect(() => {
    if (!id) return;
    getFindingDetail(id).then(setData).catch((err: Error) => setError(err.message));
  }, [id]);

  if (error) return <ErrorState message={error} />;
  if (!data) return <LoadingState />;

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
      <p>Severity: {data.severity}</p>
      <p>Application: {data.application_name}</p>
      <p>Module: {data.module_name ?? "N/A"}</p>

      {data.status === "UNKNOWN" && (
        <p>This finding requires follow-up because customer context is incomplete.</p>
      )}

      <h2>Summary</h2>
      <p>{data.plain_language_summary}</p>

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