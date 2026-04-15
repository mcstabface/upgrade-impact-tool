import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";
import EmptyState from "../components/EmptyState";
import { formatStatusLabel } from "../utils/status";
import { getReviewQueue, type ReviewQueueResponse } from "../services/reviewQueue";

function statusPriority(status: string): number {
  switch (status) {
    case "OPEN":
      return 1;
    case "IN_PROGRESS":
      return 2;
    case "DEFERRED":
      return 3;
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
  const [ownerFilter, setOwnerFilter] = useState("");
  const [searchText, setSearchText] = useState("");

  useEffect(() => {
    getReviewQueue().then(setData).catch((err: Error) => setError(err.message));
  }, []);

  const filteredItems = useMemo(() => {
    if (!data) return [];

    const filtered = data.items.filter((item) => {
      const statusMatches = statusFilter === "ALL" ? true : item.review_status === statusFilter;

      const ownerSearch = ownerFilter.trim().toLowerCase();
      const ownerMatches =
        ownerSearch.length === 0
          ? true
          : item.assigned_owner_user_id.toLowerCase().includes(ownerSearch);

      const search = searchText.trim().toLowerCase();
      const searchMatches =
        search.length === 0
          ? true
          : item.finding_headline.toLowerCase().includes(search) ||
            item.application_name.toLowerCase().includes(search) ||
            item.analysis_id.toLowerCase().includes(search) ||
            item.kb_reference.toLowerCase().includes(search) ||
            item.review_reason.toLowerCase().includes(search);

      return statusMatches && ownerMatches && searchMatches;
    });

    return [...filtered].sort((a, b) => {
      const statusDiff = statusPriority(a.review_status) - statusPriority(b.review_status);
      if (statusDiff !== 0) return statusDiff;

      const dueDateDiff = a.due_date.localeCompare(b.due_date);
      if (dueDateDiff !== 0) return dueDateDiff;

      return b.review_item_id - a.review_item_id;
    });
  }, [data, statusFilter, ownerFilter, searchText]);

  function clearFilters() {
    setStatusFilter("ALL");
    setOwnerFilter("");
    setSearchText("");
  }

  if (error) {
    return <ErrorState title="Could not load review queue" message={error} />;
  }

  if (!data) {
    return <LoadingState message="Loading review items..." />;
  }

  if (data.items.length === 0) {
    return (
      <EmptyState
        title="Review queue is clear"
        message="There are no open, in-progress, or deferred review items right now."
      />
    );
  }

  return (
    <main style={{ padding: "2rem", fontFamily: "sans-serif", maxWidth: "72rem" }}>
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
            <option value="OPEN">OPEN</option>
            <option value="IN_PROGRESS">IN_PROGRESS</option>
            <option value="DEFERRED">DEFERRED</option>
          </select>
        </div>

        <div style={{ marginBottom: "1rem" }}>
          <label>Owner </label>
          <input
            value={ownerFilter}
            onChange={(e) => setOwnerFilter(e.target.value)}
            placeholder="Filter by owner"
          />
        </div>

        <div style={{ marginBottom: "1rem" }}>
          <label>Search </label>
          <input
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            placeholder="Search headline, app, analysis, KB, or reason"
          />
        </div>

        <button type="button" onClick={clearFilters}>
          Clear Filters
        </button>
      </section>

      {(statusFilter !== "ALL" || ownerFilter.trim().length > 0 || searchText.trim().length > 0) && (
        <section style={{ marginBottom: "2rem" }}>
          <h2>Active Filters</h2>

          <div>
            {statusFilter !== "ALL" && (
              <FilterChip
                label={`Status: ${formatStatusLabel(statusFilter)}`}
                onClear={() => setStatusFilter("ALL")}
              />
            )}

            {ownerFilter.trim().length > 0 && (
              <FilterChip
                label={`Owner: ${ownerFilter}`}
                onClear={() => setOwnerFilter("")}
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
            <li key={item.review_item_id} style={{ marginBottom: "1.5rem" }}>
              <div>
                <strong>Review Item {item.review_item_id}</strong>
                {" — "}
                <Link to={`/findings/${item.finding_id}`}>{item.finding_headline}</Link>
              </div>
              <div>Status: {formatStatusLabel(item.review_status)}</div>
              <div>Owner: {item.assigned_owner_user_id}</div>
              <div>Due Date: {item.due_date}</div>
              <div>Application: {item.application_name}</div>
              <div>Analysis: {item.analysis_id}</div>
              <div>KB: {item.kb_reference}</div>
              <div>Reason: {item.review_reason}</div>
              {item.defer_reason && <div>Deferred Because: {item.defer_reason}</div>}
              {item.resolution_note && <div>Resolution Note: {item.resolution_note}</div>}
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}