import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import AppShell from "../components/layout/AppShell";
import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";
import EmptyState from "../components/EmptyState";
import Card from "../components/ui/Card";
import StatCard from "../components/ui/StatCard";
import ButtonLink from "../components/ui/ButtonLink";
import { isAdminRole } from "../auth/role";
import { useCurrentRole } from "../auth/AuthContext";
import { getDashboard, type DashboardAnalysisItem } from "../services/dashboard";
import { getAnalysisAudit, type AnalysisAuditResponse } from "../services/analyses";
import {
  getObservabilitySummary,
  type ObservabilitySummaryResponse,
} from "../services/observability";
import { formatStatusLabel } from "../utils/status";
import { formatUnixSeconds } from "../utils/time";

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
      className="ui-analysis-card"
      style={{
        backgroundColor: selected ? "var(--bg-surface-strong)" : undefined,
      }}
    >
      <div style={{ marginBottom: "0.5rem", fontWeight: 700 }}>{analysis.analysis_id}</div>
      <div className="ui-analysis-card__summary">
        {analysis.customer_name} — {analysis.environment_name}
      </div>
      <div className="ui-analysis-card__summary">
        Status: {formatStatusLabel(analysis.overall_status)}
      </div>
      {analysis.previous_analysis_id ? (
        <div className="ui-analysis-card__summary">
          Previous Analysis: {analysis.previous_analysis_id}
        </div>
      ) : null}
      {analysis.stale_reason ? (
        <div className="ui-analysis-card__summary">Stale Reason: {analysis.stale_reason}</div>
      ) : null}
      {analysis.stale_detected_utc ? (
        <div className="ui-analysis-card__summary">
          Stale Detected: {formatUnixSeconds(analysis.stale_detected_utc)}
        </div>
      ) : null}
      <div className="ui-analysis-card__summary">
        Applies: {analysis.applies_count} | Review Required: {analysis.review_required_count} |
        Unknown: {analysis.unknown_count} | Blocked: {analysis.blocked_count}
      </div>
      <div className="ui-inline-actions" style={{ marginTop: "0.9rem" }}>
        <Link to={`/analyses/${analysis.analysis_id}`}>Open Analysis</Link>
        <button
          type="button"
          className="ui-button"
          onClick={() => onInspect(analysis.analysis_id)}
        >
          {selected ? "Reload Audit" : "Inspect Audit"}
        </button>
      </div>
    </article>
  );
}

