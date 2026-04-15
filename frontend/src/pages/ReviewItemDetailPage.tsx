import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { formatUnixSeconds } from "../utils/time";
import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";
import EmptyState from "../components/EmptyState";
import { formatStatusLabel } from "../utils/status";
import { getReviewItem, updateReviewItem, type ReviewItemDetailResponse } from "../services/reviewItems";
import { createReviewComment, getReviewComments, type ReviewComment } from "../services/reviewComments";

export default function ReviewItemDetailPage() {
  const { id } = useParams();
  const [data, setData] = useState<ReviewItemDetailResponse | null>(null);
  const [comments, setComments] = useState<ReviewComment[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [working, setWorking] = useState(false);

  const [ownerEdit, setOwnerEdit] = useState("");
  const [dueDateEdit, setDueDateEdit] = useState("");
  const [resolutionNote, setResolutionNote] = useState("");
  const [deferReason, setDeferReason] = useState("");
  const [commentAuthor, setCommentAuthor] = useState("");
  const [commentText, setCommentText] = useState("");

  useEffect(() => {
    if (!id) return;

    const reviewItemId = Number(id);

    Promise.all([
      getReviewItem(reviewItemId),
      getReviewComments(reviewItemId),
    ])
      .then(([item, commentList]) => {
        setData(item);
        setComments(commentList.items);
        setOwnerEdit(item.assigned_owner_user_id);
        setDueDateEdit(item.due_date);
      })
      .catch((err: Error) => setError(err.message));
  }, [id]);

  async function handleSaveAssignment() {
    if (!data) return;

    const assignedOwner = ownerEdit.trim();
    const dueDate = dueDateEdit.trim();

    if (!assignedOwner) {
      setError("Assigned owner is required.");
      return;
    }

    if (!dueDate) {
      setError("Due date is required.");
      return;
    }

    setWorking(true);
    setError(null);
    setMessage(null);

    try {
      const result = await updateReviewItem(data.review_item_id, {
        assigned_owner_user_id: assignedOwner,
        due_date: dueDate,
      });

      setData({
        ...data,
        assigned_owner_user_id: result.assigned_owner_user_id,
        due_date: result.due_date,
        review_status: result.review_status,
        updated_utc: result.updated_utc,
        assignment_updated_utc: result.assignment_updated_utc,
        resolution_note: result.resolution_note,
        defer_reason: result.defer_reason,
      });

      setMessage("Assignment updated.");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setWorking(false);
    }
  }

  async function handleStartOrResume() {
    if (!data) return;

    setWorking(true);
    setError(null);
    setMessage(null);

    try {
      const result = await updateReviewItem(data.review_item_id, {
        review_status: "IN_PROGRESS",
      });

      setData({
        ...data,
        review_status: result.review_status,
        updated_utc: result.updated_utc,
        resolution_note: result.resolution_note,
        defer_reason: result.defer_reason,
      });

      setMessage(`Review item moved to ${result.review_status}.`);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setWorking(false);
    }
  }

  async function handleDefer() {
    if (!data) return;

    const trimmedReason = deferReason.trim();
    if (!trimmedReason) {
      setError("Defer reason is required.");
      return;
    }

    setWorking(true);
    setError(null);
    setMessage(null);

    try {
      const result = await updateReviewItem(data.review_item_id, {
        review_status: "DEFERRED",
        defer_reason: trimmedReason,
      });

      setData({
        ...data,
        review_status: result.review_status,
        updated_utc: result.updated_utc,
        resolution_note: result.resolution_note,
        defer_reason: result.defer_reason,
      });

      setMessage("Review item deferred.");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setWorking(false);
    }
  }

  async function handleResolve() {
    if (!data) return;

    const trimmedNote = resolutionNote.trim();
    if (!trimmedNote) {
      setError("Resolution note is required.");
      return;
    }

    setWorking(true);
    setError(null);
    setMessage(null);

    try {
      const result = await updateReviewItem(data.review_item_id, {
        review_status: "RESOLVED",
        resolution_note: trimmedNote,
      });

      setData({
        ...data,
        review_status: result.review_status,
        updated_utc: result.updated_utc,
        resolution_note: result.resolution_note,
        defer_reason: result.defer_reason,
      });

      setMessage("Review item resolved.");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setWorking(false);
    }
  }

  async function handleAddComment() {
    if (!data) return;

    const trimmedAuthor = commentAuthor.trim();
    const trimmedText = commentText.trim();

    if (!trimmedAuthor) {
      setError("Comment author is required.");
      return;
    }

    if (!trimmedText) {
      setError("Comment text is required.");
      return;
    }

    setWorking(true);
    setError(null);
    setMessage(null);

    try {
      const created = await createReviewComment(data.review_item_id, {
        created_by_user_id: trimmedAuthor,
        comment_text: trimmedText,
      });

      setComments((current) => [...current, created]);
      setCommentText("");
      setMessage("Comment added.");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setWorking(false);
    }
  }

  if (error) {
    return <ErrorState title="Could not load review item" message={error} />;
  }

  if (!data) {
    return <LoadingState message="Loading review item..." />;
  }

  return (
    <main style={{ padding: "2rem", fontFamily: "sans-serif", maxWidth: "72rem" }}>
      <h1>Review Item {data.review_item_id}</h1>

      <p>
        <Link to="/review-queue">Back to Review Queue</Link>
      </p>

      {message && <p>{message}</p>}

      <section style={{ marginBottom: "2rem" }}>
        <h2>Overview</h2>
        <div>Status: {formatStatusLabel(data.review_status)}</div>
        <div>Owner: {data.assigned_owner_user_id}</div>
        <div>Created: {formatUnixSeconds(data.created_utc)}</div>
        <div>Due Date: {data.due_date}</div>
        <div>Last Updated: {formatUnixSeconds(data.updated_utc)}</div>
        {data.assignment_updated_utc && (
          <div>Assignment Updated: {formatUnixSeconds(data.assignment_updated_utc)}</div>
        )}
        <div>Application: {data.application_name}</div>
        <div>Analysis: {data.analysis_id}</div>
        <div>Finding: <Link to={`/findings/${data.finding_id}`}>{data.finding_headline}</Link></div>
        <div>KB: {data.kb_reference}</div>
        <div>Reason: {data.review_reason}</div>
        {data.defer_reason && <div>Deferred Because: {data.defer_reason}</div>}
        {data.resolution_note && <div>Resolution Note: {data.resolution_note}</div>}
      </section>

      <section style={{ marginBottom: "2rem" }}>
        <h2>Assignment</h2>
        <div style={{ marginBottom: "0.75rem" }}>
          <label>Owner </label>
          <input value={ownerEdit} onChange={(e) => setOwnerEdit(e.target.value)} />
        </div>
        <div style={{ marginBottom: "0.75rem" }}>
          <label>Due Date </label>
          <input type="date" value={dueDateEdit} onChange={(e) => setDueDateEdit(e.target.value)} />
        </div>
        <button type="button" onClick={handleSaveAssignment} disabled={working}>
          Save Assignment
        </button>
      </section>

      <section style={{ marginBottom: "2rem" }}>
        <h2>Workflow</h2>

        {(data.review_status === "OPEN" || data.review_status === "DEFERRED") && (
          <div style={{ marginBottom: "1rem" }}>
            <button type="button" onClick={handleStartOrResume} disabled={working}>
              {data.review_status === "OPEN" ? "Start Work" : "Resume Work"}
            </button>
          </div>
        )}

        {data.review_status === "IN_PROGRESS" && (
          <>
            <div style={{ marginBottom: "1rem" }}>
              <label>Resolution Note </label>
              <input
                value={resolutionNote}
                onChange={(e) => setResolutionNote(e.target.value)}
                style={{ width: "32rem", maxWidth: "100%" }}
              />
              <button
                type="button"
                onClick={handleResolve}
                disabled={working}
                style={{ marginLeft: "0.5rem" }}
              >
                Resolve
              </button>
            </div>

            <div>
              <label>Defer Reason </label>
              <input
                value={deferReason}
                onChange={(e) => setDeferReason(e.target.value)}
                style={{ width: "32rem", maxWidth: "100%" }}
              />
              <button
                type="button"
                onClick={handleDefer}
                disabled={working}
                style={{ marginLeft: "0.5rem" }}
              >
                Defer
              </button>
            </div>
          </>
        )}

        {data.review_status === "RESOLVED" && (
          <EmptyState
            title="Review item resolved"
            message="This item has been completed. You can still review its details and comment history here."
          />
        )}
      </section>

      <section>
        <h2>Comments</h2>

        <div style={{ marginBottom: "0.75rem" }}>
          <label>Comment Author </label>
          <input value={commentAuthor} onChange={(e) => setCommentAuthor(e.target.value)} />
        </div>

        <div style={{ marginBottom: "0.75rem" }}>
          <label>Comment </label>
          <input
            value={commentText}
            onChange={(e) => setCommentText(e.target.value)}
            style={{ width: "32rem", maxWidth: "100%" }}
          />
          <button
            type="button"
            onClick={handleAddComment}
            disabled={working}
            style={{ marginLeft: "0.5rem" }}
          >
            Add Comment
          </button>
        </div>

        {comments.length === 0 ? (
          <EmptyState
            title="No comments yet"
            message="Add the first comment to capture context for this review item."
          />
        ) : (
          <ul>
            {comments.map((comment) => (
              <li key={comment.comment_id}>
                {comment.created_by_user_id} ({formatUnixSeconds(comment.created_utc)}): {comment.comment_text}
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}