import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";
import EmptyState from "../components/EmptyState";
import { getCurrentRole, isAdminRole } from "../auth/role";
import { getDashboard, type DashboardAnalysisItem } from "../services/dashboard";
import { getAnalysisAudit, type AnalysisAuditResponse } from "../services/analyses";
import {
  getObservabilitySummary,
  type ObservabilitySummaryResponse,
} from "../services/observability";
import { formatStatusLabel } from "../utils/status";
import { formatUnixSeconds } from "../utils/time";

function SummaryCard({
  label,
  value,
}: {
  label: string;
  value: number | string;
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

function AnalysisInspectionCard({
  analysis,
  onInspect,
  selected,
}: {
  analysis: DashboardAnalysisItem;
  onInspect: (analysisId: string) => void;
  selected: boolean;
}) {
  return (
    <article
      style={{
        border: "1px solid #ccc",
        padding: "1rem",
        marginBottom: "1rem",
        backgroundColor: selected ? "#f7f7f7" : undefined,
      }}
    >
      <div style={{ marginBottom: "0.5rem" }}>
        <strong>{analysis.analysis_id}</strong>
      </div>
      <div>
        {analysis.customer_name} — {analysis.environment_name}
      </div>
      <div>Status: {formatStatusLabel(analysis.overall_status)}</div>
      {analysis.previous_analysis_id && (
        <div>Previous Analysis: {analysis.previous_analysis_id}</div>
      )}
      {analysis.stale_reason && <div>Stale Reason: {analysis.stale_reason}</div>}
      {analysis.stale_detected_utc && (
        <div>Stale Detected: {formatUnixSeconds(analysis.stale_detected_utc)}</div>
      )}
      <div>
        Applies: {analysis.applies_count} | Review Required: {analysis.review_required_count} | Unknown:{" "}
        {analysis.unknown_count} | Blocked: {analysis.blocked_count}
      </div>
      <div style={{ marginTop: "0.75rem", display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
        <Link to={`/analyses/${analysis.analysis_id}`}>Open Analysis</Link>
        <button type="button" onClick={() => onInspect(analysis.analysis_id)}>
          {selected ? "Reload Audit" : "Inspect Audit"}
        </button>
      </div>
    </article>
  );
}

export default function AdminInspectionPage() {
  const currentRole = getCurrentRole();
  const [analyses, setAnalyses] = useState<DashboardAnalysisItem[] | null>(null);
  const [observability, setObservability] = useState<ObservabilitySummaryResponse | null>(null);
  const [audit, setAudit] = useState<AnalysisAuditResponse | null>(null);
  const [selectedAnalysisId, setSelectedAnalysisId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [auditError, setAuditError] = useState<string | null>(null);
  const [loadingAudit, setLoadingAudit] = useState(false);

  const loadInspectionView = useCallback(async () => {
    if (!isAdminRole(currentRole)) {
      return;
    }

    setError(null);

    try {
      const [dashboardResult, observabilityResult] = await Promise.all([
        getDashboard(),
        getObservabilitySummary(),
      ]);
      setAnalyses(dashboardResult.analyses);
      setObservability(observabilityResult);
    } catch (err) {
      setError((err as Error).message);
    }
  }, [currentRole]);

  useEffect(() => {
    loadInspectionView();
  }, [loadInspectionView]);

  const staleAnalyses = useMemo(() => {
    if (!analyses) return [];
    return analyses.filter((analysis) => analysis.overall_status === "STALE");
  }, [analyses]);

  const refreshedAnalyses = useMemo(() => {
    if (!analyses) return [];
    return analyses.filter((analysis) => analysis.previous_analysis_id !== null);
  }, [analyses]);

  const inspectionCount = useMemo(() => {
    return new Set([
      ...staleAnalyses.map((analysis) => analysis.analysis_id),
      ...refreshedAnalyses.map((analysis) => analysis.analysis_id),
    ]).size;
  }, [staleAnalyses, refreshedAnalyses]);

  const loadAudit = useCallback(async (analysisId: string) => {
    setSelectedAnalysisId(analysisId);
    setAuditError(null);
    setLoadingAudit(true);

    try {
      const result = await getAnalysisAudit(analysisId);
      setAudit(result);
    } catch (err) {
      setAudit(null);
      setAuditError((err as Error).message);
    } finally {
      setLoadingAudit(false);
    }
  }, []);

  if (!isAdminRole(currentRole)) {
    return (
      <ErrorState
        title="Permission denied"
        message="Admin role is required to access the admin inspection view."
      />
    );
  }

  if (error) {
    return (
      <ErrorState
        title="Could not load admin inspection view"
        message={error}
        onRetry={loadInspectionView}
        retryLabel="Retry Load"
      />
    );
  }

  if (!analyses || !observability) {
    return <LoadingState message="Loading admin inspection view..." />;
  }

  return (
    <main style={{ padding: "2rem", fontFamily: "sans-serif", maxWidth: "72rem" }}>
      <h1>Admin Inspection</h1>

      <p>
        <Link to="/dashboard">Back to Dashboard</Link>
      </p>

      <section style={{ marginBottom: "2rem" }}>
        <h2>System Health Summary</h2>
        <div
          style={{
            display: "flex",
            gap: "1rem",
            flexWrap: "wrap",
          }}
        >
          <SummaryCard label="Health Status" value={observability.system_health_status} />
          {observability.counts.map((item) => (
            <SummaryCard key={item.label} label={item.label} value={item.value} />
          ))}
        </div>
      </section>

      <section style={{ marginBottom: "2rem" }}>
        <h2>Pilot Usage Summary</h2>
        <div
          style={{
            display: "flex",
            gap: "1rem",
            flexWrap: "wrap",
          }}
        >
          {observability.pilot_usage_metrics.map((item) => (
            <SummaryCard key={item.label} label={item.label} value={item.value} />
          ))}
        </div>
      </section>

      <section style={{ marginBottom: "2rem" }}>
        <h2>Inspection Summary</h2>
        <div
          style={{
            display: "flex",
            gap: "1rem",
            flexWrap: "wrap",
          }}
        >
          <SummaryCard label="Analyses in Inspection Scope" value={inspectionCount} />
          <SummaryCard label="Stale Analyses" value={staleAnalyses.length} />
          <SummaryCard label="Refreshed Analyses" value={refreshedAnalyses.length} />
        </div>
      </section>

      <section style={{ marginBottom: "2rem" }}>
        <h2>Most Common Blocked Fields</h2>
        {observability.most_common_blocked_fields.length === 0 ? (
          <EmptyState
            title="No blocked-field patterns"
            message="No blocked validation field patterns are currently available to summarize."
          />
        ) : (
          <ul>
            {observability.most_common_blocked_fields.map((item) => (
              <li key={item.label}>
                {item.label} — {item.value}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section style={{ marginBottom: "2rem" }}>
        <h2>Most Common Missing Inputs</h2>
        {observability.most_common_missing_inputs.length === 0 ? (
          <EmptyState
            title="No missing-input patterns"
            message="No missing-input text is currently available to summarize."
          />
        ) : (
          <ul>
            {observability.most_common_missing_inputs.map((item) => (
              <li key={item.label}>
                {item.label} — {item.value}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section style={{ marginBottom: "2rem" }}>
        <h2>Most Frequent Review Reasons</h2>
        {observability.most_frequent_review_reasons.length === 0 ? (
          <EmptyState
            title="No review reasons recorded"
            message="No review-item reasons are currently available to summarize."
          />
        ) : (
          <ul>
            {observability.most_frequent_review_reasons.map((item) => (
              <li key={item.label}>
                {item.label} — {item.value}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section style={{ marginBottom: "2rem" }}>
        <h2>Stale Analyses</h2>
        {staleAnalyses.length === 0 ? (
          <EmptyState
            title="No stale analyses"
            message="No analyses are currently marked stale."
          />
        ) : (
          staleAnalyses.map((analysis) => (
            <AnalysisInspectionCard
              key={analysis.analysis_id}
              analysis={analysis}
              onInspect={loadAudit}
              selected={selectedAnalysisId === analysis.analysis_id}
            />
          ))
        )}
      </section>

      <section style={{ marginBottom: "2rem" }}>
        <h2>Refreshed Analyses</h2>
        {refreshedAnalyses.length === 0 ? (
          <EmptyState
            title="No refreshed analyses"
            message="No analyses currently reference a previous analysis."
          />
        ) : (
          refreshedAnalyses.map((analysis) => (
            <AnalysisInspectionCard
              key={analysis.analysis_id}
              analysis={analysis}
              onInspect={loadAudit}
              selected={selectedAnalysisId === analysis.analysis_id}
            />
          ))
        )}
      </section>

      <section>
        <h2>Inspection Audit</h2>

        {!selectedAnalysisId && (
          <EmptyState
            title="No analysis selected"
            message="Choose a stale or refreshed analysis to load its audit and lineage."
          />
        )}

        {loadingAudit && <LoadingState message="Loading audit..." />}

        {auditError && selectedAnalysisId && (
          <ErrorState
            title="Could not load audit"
            message={auditError}
            onRetry={() => loadAudit(selectedAnalysisId)}
            retryLabel="Retry Audit Load"
          />
        )}

        {!loadingAudit && !auditError && audit && (
          <>
            <p>Selected Analysis: {audit.analysis_id}</p>

            <section style={{ marginBottom: "2rem" }}>
              <h3>Lineage Chain</h3>
              <ul>
                {audit.lineage.map((node) => (
                  <li key={node.analysis_id}>
                    {node.analysis_id} | Status: {formatStatusLabel(node.overall_status)} | Started:{" "}
                    {formatUnixSeconds(node.started_utc)} | Completed: {formatUnixSeconds(node.completed_utc)}
                  </li>
                ))}
              </ul>
            </section>

            <section>
              <h3>State Transitions</h3>
              <ul>
                {audit.transitions.map((transition) => (
                  <li key={transition.state_transition_id}>
                    {transition.analysis_id} | {transition.previous_state ?? "NONE"} -&gt;{" "}
                    {transition.new_state} | Trigger: {transition.trigger_event} | User:{" "}
                    {transition.user_id ?? "system"} | At: {formatUnixSeconds(transition.transition_utc)}
                  </li>
                ))}
              </ul>
            </section>
          </>
        )}
      </section>
    </main>
  );
}