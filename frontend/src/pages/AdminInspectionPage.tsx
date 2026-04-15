import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";
import EmptyState from "../components/EmptyState";
import { getDashboard, type DashboardAnalysisItem } from "../services/dashboard";
import { getAnalysisAudit, type AnalysisAuditResponse } from "../services/analyses";
import { formatStatusLabel } from "../utils/status";
import { formatUnixSeconds } from "../utils/time";

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
  const [analyses, setAnalyses] = useState<DashboardAnalysisItem[] | null>(null);
  const [audit, setAudit] = useState<AnalysisAuditResponse | null>(null);
  const [selectedAnalysisId, setSelectedAnalysisId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [auditError, setAuditError] = useState<string | null>(null);
  const [loadingAudit, setLoadingAudit] = useState(false);

  useEffect(() => {
    getDashboard()
      .then((result) => setAnalyses(result.analyses))
      .catch((err: Error) => setError(err.message));
  }, []);

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

  async function handleInspectAudit(analysisId: string) {
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
  }

  if (error) {
    return <ErrorState title="Could not load admin inspection view" message={error} />;
  }

  if (!analyses) {
    return <LoadingState message="Loading admin inspection view..." />;
  }

  return (
    <main style={{ padding: "2rem", fontFamily: "sans-serif", maxWidth: "72rem" }}>
      <h1>Admin Inspection</h1>

      <p>
        <Link to="/dashboard">Back to Dashboard</Link>
      </p>

      <section style={{ marginBottom: "2rem" }}>
        <h2>Summary</h2>
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
              onInspect={handleInspectAudit}
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
              onInspect={handleInspectAudit}
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

        {auditError && (
          <ErrorState title="Could not load audit" message={auditError} />
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