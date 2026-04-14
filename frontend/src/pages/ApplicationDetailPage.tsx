import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";
import StatusHelp from "../components/StatusHelp";
import {
  getAnalysisApplicationDetail,
  type AnalysisApplicationDetailResponse,
} from "../services/analyses";

export default function ApplicationDetailPage() {
  const { id, applicationId } = useParams();
  const [data, setData] = useState<AnalysisApplicationDetailResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [statusFilter, setStatusFilter] = useState("ALL");
  const [searchText, setSearchText] = useState("");

  useEffect(() => {
    if (!id || !applicationId) return;
    getAnalysisApplicationDetail(id, applicationId)
      .then(setData)
      .catch((err: Error) => setError(err.message));
  }, [id, applicationId]);

  const filteredFindings = useMemo(() => {
    if (!data) return [];

    return data.findings.filter((finding) => {
      const statusMatches =
        statusFilter === "ALL" ? true : finding.status === statusFilter;

      const search = searchText.trim().toLowerCase();
      const searchMatches =
        search.length === 0
          ? true
          : finding.headline.toLowerCase().includes(search) ||
            finding.change_taxonomy.toLowerCase().includes(search) ||
            finding.kb_reference.toLowerCase().includes(search);

      return statusMatches && searchMatches;
    });
  }, [data, statusFilter, searchText]);

  if (error) return <ErrorState message={error} />;
  if (!data) return <LoadingState />;

  return (
    <main style={{ padding: "2rem", fontFamily: "sans-serif", maxWidth: "56rem" }}>
      <p>
        <Link to={`/analyses/${id}`}>Back to Analysis Overview</Link>
      </p>

      <h1>{data.application_name}</h1>
      <p>Status: {data.application_status}</p>
      <StatusHelp status={data.application_status} />

      <h2>Filters</h2>
      <div style={{ marginBottom: "1rem" }}>
        <label>Status </label>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="ALL">ALL</option>
          <option value="BLOCKED">BLOCKED</option>
          <option value="REQUIRES_REVIEW">REQUIRES_REVIEW</option>
          <option value="UNKNOWN">UNKNOWN</option>
          <option value="APPLIES">APPLIES</option>
          <option value="RESOLVED">RESOLVED</option>
        </select>
      </div>

      <div style={{ marginBottom: "1rem" }}>
        <label>Search </label>
        <input
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          placeholder="Search headline, taxonomy, or KB"
        />
      </div>

      <h2>Findings</h2>

      {filteredFindings.length === 0 ? (
        <p>No findings match the current filters.</p>
      ) : (
        <ul>
          {filteredFindings.map((finding) => (
            <li key={finding.finding_id} style={{ marginBottom: "1rem" }}>
              <div>
                <Link
                  to={`/findings/${finding.finding_id}?analysisId=${id}&applicationId=${applicationId}`}
                >
                  {finding.headline}
                </Link>
              </div>
              <div>Status: {finding.status}</div>
              <div>Severity: {finding.severity}</div>
              <div>Change Type: {finding.change_taxonomy}</div>
              <div>Source KB: {finding.kb_reference}</div>
              {finding.recommended_action && (
                <div>Recommended Action: {finding.recommended_action}</div>
              )}
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}