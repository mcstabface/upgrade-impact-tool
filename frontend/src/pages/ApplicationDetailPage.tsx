import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";
import {
  getAnalysisApplicationDetail,
  type AnalysisApplicationDetailResponse,
} from "../services/analyses";

export default function ApplicationDetailPage() {
  const { id, applicationId } = useParams();
  const [data, setData] = useState<AnalysisApplicationDetailResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id || !applicationId) return;
    getAnalysisApplicationDetail(id, applicationId)
      .then(setData)
      .catch((err: Error) => setError(err.message));
  }, [id, applicationId]);

  if (error) return <ErrorState message={error} />;
  if (!data) return <LoadingState />;

  return (
    <main style={{ padding: "2rem", fontFamily: "sans-serif" }}>
      <p>
        <Link to={`/analyses/${id}`}>Back to Analysis Overview</Link>
      </p>

      <h1>{data.application_name}</h1>
      <p>Status: {data.application_status}</p>

      <h2>Findings</h2>
      <ul>
        {data.findings.map((finding) => (
          <li key={finding.finding_id}>
            <Link to={`/findings/${finding.finding_id}?analysisId=${id}&applicationId=${applicationId}`}>
              {finding.headline}
            </Link>
            {" — "}
            {finding.status}
          </li>
        ))}
      </ul>
    </main>
  );
}