export default function AdminInspectionPage() {
  const currentRole = useCurrentRole();
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
    <AppShell
      title="Admin Inspection"
      subtitle="Inspect pilot health, blocked patterns, stale analysis pressure, and audit lineage from one controlled admin surface."
      actions={
        <ButtonLink to="/dashboard" variant="subtle">
          Back to Dashboard
        </ButtonLink>
      }
    >
      <div className="ui-stack">
        <Card title="System Health Summary">
          <div className="ui-grid ui-grid--stats">
            <StatCard label="Health Status" value={observability.system_health_status} />
            {observability.counts.map((item) => (
              <StatCard key={item.label} label={item.label} value={item.value} />
            ))}
          </div>
        </Card>

        <Card title="Pilot Usage Summary">
          <div className="ui-grid ui-grid--stats">
            {observability.pilot_usage_metrics.map((item) => (
              <StatCard key={item.label} label={item.label} value={item.value} />
            ))}
          </div>
        </Card>

        <Card title="Inspection Summary">
          <div className="ui-grid ui-grid--stats">
            <StatCard label="Analyses in Inspection Scope" value={inspectionCount} />
            <StatCard label="Stale Analyses" value={staleAnalyses.length} />
            <StatCard label="Refreshed Analyses" value={refreshedAnalyses.length} />
          </div>
        </Card>

        <Card title="Most Common Blocked Fields">
          {observability.most_common_blocked_fields.length === 0 ? (
            <EmptyState
              title="No blocked-field patterns"
              message="No blocked validation field patterns are currently available to summarize."
            />
          ) : (
            <ul className="ui-list ui-list--compact">
              {observability.most_common_blocked_fields.map((item) => (
                <li key={item.label}>
                  {item.label} — {item.value}
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card title="Most Common Missing Inputs">
          {observability.most_common_missing_inputs.length === 0 ? (
            <EmptyState
              title="No missing-input patterns"
              message="No missing-input text is currently available to summarize."
            />
          ) : (
            <ul className="ui-list ui-list--compact">
              {observability.most_common_missing_inputs.map((item) => (
                <li key={item.label}>
                  {item.label} — {item.value}
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card title="Most Frequent Review Reasons">
          {observability.most_frequent_review_reasons.length === 0 ? (
            <EmptyState
              title="No review reasons recorded"
              message="No review-item reasons are currently available to summarize."
            />
          ) : (
            <ul className="ui-list ui-list--compact">
              {observability.most_frequent_review_reasons.map((item) => (
                <li key={item.label}>
                  {item.label} — {item.value}
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card title="Stale Analyses">
          {staleAnalyses.length === 0 ? (
            <EmptyState
              title="No stale analyses"
              message="No analyses are currently marked stale."
            />
          ) : (
            <div className="ui-stack" style={{ gap: "1rem" }}>
              {staleAnalyses.map((analysis) => (
                <AnalysisInspectionCard
                  key={analysis.analysis_id}
                  analysis={analysis}
                  onInspect={loadAudit}
                  selected={selectedAnalysisId === analysis.analysis_id}
                />
              ))}
            </div>
          )}
        </Card>

        <Card title="Refreshed Analyses">
          {refreshedAnalyses.length === 0 ? (
            <EmptyState
              title="No refreshed analyses"
              message="No analyses currently reference a previous analysis."
            />
          ) : (
            <div className="ui-stack" style={{ gap: "1rem" }}>
              {refreshedAnalyses.map((analysis) => (
                <AnalysisInspectionCard
                  key={analysis.analysis_id}
                  analysis={analysis}
                  onInspect={loadAudit}
                  selected={selectedAnalysisId === analysis.analysis_id}
                />
              ))}
            </div>
          )}
        </Card>

        <Card title="Inspection Audit">
          {!selectedAnalysisId ? (
            <EmptyState
              title="No analysis selected"
              message="Choose a stale or refreshed analysis to load its audit and lineage."
            />
          ) : null}

          {loadingAudit ? <LoadingState message="Loading audit..." /> : null}

          {auditError && selectedAnalysisId ? (
            <ErrorState
              title="Could not load audit"
              message={auditError}
              onRetry={() => loadAudit(selectedAnalysisId)}
              retryLabel="Retry Audit Load"
            />
          ) : null}

          {!loadingAudit && !auditError && audit ? (
            <div className="ui-stack">
              <div className="ui-meta-list">
                <div className="ui-meta-list__row">
                  <span className="ui-meta-list__label">Selected Analysis</span>
                  <span>{audit.analysis_id}</span>
                </div>
              </div>

              <div>
                <h3 className="ui-section-title">Lineage Chain</h3>
                <ul className="ui-list ui-list--compact">
                  {audit.lineage.map((node) => (
                    <li key={node.analysis_id}>
                      {node.analysis_id} | Status: {formatStatusLabel(node.overall_status)} |
                      Started: {formatUnixSeconds(node.started_utc)} | Completed:{" "}
                      {formatUnixSeconds(node.completed_utc)}
                    </li>
                  ))}
                </ul>
              </div>

              <div>
                <h3 className="ui-section-title">State Transitions</h3>
                <ul className="ui-list ui-list--compact">
                  {audit.transitions.map((transition) => (
                    <li key={transition.state_transition_id}>
                      {transition.analysis_id} | {transition.previous_state ?? "NONE"} -&gt;{" "}
                      {transition.new_state} | Trigger: {transition.trigger_event} | User:{" "}
                      {transition.user_id ?? "system"} | At:{" "}
                      {formatUnixSeconds(transition.transition_utc)}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ) : null}
        </Card>
      </div>
    </AppShell>
  );
}