import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";
import EmptyState from "../components/EmptyState";
import StatusHelp from "../components/StatusHelp";
import { formatStatusLabel } from "../utils/status";
import { formatUnixSeconds } from "../utils/time";
import { getDashboard, type DashboardAnalysisItem, type DashboardResponse } from "../services/dashboard";

function AnalysisCard({ analysis }: { analysis: DashboardAnalysisItem }) {
  return (
    <article style={{ marginBottom: "1.5rem" }}>
      <h3>
        <Link to={`/analyses/${analysis.analysis_id}`}>
          {analysis.customer_name} — {analysis.environment_name}
        </Link>
      </h3>
      <p>Analysis ID: {analysis.analysis_id}</p>
      <p>Status: {formatStatusLabel(analysis.overall_status)}</p>
      <StatusHelp status={analysis.overall_status} />
      <p>
        Applies: {analysis.applies_count} | Review Required: {analysis.review_required_count} | Unknown:{" "}
        {analysis.unknown_count} | Blocked: {analysis.blocked_count}
      </p>
      <p>Applications in Scope: {analysis.applications_count}</p>
      <p>Analysis Date: {formatUnixSeconds(analysis.analysis_date)}</p>
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
    <button
      type="button"
      onClick={onClear}
      style={{ marginRight: "0.5rem", marginBottom: "0.5rem" }}
    >
      {label} ×
    </button>
  );
}

function SummaryCard({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  return (
    <div
      style={{
        border: "1px solid #ccc",
        padding: "0.75rem 1rem",
        minWidth: "10rem",
      }}
    >
      <div style={{ fontSize: "0.9rem" }}>{label}</div>
      <div style={{ fontSize: "1.5rem", fontWeight: 700 }}>{value}</div>
    </div>
  );
}

export default function DashboardPage() {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [statusFilter, setStatusFilter] = useState("ALL");
  const [showUnresolvedOnly, setShowUnresolvedOnly] = useState(false);

  useEffect(() => {
    getDashboard().then(setData).catch((err: Error) => setError(err.message));
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

  if (error) {
    return <ErrorState title="Could not load dashboard" message={error} />;
  }

  if (!data) {
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
    <main style={{ padding: "2rem", fontFamily: "sans-serif", maxWidth: "64rem" }}>
      <h1>Dashboard</h1>

      <p>
        <Link to="/intakes/new">Create Intake</Link>
      </p>
      <p>
        <Link to="/review-queue">Open Review Queue</Link>
      </p>
      <p>
        <Link to="/admin/inspection">Open Admin Inspection</Link>
      </p>

      <section style={{ marginBottom: "2rem" }}>
        <h2>Filters</h2>

        <div style={{ marginBottom: "1rem" }}>
          <label>Status </label>
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="ALL">ALL</option>
            <option value="READY">READY</option>
            <option value="REVIEW_REQUIRED">REVIEW_REQUIRED</option>
            <option value="ANALYSIS_RUNNING">ANALYSIS_RUNNING</option>
            <option value="STALE">STALE</option>
            <option value="BLOCKED">BLOCKED</option>
            <option value="FAILED">FAILED</option>
          </select>
        </div>

        <div style={{ marginBottom: "1rem" }}>
          <label>
            <input
              type="checkbox"
              checked={showUnresolvedOnly}
              onChange={(e) => setShowUnresolvedOnly(e.target.checked)}
            />{" "}
            Show unresolved only
          </label>
        </div>

        <button type="button" onClick={clearFilters}>
          Clear Filters
        </button>
      </section>

      {(statusFilter !== "ALL" || showUnresolvedOnly) && (
        <section style={{ marginBottom: "2rem" }}>
          <h2>Active Filters</h2>

          <div>
            {statusFilter !== "ALL" && (
              <FilterChip
                label={`Status: ${formatStatusLabel(statusFilter)}`}
                onClear={() => setStatusFilter("ALL")}
              />
            )}

            {showUnresolvedOnly && (
              <FilterChip
                label="Unresolved Only"
                onClear={() => setShowUnresolvedOnly(false)}
              />
            )}
          </div>
        </section>
      )}

      <section style={{ marginBottom: "2rem" }}>
        <h2>Summary</h2>
        <div
          style={{
            display: "flex",
            gap: "1rem",
            flexWrap: "wrap",
          }}
        >
          <SummaryCard label="Analyses in View" value={dashboardMetrics.totalAnalyses} />
          <SummaryCard label="Ready" value={dashboardMetrics.readyAnalyses} />
          <SummaryCard label="Review Required" value={dashboardMetrics.reviewRequiredAnalyses} />
          <SummaryCard label="Running" value={dashboardMetrics.runningAnalyses} />
          <SummaryCard label="Stale" value={dashboardMetrics.staleAnalyses} />
          <SummaryCard label="Refreshed Runs" value={dashboardMetrics.refreshedAnalyses} />
          <SummaryCard label="Unknown Findings" value={dashboardMetrics.unknownFindings} />
          <SummaryCard label="Blocked Findings" value={dashboardMetrics.blockedFindings} />
          <SummaryCard label="Open Review Items" value={reviewItemSummary.open_count} />
          <SummaryCard label="In Progress Review Items" value={reviewItemSummary.in_progress_count} />
          <SummaryCard label="Deferred Review Items" value={reviewItemSummary.deferred_count} />
          <SummaryCard label="Overdue Review Items" value={reviewItemSummary.overdue_count} />
        </div>
      </section>

      {latestCompletedAnalysis && (
        <>
          <h2>Latest Completed Analysis</h2>
          <AnalysisCard analysis={latestCompletedAnalysis} />
        </>
      )}

      {topRisks.length > 0 && (
        <>
          <h2>Top Risks</h2>
          <ul>
            {topRisks.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </>
      )}

      {topActions.length > 0 && (
        <>
          <h2>Top Actions</h2>
          <ul>
            {topActions.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </>
      )}

      {activeAnalyses.length > 0 && (
        <>
          <h2>Active / Incomplete Analyses</h2>
          {activeAnalyses.map((analysis) => (
            <AnalysisCard key={analysis.analysis_id} analysis={analysis} />
          ))}
        </>
      )}

      {completedHistory.length > 0 && (
        <>
          <h2>Completed Analysis History</h2>
          {completedHistory.map((analysis) => (
            <AnalysisCard key={analysis.analysis_id} analysis={analysis} />
          ))}
        </>
      )}

      {filteredAnalyses.length === 0 && (
        <EmptyState
          title="No matching analyses"
          message="No analyses match the current filters. Clear or adjust the filters to see more results."
        />
      )}
    </main>
  );
}