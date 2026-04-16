import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import AppShell from "../components/layout/AppShell";
import { formatUnixSeconds } from "../utils/time";
import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";
import EmptyState from "../components/EmptyState";
import Card from "../components/ui/Card";
import ButtonLink from "../components/ui/ButtonLink";
import { canManageReviews } from "../auth/role";
import { useCurrentRole } from "../auth/AuthContext";
import { formatStatusLabel } from "../utils/status";
import {
  getReviewItem,
  updateReviewItem,
  type ReviewItemDetailResponse,
} from "../services/reviewItems";
import {
  createReviewComment,
  getReviewComments,
  type ReviewComment,
} from "../services/reviewComments";

function FieldBlock({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div style={{ display: "grid", gap: "0.35rem" }}>
      <label className="ui-label">{label}</label>
      {children}
    </div>
  );
}

export default function ReviewItemDetailPage() {
  const { id } = useParams();
  const currentRole = useCurrentRole();
  const canEditReview = canManageReviews(currentRole);

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
    if (!data || !canEditReview) return;

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
    if (!data || !canEditReview) return;

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
    if (!data || !canEditReview) return;

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
    if (!data || !canEditReview) return;

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
    if (!data || !canEditReview) return;

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
    <AppShell
      title={`Review Item ${data.review_item_id}`}
      subtitle="Inspect review context, update assignment and workflow, and capture reviewer notes without making the page feel like a database punishment screen."
      actions={
        <>
          <ButtonLink to="/review-queue" variant="subtle">
            Back to Review Queue
          </ButtonLink>
          <ButtonLink to={`/findings/${data.finding_id}`} variant="subtle">
            Open Finding
          </ButtonLink>
        </>
      }
    >
      <div className="ui-stack">
        {message ? (
          <Card muted>
            <p style={{ margin: 0 }}>{message}</p>
          </Card>
        ) : null}

        <Card title="Overview">
          <div className="ui-meta-list">
            <div className="ui-meta-list__row">
              <span className="ui-meta-list__label">Status</span>
              <span>{formatStatusLabel(data.review_status)}</span>
            </div>
            <div className="ui-meta-list__row">
              <span className="ui-meta-list__label">Owner</span>
              <span>{data.assigned_owner_user_id}</span>
            </div>
            <div className="ui-meta-list__row">
              <span className="ui-meta-list__label">Created</span>
              <span>{formatUnixSeconds(data.created_utc)}</span>
            </div>
            <div className="ui-meta-list__row">
              <span className="ui-meta-list__label">Due Date</span>
              <span>{data.due_date}</span>
            </div>
            <div className="ui-meta-list__row">
              <span className="ui-meta-list__label">Last Updated</span>
              <span>{formatUnixSeconds(data.updated_utc)}</span>
            </div>
            {data.assignment_updated_utc ? (
              <div className="ui-meta-list__row">
                <span className="ui-meta-list__label">Assignment Updated</span>
                <span>{formatUnixSeconds(data.assignment_updated_utc)}</span>
              </div>
            ) : null}
            <div className="ui-meta-list__row">
              <span className="ui-meta-list__label">Application</span>
              <span>{data.application_name}</span>
            </div>
            <div className="ui-meta-list__row">
              <span className="ui-meta-list__label">Analysis</span>
              <span>{data.analysis_id}</span>
            </div>
            <div className="ui-meta-list__row">
              <span className="ui-meta-list__label">Finding</span>
              <span>
                <Link to={`/findings/${data.finding_id}`}>{data.finding_headline}</Link>
              </span>
            </div>
            <div className="ui-meta-list__row">
              <span className="ui-meta-list__label">KB</span>
              <span>{data.kb_reference}</span>
            </div>
            <div className="ui-meta-list__row">
              <span className="ui-meta-list__label">Reason</span>
              <span>{data.review_reason}</span>
            </div>
            {data.defer_reason ? (
              <div className="ui-meta-list__row">
                <span className="ui-meta-list__label">Deferred Because</span>
                <span>{data.defer_reason}</span>
              </div>
            ) : null}
            {data.resolution_note ? (
              <div className="ui-meta-list__row">
                <span className="ui-meta-list__label">Resolution Note</span>
                <span>{data.resolution_note}</span>
              </div>
            ) : null}
          </div>
        </Card>

        {canEditReview ? (
          <>
            <Card title="Assignment">
              <div className="ui-field-grid">
                <FieldBlock label="Owner">
                  <input
                    className="ui-input"
                    value={ownerEdit}
                    onChange={(e) => setOwnerEdit(e.target.value)}
                  />
                </FieldBlock>

                <FieldBlock label="Due Date">
                  <input
                    className="ui-input"
                    type="date"
                    value={dueDateEdit}
                    onChange={(e) => setDueDateEdit(e.target.value)}
                  />
                </FieldBlock>
              </div>

              <div style={{ marginTop: "1rem" }}>
                <button
                  type="button"
                  className="ui-button ui-button--primary"
                  onClick={handleSaveAssignment}
                  disabled={working}
                >
                  Save Assignment
                </button>
              </div>
            </Card>

            <Card title="Workflow">
              {(data.review_status === "OPEN" || data.review_status === "DEFERRED") ? (
                <div className="ui-inline-actions" style={{ marginBottom: "1rem" }}>
                  <button
                    type="button"
                    className="ui-button ui-button--primary"
                    onClick={handleStartOrResume}
                    disabled={working}
                  >
                    {data.review_status === "OPEN" ? "Start Work" : "Resume Work"}
                  </button>
                </div>
              ) : null}

              {data.review_status === "IN_PROGRESS" ? (
                <div className="ui-stack" style={{ gap: "1rem" }}>
                  <div className="ui-field-grid" style={{ gridTemplateColumns: "1fr" }}>
                    <FieldBlock label="Resolution Note">
                      <input
                        className="ui-input"
                        value={resolutionNote}
                        onChange={(e) => setResolutionNote(e.target.value)}
                      />
                    </FieldBlock>
                  </div>

                  <div className="ui-inline-actions">
                    <button
                      type="button"
                      className="ui-button ui-button--primary"
                      onClick={handleResolve}
                      disabled={working}
                    >
                      Resolve
                    </button>
                  </div>

                  <hr className="ui-divider" />

                  <div className="ui-field-grid" style={{ gridTemplateColumns: "1fr" }}>
                    <FieldBlock label="Defer Reason">
                      <input
                        className="ui-input"
                        value={deferReason}
                        onChange={(e) => setDeferReason(e.target.value)}
                      />
                    </FieldBlock>
                  </div>

                  <div className="ui-inline-actions">
                    <button
                      type="button"
                      className="ui-button"
                      onClick={handleDefer}
                      disabled={working}
                    >
                      Defer
                    </button>
                  </div>
                </div>
              ) : null}

              {data.review_status === "RESOLVED" ? (
                <EmptyState
                  title="Review item resolved"
                  message="This item has been completed. You can still review its details and comment history here."
                />
              ) : null}
            </Card>
          </>
        ) : (
          <Card title="Review Controls" muted>
            <EmptyState
              title="Read-only access"
              message="Reviewer or admin role is required to update assignments, workflow, or comments."
            />
          </Card>
        )}

        <Card title="Comments">
          {canEditReview ? (
            <div className="ui-stack" style={{ gap: "1rem", marginBottom: "1rem" }}>
              <div className="ui-field-grid">
                <FieldBlock label="Comment Author">
                  <input
                    className="ui-input"
                    value={commentAuthor}
                    onChange={(e) => setCommentAuthor(e.target.value)}
                  />
                </FieldBlock>

                <FieldBlock label="Comment">
                  <input
                    className="ui-input"
                    value={commentText}
                    onChange={(e) => setCommentText(e.target.value)}
                  />
                </FieldBlock>
              </div>

              <div className="ui-inline-actions">
                <button
                  type="button"
                  className="ui-button"
                  onClick={handleAddComment}
                  disabled={working}
                >
                  Add Comment
                </button>
              </div>
            </div>
          ) : null}

          {comments.length === 0 ? (
            <EmptyState
              title="No comments yet"
              message="Add the first comment to capture context for this review item."
            />
          ) : (
            <div className="ui-stack" style={{ gap: "1rem" }}>
              {comments.map((comment: ReviewComment) => (
                <article key={comment.comment_id} className="ui-analysis-card">
                  <div style={{ fontWeight: 700, marginBottom: "0.35rem" }}>
                    {comment.created_by_user_id}
                  </div>
                  <div className="ui-status-note" style={{ marginTop: 0 }}>
                    {formatUnixSeconds(comment.created_utc)}
                  </div>
                  <p style={{ marginBottom: 0 }}>{comment.comment_text}</p>
                </article>
              ))}
            </div>
          )}
        </Card>
      </div>
    </AppShell>
  );
}