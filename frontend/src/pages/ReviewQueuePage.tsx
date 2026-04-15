import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";
import EmptyState from "../components/EmptyState";
import { formatStatusLabel } from "../utils/status";
import { getReviewQueue, type ReviewQueueResponse } from "../services/reviewQueue";
import { updateReviewItem } from "../services/reviewItems";
import { createReviewComment, getReviewComments } from "../services/reviewComments";

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

  const [workingItemId, setWorkingItemId] = useState<number | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const [resolutionNotes, setResolutionNotes] = useState<Record<number, string>>({});
  const [deferReasons, setDeferReasons] = useState<Record<number, string>>({});

  const [ownerEdits, setOwnerEdits] = useState<Record<number, string>>({});
  const [dueDateEdits, setDueDateEdits] = useState<Record<number, string>>({});

  const [commentsByItem, setCommentsByItem] = useState<Record<number, { comment_id: number; review_item_id: number; comment_text: string; created_by_user_id: string; created_utc: number }[]>>({});
  const [commentDrafts, setCommentDrafts] = useState<Record<number, string>>({});
  const [commentAuthors, setCommentAuthors] = useState<Record<number, string>>({});

  const [showOverdueOnly, setShowOverdueOnly] = useState(false);

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

      const overdueMatches = showOverdueOnly ? item.is_overdue : true;

      return statusMatches && ownerMatches && searchMatches && overdueMatches;
    });

    return [...filtered].sort((a, b) => {
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

  async function handleLoadComments(reviewItemId: number) {
    setError(null);

    try {
      const result = await getReviewComments(reviewItemId);
      setCommentsByItem((current) => ({
        ...current,
        [reviewItemId]: result.items,
      }));
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function handleAddComment(reviewItemId: number) {
    const commentText = (commentDrafts[reviewItemId] ?? "").trim();
    const createdByUserId = (commentAuthors[reviewItemId] ?? "").trim();

    if (!commentText) {
      setError("Comment text is required.");
      return;
    }

    if (!createdByUserId) {
      setError("Comment author is required.");
      return;
    }

    setWorkingItemId(reviewItemId);
    setError(null);
    setMessage(null);

    try {
      const created = await createReviewComment(reviewItemId, {
        comment_text: commentText,
        created_by_user_id: createdByUserId,
      });

      setCommentsByItem((current) => ({
        ...current,
        [reviewItemId]: [...(current[reviewItemId] ?? []), created],
      }));

      setCommentDrafts((current) => ({
        ...current,
        [reviewItemId]: "",
      }));

      setMessage(`Comment added to review item ${reviewItemId}.`);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setWorkingItemId(null);
    }
  }

  async function handleSaveAssignment(reviewItemId: number) {
    const item = data?.items.find((entry) => entry.review_item_id === reviewItemId);
    if (!item) return;

    const assignedOwner = (ownerEdits[reviewItemId] ?? item.assigned_owner_user_id).trim();
    const dueDate = (dueDateEdits[reviewItemId] ?? item.due_date).trim();

    if (!assignedOwner) {
      setError("Assigned owner is required.");
      return;
    }

    if (!dueDate) {
      setError("Due date is required.");
      return;
    }

    setWorkingItemId(reviewItemId);
    setError(null);
    setMessage(null);

    try {
      const result = await updateReviewItem(reviewItemId, {
        assigned_owner_user_id: assignedOwner,
        due_date: dueDate,
      });

      setData((current) =>
        current
          ? {
              ...current,
              items: current.items.map((entry) =>
                entry.review_item_id === reviewItemId
                  ? {
                      ...entry,
                      assigned_owner_user_id: result.assigned_owner_user_id,
                      due_date: result.due_date,
                      updated_utc: result.updated_utc,
                      resolution_note: result.resolution_note,
                      defer_reason: result.defer_reason,
                    }
                  : entry,
              ),
            }
          : current,
      );

      setMessage(`Review item ${reviewItemId} assignment updated.`);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setWorkingItemId(null);
    }
  }

  async function handleStart(reviewItemId: number) {
    setWorkingItemId(reviewItemId);
    setError(null);
    setMessage(null);

    try {
      const result = await updateReviewItem(reviewItemId, {
        review_status: "IN_PROGRESS",
      });

      setData((current) =>
        current
          ? {
              ...current,
              items: current.items.map((item) =>
                item.review_item_id === reviewItemId
                  ? {
                      ...item,
                      review_status: result.review_status,
                      updated_utc: result.updated_utc,
                      resolution_note: result.resolution_note,
                      defer_reason: result.defer_reason,
                    }
                  : item,
              ),
            }
          : current,
      );

      setMessage(`Review item ${reviewItemId} moved to IN_PROGRESS.`);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setWorkingItemId(null);
    }
  }

  async function handleDefer(reviewItemId: number) {
    const deferReason = (deferReasons[reviewItemId] ?? "").trim();
    if (!deferReason) {
      setError("Defer reason is required.");
      return;
    }

    setWorkingItemId(reviewItemId);
    setError(null);
    setMessage(null);

    try {
      const result = await updateReviewItem(reviewItemId, {
        review_status: "DEFERRED",
        defer_reason: deferReason,
      });

      setData((current) =>
        current
          ? {
              ...current,
              items: current.items.map((item) =>
                item.review_item_id === reviewItemId
                  ? {
                      ...item,
                      review_status: result.review_status,
                      updated_utc: result.updated_utc,
                      resolution_note: result.resolution_note,
                      defer_reason: result.defer_reason,
                    }
                  : item,
              ),
            }
          : current,
      );

      setMessage(`Review item ${reviewItemId} deferred.`);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setWorkingItemId(null);
    }
  }

  async function handleResolve(reviewItemId: number) {
    const resolutionNote = (resolutionNotes[reviewItemId] ?? "").trim();
    if (!resolutionNote) {
      setError("Resolution note is required.");
      return;
    }

    setWorkingItemId(reviewItemId);
    setError(null);
    setMessage(null);

    try {
      const result = await updateReviewItem(reviewItemId, {
        review_status: "RESOLVED",
        resolution_note: resolutionNote,
      });

      setData((current) =>
        current
          ? {
              ...current,
              items: current.items.filter((item) => item.review_item_id !== reviewItemId),
            }
          : current,
      );

      setMessage(`Review item ${reviewItemId} resolved.`);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setWorkingItemId(null);
    }
  }

  if (error) {
    return <ErrorState title="Could not load review queue" message={error} />;
  }

  if (!data) {
    return <LoadingState message="Loading review items..." />;
  }

  return (
    <main style={{ padding: "2rem", fontFamily: "sans-serif", maxWidth: "72rem" }}>
      <h1>Review Queue</h1>

      <p>
        <Link to="/dashboard">Back to Dashboard</Link>
      </p>

      {message && <p>{message}</p>}

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
          <label>
            <input
              type="checkbox"
              checked={showOverdueOnly}
              onChange={(e) => setShowOverdueOnly(e.target.checked)}
            />{" "}
            Show overdue only
          </label>
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

            {showOverdueOnly && (
              <FilterChip
                label="Overdue Only"
                onClear={() => setShowOverdueOnly(false)}
              />
            )}
          </div>
        </section>
      )}

      {filteredItems.length === 0 ? (
        <EmptyState
          title="Review queue is clear"
          message="There are no open, in-progress, or deferred review items right now."
        />
      ) : (
        <ul>
          {filteredItems.map((item) => (
            <li
              key={item.review_item_id}
              style={{
                marginBottom: "2rem",
                border: item.is_overdue ? "1px solid #ccc" : undefined,
                padding: item.is_overdue ? "0.75rem" : undefined,
              }}
            >
              <div>
                <strong>Review Item {item.review_item_id}</strong>
                {" — "}
                <Link to={`/review-items/${item.review_item_id}`}>{item.finding_headline}</Link>
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

              <div style={{ marginTop: "1rem", marginBottom: "1rem" }}>
                <div style={{ marginBottom: "0.75rem" }}>
                  <label>Owner </label>
                  <input
                    value={ownerEdits[item.review_item_id] ?? item.assigned_owner_user_id}
                    onChange={(e) =>
                      setOwnerEdits((current) => ({
                        ...current,
                        [item.review_item_id]: e.target.value,
                      }))
                    }
                    style={{ width: "20rem", maxWidth: "100%" }}
                  />
                </div>

                <div style={{ marginBottom: "0.75rem" }}>
                  <label>Due Date </label>
                  <input
                    type="date"
                    value={dueDateEdits[item.review_item_id] ?? item.due_date}
                    onChange={(e) =>
                      setDueDateEdits((current) => ({
                        ...current,
                        [item.review_item_id]: e.target.value,
                      }))
                    }
                  />
                </div>

        <button
          type="button"
          onClick={() => handleSaveAssignment(item.review_item_id)}
          disabled={workingItemId === item.review_item_id}
        >
          Save Assignment
        </button>
      </div>

      <div style={{ marginTop: "1rem" }}>
        {item.review_status === "OPEN" && (
          <button
            type="button"
            onClick={() => handleStart(item.review_item_id)}
            disabled={workingItemId === item.review_item_id}
          >
            Start Work
          </button>
        )}

        {item.review_status === "DEFERRED" && (
          <button
            type="button"
            onClick={() => handleStart(item.review_item_id)}
            disabled={workingItemId === item.review_item_id}
          >
            Resume Work
          </button>
        )}
      </div>

              {item.review_status === "IN_PROGRESS" && (
                <div style={{ marginTop: "1rem" }}>
                  <div style={{ marginBottom: "0.75rem" }}>
                    <label>Resolution Note </label>
                    <input
                      value={resolutionNotes[item.review_item_id] ?? ""}
                      onChange={(e) =>
                        setResolutionNotes((current) => ({
                          ...current,
                          [item.review_item_id]: e.target.value,
                        }))
                      }
                      style={{ width: "32rem", maxWidth: "100%" }}
                    />
                    <button
                      type="button"
                      onClick={() => handleResolve(item.review_item_id)}
                      disabled={workingItemId === item.review_item_id}
                      style={{ marginLeft: "0.5rem" }}
                    >
                      Resolve
                    </button>
                  </div>

                  <div>
                    <label>Defer Reason </label>
                    <input
                      value={deferReasons[item.review_item_id] ?? ""}
                      onChange={(e) =>
                        setDeferReasons((current) => ({
                          ...current,
                          [item.review_item_id]: e.target.value,
                        }))
                      }
                      style={{ width: "32rem", maxWidth: "100%" }}
                    />
                    <button
                      type="button"
                      onClick={() => handleDefer(item.review_item_id)}
                      disabled={workingItemId === item.review_item_id}
                      style={{ marginLeft: "0.5rem" }}
                    >
                      Defer
                    </button>
                  </div>
                </div>
              )}
              <div style={{ marginTop: "1rem" }}>
                <button
                  type="button"
                  onClick={() => handleLoadComments(item.review_item_id)}
                  disabled={workingItemId === item.review_item_id}
                >
                  Load Comments
                </button>
              </div>

              <div style={{ marginTop: "1rem" }}>
                <div style={{ marginBottom: "0.75rem" }}>
                  <label>Comment Author </label>
                  <input
                    value={commentAuthors[item.review_item_id] ?? ""}
                    onChange={(e) =>
                      setCommentAuthors((current) => ({
                        ...current,
                        [item.review_item_id]: e.target.value,
                      }))
                    }
                    placeholder="user_id"
                    style={{ width: "16rem", maxWidth: "100%" }}
                  />
                </div>

                <div style={{ marginBottom: "0.75rem" }}>
                  <label>Comment </label>
                  <input
                    value={commentDrafts[item.review_item_id] ?? ""}
                    onChange={(e) =>
                      setCommentDrafts((current) => ({
                        ...current,
                        [item.review_item_id]: e.target.value,
                      }))
                    }
                    style={{ width: "32rem", maxWidth: "100%" }}
                  />
                  <button
                    type="button"
                    onClick={() => handleAddComment(item.review_item_id)}
                    disabled={workingItemId === item.review_item_id}
                    style={{ marginLeft: "0.5rem" }}
                  >
                    Add Comment
                  </button>
                </div>

                {(commentsByItem[item.review_item_id] ?? []).length > 0 && (
                  <ul>
                    {(commentsByItem[item.review_item_id] ?? []).map((comment) => (
                      <li key={comment.comment_id}>
                        {comment.created_by_user_id}: {comment.comment_text}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}