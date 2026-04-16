import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import AppShell from "../components/layout/AppShell";
import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";
import EmptyState from "../components/EmptyState";
import Card from "../components/ui/Card";
import ButtonLink from "../components/ui/ButtonLink";
import { formatStatusLabel } from "../utils/status";
import {
  getReviewQueue,
  getReviewQueueCsvExportUrl,
  type ReviewQueueResponse,
} from "../services/reviewQueue";

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
    <button type="button" className="ui-chip" onClick={onClear}>
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
  const [showOverdueOnly, setShowOverdueOnly] = useState(false);

  const loadQueue = useCallback(async () => {
    setError(null);
    try {
      const result = await getReviewQueue();
      setData(result);
    } catch (err) {
      setError((err as Error).message);
    }
  }, []);

  useEffect(() => {
    loadQueue();
  }, [loadQueue]);

  const filteredItems = useMemo(() => {
    if (!data) return [];

    const filtered = data.items.filter((item) => {
      const statusMatches =
        statusFilter === "ALL" ? true : item.review_status === statusFilter;

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

      const overdueMatches = showOverdueOnly ? item.is_overdue : true;

      return statusMatches && ownerMatches && searchMatches && overdueMatches;
    });

    return [...filtered].sort((a, b) => {
      if (a.is_overdue !== b.is_overdue) {
        return a.is_overdue ? -1 : 1;
      }

      const statusDiff = statusPriority(a.review_status) - statusPriority(b.review_status);
      if (statusDiff !== 0) return statusDiff;

      const dueDateDiff = a.due_date.localeCompare(b.due_date);
      if (dueDateDiff !== 0) return dueDateDiff;

      return b.review_item_id - a.review_item_id;
    });
  }, [data, statusFilter, ownerFilter, searchText, showOverdueOnly]);

  function clearFilters() {
    setStatusFilter("ALL");
    setOwnerFilter("");
    setSearchText("");
    setShowOverdueOnly(false);
  }

  if (error) {
    return (
      <ErrorState
        title="Could not load review queue"
        message={error}
        onRetry={loadQueue}
        retryLabel="Retry Load"
      />
    );
  }

  if (!data) {
    return <LoadingState message="Loading review items..." />;
  }

  return (
    <AppShell
      title="Review Queue"
      subtitle="Track open review work, overdue items, and owner assignments before pilot issues become somebody else’s archaeology."
      actions={
        <>
          <ButtonLink to="/dashboard" variant="subtle">
            Back to Dashboard
          </ButtonLink>
          <a className="ui-button" href={getReviewQueueCsvExportUrl()}>
            Export Review Queue CSV
          </a>
        </>
      }
    >
      <div className="ui-stack">
        <Card title="Filters" muted>
          <div className="ui-toolbar">
            <div className="ui-toolbar__group">
              <label className="ui-label">Status</label>
              <select
                className="ui-select"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="ALL">ALL</option>
                <option value="OPEN">OPEN</option>
                <option value="IN_PROGRESS">IN_PROGRESS</option>
                <option value="DEFERRED">DEFERRED</option>
              </select>
            </div>

            <div className="ui-toolbar__group">
              <label className="ui-label">Owner</label>
              <input
                className="ui-input"
                value={ownerFilter}
                onChange={(e) => setOwnerFilter(e.target.value)}
                placeholder="Filter by owner"
              />
            </div>

            <div className="ui-toolbar__group" style={{ minWidth: "260px" }}>
              <label className="ui-label">Search</label>
              <input
                className="ui-input"
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                placeholder="Search headline, app, analysis, KB, or reason"
              />
            </div>

            <div className="ui-toolbar__group">
              <label className="ui-label">View</label>
              <label style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                <input
                  type="checkbox"
                  checked={showOverdueOnly}
                  onChange={(e) => setShowOverdueOnly(e.target.checked)}
                />
                <span>Show overdue only</span>
              </label>
            </div>

            <div className="ui-toolbar__group">
              <label className="ui-label">Actions</label>
              <button type="button" className="ui-button" onClick={clearFilters}>
                Clear Filters
              </button>
            </div>
          </div>

          {statusFilter !== "ALL" ||
          ownerFilter.trim().length > 0 ||
          searchText.trim().length > 0 ||
          showOverdueOnly ? (
            <div style={{ marginTop: "1rem" }}>
              <div className="ui-chip-row">
                {statusFilter !== "ALL" ? (
                  <FilterChip
                    label={`Status: ${formatStatusLabel(statusFilter)}`}
                    onClear={() => setStatusFilter("ALL")}
                  />
                ) : null}

                {showOverdueOnly ? (
                  <FilterChip
                    label="Overdue Only"
                    onClear={() => setShowOverdueOnly(false)}
                  />
                ) : null}

                {ownerFilter.trim().length > 0 ? (
                  <FilterChip label={`Owner: ${ownerFilter}`} onClear={() => setOwnerFilter("")} />
                ) : null}

                {searchText.trim().length > 0 ? (
                  <FilterChip
                    label={`Search: ${searchText}`}
                    onClear={() => setSearchText("")}
                  />
                ) : null}
              </div>
            </div>
          ) : null}
        </Card>

        {filteredItems.length === 0 ? (
          <EmptyState
            title="Review queue is clear"
            message="There are no open, in-progress, or deferred review items right now."
          />
        ) : (
          <div className="ui-stack" style={{ gap: "1rem" }}>
            {filteredItems.map((item) => (
              <Card
                key={item.review_item_id}
                tone={item.is_overdue ? "danger" : "default"}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    gap: "1rem",
                    flexWrap: "wrap",
                    alignItems: "start",
                  }}
                >
                  <div>
                    <div style={{ marginBottom: "0.35rem", fontWeight: 700 }}>
                      Review Item {item.review_item_id} —{" "}
                      <Link to={`/review-items/${item.review_item_id}`}>
                        {item.finding_headline}
                      </Link>
                    </div>
                    <div className="ui-status-note">
                      Status: {formatStatusLabel(item.review_status)}
                    </div>
                    <div className="ui-status-note">Owner: {item.assigned_owner_user_id}</div>
                    <div className="ui-status-note">Due Date: {item.due_date}</div>
                    {item.is_overdue ? (
                      <div style={{ color: "var(--danger-text)", fontWeight: 600, marginTop: "0.35rem" }}>
                        Overdue
                      </div>
                    ) : null}
                  </div>

                  <div className="ui-inline-actions">
                    <ButtonLink to={`/review-items/${item.review_item_id}`} variant="subtle">
                      Open Review Item
                    </ButtonLink>
                  </div>
                </div>

                <hr className="ui-divider" style={{ marginTop: "1rem", marginBottom: "1rem" }} />

                <div className="ui-meta-list">
                  <div className="ui-meta-list__row">
                    <span className="ui-meta-list__label">Application</span>
                    <span>{item.application_name}</span>
                  </div>
                  <div className="ui-meta-list__row">
                    <span className="ui-meta-list__label">Analysis</span>
                    <span>{item.analysis_id}</span>
                  </div>
                  <div className="ui-meta-list__row">
                    <span className="ui-meta-list__label">KB</span>
                    <span>{item.kb_reference}</span>
                  </div>
                  <div className="ui-meta-list__row">
                    <span className="ui-meta-list__label">Reason</span>
                    <span>{item.review_reason}</span>
                  </div>
                  {item.defer_reason ? (
                    <div className="ui-meta-list__row">
                      <span className="ui-meta-list__label">Deferred Because</span>
                      <span>{item.defer_reason}</span>
                    </div>
                  ) : null}
                  {item.resolution_note ? (
                    <div className="ui-meta-list__row">
                      <span className="ui-meta-list__label">Resolution Note</span>
                      <span>{item.resolution_note}</span>
                    </div>
                  ) : null}
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}