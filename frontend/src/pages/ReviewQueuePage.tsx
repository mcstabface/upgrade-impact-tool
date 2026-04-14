import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";
import EmptyState from "../components/EmptyState";
import StatusHelp from "../components/StatusHelp";
import StatusBanner from "../components/StatusBanner";
import { formatStatusLabel } from "../utils/status";
import { getReviewQueue, type ReviewQueueResponse } from "../services/reviewQueue";

function statusPriority(status: string): number {
  switch (status) {
    case "BLOCKED":
      return 1;
    case "REQUIRES_REVIEW":
      return 2;
    case "UNKNOWN":
      return 3;
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
      style={{ marginRight: "0.5rem", marginBottom: "0.5rem" }}
    >
      {label} ×
    </button>
  );
}

export default function ReviewQueuePage() {
  const [data, setData] = useState<ReviewQueueResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [statusFilter, setStatusFilter] = useState("ALL");
  const [severityFilter, setSeverityFilter] = useState("ALL");
  const [searchText, setSearchText] = useState("");

  useEffect(() => {
    getReviewQueue().then(setData).catch((err: Error) => setError(err.message));
  }, []);

  const filteredItems = useMemo(() => {
    if (!data) return [];

    const filtered = data.items.filter((item) => {
      const statusMatches = statusFilter === "ALL" ? true : item.finding_status === statusFilter;
      const severityMatches = severityFilter === "ALL" ? true : item.severity === severityFilter;

      const search = searchText.trim().toLowerCase();
      const searchMatches =
        search.length === 0
          ? true
          : item.headline.toLowerCase().includes(search) ||
            item.application_name.toLowerCase().includes(search) ||
            item.analysis_id.toLowerCase().includes(search) ||
            (item.reason_for_status ?? "").toLowerCase().includes(search);

      return statusMatches && severityMatches && searchMatches;
    });

    return [...filtered].sort((a, b) => {
      const statusDiff = statusPriority(a.finding_status) - statusPriority(b.finding_status);
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
    return <ErrorState title="Could not load review queue" message={error} />;
  }

  if (!data) {
    return <LoadingState message="Loading unresolved review items..." />;
  }

  if (data.items.length === 0) {
    return (
      <EmptyState
        title="Review queue is clear"
        message="There are no unresolved unknown, blocked, or review-required findings right now."
      />
    );
  }

  return (
    <main style={{ padding: "2rem", fontFamily: "sans-serif", maxWidth: "64rem" }}>
      <h1>Review Queue</h1>

      <p>
        <Link to="/dashboard">Back to Dashboard</Link>
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
            placeholder="Search headline, app, analysis, or reason"
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

      {filteredItems.length === 0 ? (
        <EmptyState
          title="No matching review items"
          message="No review items match the current filters. Clear or adjust the filters to see more results."
        />
      ) : (
        <ul>
          {filteredItems.map((item) => (
            <li key={item.finding_id} style={{ marginBottom: "1.5rem" }}>
              <div>
                <Link to={`/findings/${item.finding_id}`}>{item.headline}</Link>
                {" — "}
                {formatStatusLabel(item.finding_status)}
                {" — "}
                {item.application_name}
                {" — "}
                {item.analysis_id}
                {item.reason_for_status ? ` — ${item.reason_for_status}` : ""}
              </div>

              <StatusHelp status={item.finding_status} />
              <StatusBanner status={item.finding_status} />
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}