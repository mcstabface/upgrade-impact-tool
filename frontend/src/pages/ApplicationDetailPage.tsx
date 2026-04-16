import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";
import EmptyState from "../components/EmptyState";
import StatusHelp from "../components/StatusHelp";
import StatusBanner from "../components/StatusBanner";
import { formatStatusLabel } from "../utils/status";
import {
  getAnalysisApplicationDetail,
  getAnalysisApplicationExportJsonUrl,
  type AnalysisApplicationDetailResponse,
} from "../services/analyses";

function statusPriority(status: string): number {
  switch (status) {
    case "BLOCKED":
      return 1;
    case "REQUIRES_REVIEW":
      return 2;
    case "UNKNOWN":
      return 3;
    case "APPLIES":
      return 4;
    case "RESOLVED":
      return 5;
    default:
      return 99;
  }
}

function severityPriority(severity: string): number {
  switch (severity) {
    case "CRITICAL":
      return 1;
    case "HIGH":
      return 2;
    case "MEDIUM":
      return 3;
    case "LOW":
      return 4;
    default:
      return 99;
  }
}

function FilterChip({
  label,
  onClear,
}: {
  label: string;
  onClear: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClear}
      style={{
        marginRight: "0.5rem",
        marginBottom: "0.5rem",
      }}
    >
      {label} ×
    </button>
  );
}

export default function ApplicationDetailPage() {
  const { id, applicationId } = useParams();
  const [data, setData] = useState<AnalysisApplicationDetailResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [statusFilter, setStatusFilter] = useState("ALL");
  const [severityFilter, setSeverityFilter] = useState("ALL");
  const [searchText, setSearchText] = useState("");

  const loadApplicationDetail = useCallback(async () => {
    if (!id || !applicationId) return;

    setError(null);

    try {
      const result = await getAnalysisApplicationDetail(id, applicationId);
      setData(result);
    } catch (err) {
      setError((err as Error).message);
    }
  }, [id, applicationId]);

  useEffect(() => {
    loadApplicationDetail();
  }, [loadApplicationDetail]);

  const filteredFindings = useMemo(() => {
    if (!data) return [];

    const filtered = data.findings.filter((finding) => {
      const statusMatches = statusFilter === "ALL" ? true : finding.status === statusFilter;
      const severityMatches = severityFilter === "ALL" ? true : finding.severity === severityFilter;

      const search = searchText.trim().toLowerCase();
      const searchMatches =
        search.length === 0
          ? true
          : finding.headline.toLowerCase().includes(search) ||
            finding.change_taxonomy.toLowerCase().includes(search) ||
            finding.kb_reference.toLowerCase().includes(search) ||
            (finding.recommended_action ?? "").toLowerCase().includes(search);

      return statusMatches && severityMatches && searchMatches;
    });

    return [...filtered].sort((a, b) => {
      const statusDiff = statusPriority(a.status) - statusPriority(b.status);
      if (statusDiff !== 0) return statusDiff;

      const severityDiff = severityPriority(a.severity) - severityPriority(b.severity);
      if (severityDiff !== 0) return severityDiff;

      return a.headline.localeCompare(b.headline);
    });
  }, [data, statusFilter, severityFilter, searchText]);

  function clearFilters() {
    setStatusFilter("ALL");
    setSeverityFilter("ALL");
    setSearchText("");
  }

  if (error) {
    return (
      <ErrorState
        title="Could not load application detail"
        message={error}
        onRetry={loadApplicationDetail}
        retryLabel="Retry Load"
      />
    );
  }

  if (!data) {
    return <LoadingState message="Loading application findings..." />;
  }

  return (
    <main style={{ padding: "2rem", fontFamily: "sans-serif", maxWidth: "64rem" }}>
      <p>
        <Link to={`/analyses/${id}`}>Back to Analysis Overview</Link>
      </p>

      {id && applicationId && (
        <>
          <p>
            <a href={getAnalysisApplicationExportJsonUrl(id, applicationId)}>
              Export Application JSON
            </a>
          </p>
          <p>
            <Link to={`/analyses/${id}/applications/${applicationId}/report`}>
              Open Printable Application Report
            </Link>
          </p>
        </>
      )}

      <h1>{data.application_name}</h1>
      <p>Status: {formatStatusLabel(data.application_status)}</p>
      <StatusHelp status={data.application_status} />
      <StatusBanner status={data.application_status} />
      <p>
        Current Version: {data.current_version} | Target Version: {data.target_version}
      </p>

      <section style={{ marginBottom: "2rem" }}>
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
          <label>Severity </label>
          <select value={severityFilter} onChange={(e) => setSeverityFilter(e.target.value)}>
            <option value="ALL">ALL</option>
            <option value="CRITICAL">CRITICAL</option>
            <option value="HIGH">HIGH</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="LOW">LOW</option>
          </select>
        </div>

        <div style={{ marginBottom: "1rem" }}>
          <label>Search </label>
          <input
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            placeholder="Search headline, taxonomy, KB, or action"
          />
        </div>

        <button type="button" onClick={clearFilters}>
          Clear Filters
        </button>
      </section>

      {(statusFilter !== "ALL" || severityFilter !== "ALL" || searchText.trim().length > 0) && (
        <section style={{ marginBottom: "2rem" }}>
          <h2>Active Filters</h2>

          <div>
            {statusFilter !== "ALL" && (
              <FilterChip
                label={`Status: ${formatStatusLabel(statusFilter)}`}
                onClear={() => setStatusFilter("ALL")}
              />
            )}

            {severityFilter !== "ALL" && (
              <FilterChip
                label={`Severity: ${severityFilter}`}
                onClear={() => setSeverityFilter("ALL")}
              />
            )}

            {searchText.trim().length > 0 && (
              <FilterChip
                label={`Search: ${searchText}`}
                onClear={() => setSearchText("")}
              />
            )}
          </div>
        </section>
      )}

      <section>
        <h2>Findings</h2>

        {filteredFindings.length === 0 ? (
          <EmptyState
            title="No matching findings"
            message="No findings match the current filters. Clear or adjust the filters to see more results."
          />
        ) : (
          filteredFindings.map((finding) => (
            <article
              key={finding.finding_id}
              style={{
                border: "1px solid #ccc",
                padding: "1rem",
                marginBottom: "1rem",
              }}
            >
              <h3 style={{ marginTop: 0 }}>
                <Link
                  to={`/findings/${finding.finding_id}?analysisId=${id}&applicationId=${applicationId}`}
                >
                  {finding.headline}
                </Link>
              </h3>

              <p>Status: {formatStatusLabel(finding.status)}</p>
              <StatusBanner status={finding.status} />
              <p>Severity: {finding.severity}</p>
              <p>Change Type: {finding.change_taxonomy}</p>
              <p>Source KB: {finding.kb_reference}</p>

              {finding.recommended_action && (
                <p>Recommended Action: {finding.recommended_action}</p>
              )}
            </article>
          ))
        )}
      </section>
    </main>
  );
}