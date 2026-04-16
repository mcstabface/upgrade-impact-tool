import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import AppShell from "../components/layout/AppShell";
import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";
import EmptyState from "../components/EmptyState";
import NotificationTray from "../components/NotificationTray";
import StatusHelp from "../components/StatusHelp";
import Card from "../components/ui/Card";
import StatCard from "../components/ui/StatCard";
import ButtonLink from "../components/ui/ButtonLink";
import { canManageIntakes, isAdminRole, type UserRole } from "../auth/role";
import { useAuth } from "../auth/AuthContext";
import { formatStatusLabel } from "../utils/status";
import { formatUnixSeconds } from "../utils/time";
import {
  getDashboard,
  type DashboardAnalysisItem,
  type DashboardResponse,
} from "../services/dashboard";
import {
  getNotifications,
  markNotificationRead,
  type NotificationSummaryResponse,
} from "../services/notifications";

function AnalysisCard({ analysis }: { analysis: DashboardAnalysisItem }) {
  return (
    <article className="ui-analysis-card">
      <h3 className="ui-analysis-card__title">
        <Link to={`/analyses/${analysis.analysis_id}`}>
          {analysis.customer_name} — {analysis.environment_name}
        </Link>
      </h3>

      <div className="ui-meta-list">
        <div className="ui-meta-list__row">
          <span className="ui-meta-list__label">Analysis ID</span>
          <span>{analysis.analysis_id}</span>
        </div>
        <div className="ui-meta-list__row">
          <span className="ui-meta-list__label">Status</span>
          <span>{formatStatusLabel(analysis.overall_status)}</span>
        </div>
      </div>

      <StatusHelp status={analysis.overall_status} />

      <p className="ui-analysis-card__summary">
        Applies: {analysis.applies_count} | Review Required: {analysis.review_required_count} | Unknown:{" "}
        {analysis.unknown_count} | Blocked: {analysis.blocked_count}
      </p>
      <p className="ui-analysis-card__summary">
        Applications in Scope: {analysis.applications_count}
      </p>
      <p className="ui-analysis-card__summary">
        Analysis Date: {formatUnixSeconds(analysis.analysis_date)}
      </p>
    </article>
  );
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

export default function DashboardPage() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const [data, setData] = useState<DashboardResponse | null>(null);
  const [notifications, setNotifications] = useState<NotificationSummaryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const currentRole: UserRole = user?.role ?? "VIEWER";

  const [statusFilter, setStatusFilter] = useState("ALL");
  const [showUnresolvedOnly, setShowUnresolvedOnly] = useState(false);

  useEffect(() => {
    setError(null);

    Promise.all([getDashboard(), getNotifications()])
      .then(([dashboardResult, notificationResult]) => {
        setData(dashboardResult);
        setNotifications(notificationResult);
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  const filteredAnalyses = useMemo(() => {
    if (!data) return [];

    return data.analyses.filter((analysis) => {
      const statusMatches =
        statusFilter === "ALL" ? true : analysis.overall_status === statusFilter;

      const unresolvedMatches = showUnresolvedOnly
        ? analysis.overall_status !== "READY"
        : true;

      return statusMatches && unresolvedMatches;
    });
  }, [data, statusFilter, showUnresolvedOnly]);

  const dashboardMetrics = useMemo(() => {
    return filteredAnalyses.reduce(
      (acc, analysis) => {
        acc.totalAnalyses += 1;
        if (analysis.overall_status === "READY") acc.readyAnalyses += 1;
        if (analysis.overall_status === "REVIEW_REQUIRED") acc.reviewRequiredAnalyses += 1;
        if (analysis.overall_status === "ANALYSIS_RUNNING") acc.runningAnalyses += 1;
        if (analysis.overall_status === "STALE") acc.staleAnalyses += 1;
        if (analysis.previous_analysis_id) acc.refreshedAnalyses += 1;
        acc.unknownFindings += analysis.unknown_count;
        acc.blockedFindings += analysis.blocked_count;
        return acc;
      },
      {
        totalAnalyses: 0,
        readyAnalyses: 0,
        reviewRequiredAnalyses: 0,
        runningAnalyses: 0,
        staleAnalyses: 0,
        refreshedAnalyses: 0,
        unknownFindings: 0,
        blockedFindings: 0,
      },
    );
  }, [filteredAnalyses]);

  const latestCompletedAnalysis = useMemo(() => {
    return filteredAnalyses.find((analysis) => analysis.analysis_date !== null) ?? null;
  }, [filteredAnalyses]);

  const activeAnalyses = useMemo(() => {
    return filteredAnalyses.filter(
      (analysis) => analysis.analysis_date === null && analysis.overall_status !== "READY",
    );
  }, [filteredAnalyses]);

  const completedHistory = useMemo(() => {
    return filteredAnalyses.filter(
      (analysis) =>
        analysis.analysis_id !== latestCompletedAnalysis?.analysis_id &&
        analysis.analysis_date !== null,
    );
  }, [filteredAnalyses, latestCompletedAnalysis]);

  const topRisks = data?.top_risks ?? [];
  const topActions = data?.top_actions ?? [];
  const reviewItemSummary = data?.review_item_summary ?? {
    open_count: 0,
    in_progress_count: 0,
    deferred_count: 0,
    overdue_count: 0,
  };

  function clearFilters() {
    setStatusFilter("ALL");
    setShowUnresolvedOnly(false);
  }

  async function handleLogout() {
    await logout();
    navigate("/login", { replace: true });
  }
  
  async function handleMarkNotificationRead(notificationId: string) {
    await markNotificationRead(notificationId);
    const refreshed = await getNotifications();
    setNotifications(refreshed);
  }

  if (error) {
    return <ErrorState title="Could not load dashboard" message={error} />;
  }

  if (!data || !notifications) {
    return <LoadingState message="Loading dashboard..." />;
  }

  if (data.analyses.length === 0) {
    return (
      <EmptyState
        title="No analyses found"
        message="Create an intake to begin a new upgrade impact analysis."
      />
    );
  }

  return (
    <AppShell
      title="Dashboard"
      subtitle="Track analysis status, review pressure, and stale refresh activity from a calmer operator view."
      actions={
        <>
          {canManageIntakes(currentRole) ? (
            <ButtonLink to="/intakes/new" variant="primary">
              Create Intake
            </ButtonLink>
          ) : null}
          <ButtonLink to="/review-queue" variant="subtle">
            Review Queue
          </ButtonLink>
          {isAdminRole(currentRole) ? (
            <ButtonLink to="/admin/inspection" variant="subtle">
              Admin Inspection
            </ButtonLink>
          ) : null}
        </>
      }
    >
      <div className="ui-grid ui-grid--two">
        <div className="ui-stack">
          <Card muted>
            <div className="ui-kicker">Signed In</div>
            <div style={{ fontSize: "1.05rem", fontWeight: 700 }}>{user?.display_name}</div>
            <div style={{ color: "var(--text-secondary)", marginTop: "0.35rem" }}>{user?.email}</div>
            <div style={{ color: "var(--text-secondary)", marginTop: "0.35rem" }}>Role: {currentRole}</div>
            <div style={{ marginTop: "1rem" }}>
              <button type="button" className="ui-button" onClick={() => void handleLogout()}>
                Log Out
              </button>
            </div>
          </Card>

          <Card title="Summary">
            <div className="ui-grid ui-grid--stats">
              <StatCard label="Analyses in View" value={dashboardMetrics.totalAnalyses} />
              <StatCard label="Ready" value={dashboardMetrics.readyAnalyses} />
              <StatCard label="Review Required" value={dashboardMetrics.reviewRequiredAnalyses} />
              <StatCard label="Running" value={dashboardMetrics.runningAnalyses} />
              <StatCard label="Stale" value={dashboardMetrics.staleAnalyses} />
              <StatCard label="Refreshed Runs" value={dashboardMetrics.refreshedAnalyses} />
              <StatCard label="Unknown Findings" value={dashboardMetrics.unknownFindings} />
              <StatCard label="Blocked Findings" value={dashboardMetrics.blockedFindings} />
              <StatCard label="Open Review Items" value={reviewItemSummary.open_count} />
              <StatCard
                label="In Progress Review Items"
                value={reviewItemSummary.in_progress_count}
              />
              <StatCard label="Deferred Review Items" value={reviewItemSummary.deferred_count} />
              <StatCard label="Overdue Review Items" value={reviewItemSummary.overdue_count} />
            </div>
          </Card>

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
                  <option value="READY">READY</option>
                  <option value="REVIEW_REQUIRED">REVIEW_REQUIRED</option>
                  <option value="ANALYSIS_RUNNING">ANALYSIS_RUNNING</option>
                  <option value="STALE">STALE</option>
                  <option value="BLOCKED">BLOCKED</option>
                  <option value="FAILED">FAILED</option>
                </select>
              </div>

              <div className="ui-toolbar__group">
                <label className="ui-label">View</label>
                <label style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                  <input
                    type="checkbox"
                    checked={showUnresolvedOnly}
                    onChange={(e) => setShowUnresolvedOnly(e.target.checked)}
                  />
                  <span>Show unresolved only</span>
                </label>
              </div>

              <div className="ui-toolbar__group">
                <label className="ui-label">Actions</label>
                <button type="button" className="ui-button" onClick={clearFilters}>
                  Clear Filters
                </button>
              </div>
            </div>

            {statusFilter !== "ALL" || showUnresolvedOnly ? (
              <div style={{ marginTop: "1rem" }}>
                <div className="ui-chip-row">
                  {statusFilter !== "ALL" ? (
                    <FilterChip
                      label={`Status: ${formatStatusLabel(statusFilter)}`}
                      onClear={() => setStatusFilter("ALL")}
                    />
                  ) : null}

                  {showUnresolvedOnly ? (
                    <FilterChip
                      label="Unresolved Only"
                      onClear={() => setShowUnresolvedOnly(false)}
                    />
                  ) : null}
                </div>
              </div>
            ) : null}
          </Card>

          {latestCompletedAnalysis ? (
            <Card title="Latest Completed Analysis">
              <AnalysisCard analysis={latestCompletedAnalysis} />
            </Card>
          ) : null}

          {activeAnalyses.length > 0 ? (
            <Card title="Active / Incomplete Analyses">
              {activeAnalyses.map((analysis) => (
                <AnalysisCard key={analysis.analysis_id} analysis={analysis} />
              ))}
            </Card>
          ) : null}

          {completedHistory.length > 0 ? (
            <Card title="Completed Analysis History">
              {completedHistory.map((analysis) => (
                <AnalysisCard key={analysis.analysis_id} analysis={analysis} />
              ))}
            </Card>
          ) : null}

          {filteredAnalyses.length === 0 ? (
            <EmptyState
              title="No matching analyses"
              message="No analyses match the current filters. Clear or adjust the filters to see more results."
            />
          ) : null}
        </div>

        <div className="ui-stack">
          <NotificationTray
            unreadCount={notifications.unread_count}
            items={notifications.items}
            onMarkRead={handleMarkNotificationRead}
          />

          {topRisks.length > 0 ? (
            <Card title="Top Risks">
              <ul className="ui-list ui-list--compact">
                {topRisks.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </Card>
          ) : null}

          {topActions.length > 0 ? (
            <Card title="Top Actions">
              <ul className="ui-list ui-list--compact">
                {topActions.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </Card>
          ) : null}
        </div>
      </div>
    </AppShell>
  );
}