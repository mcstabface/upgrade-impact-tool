import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { isAdminRole } from "../auth/role";
import { useCurrentRole } from "../auth/AuthContext";
import { formatStatusLabel } from "../utils/status";
import StatusHelp from "../components/StatusHelp";
import { formatUnixSeconds } from "../utils/time";
import AppShell from "../components/layout/AppShell";
import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";
import Card from "../components/ui/Card";
import StatCard from "../components/ui/StatCard";
import ButtonLink from "../components/ui/ButtonLink";
import {
  evaluateAnalysisStaleness,
  getAnalysisAudit,
  getAnalysisDeltaSummary,
  getAnalysisExportJsonUrl,
  getAnalysisOverview,
  refreshAnalysis,
  type AnalysisAuditResponse,
  type AnalysisDeltaSummaryResponse,
  type AnalysisOverviewResponse,
} from "../services/analyses";
import { recordResultsOverviewSession } from "../services/usageEvents";

function SectionList({
  title,
  items,
}: {
  title: string;
  items: string[];
}) {
  if (items.length === 0) return null;

  return (
    <Card title={title}>
      <ul className="ui-list ui-list--compact">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </Card>
  );
}

export default function AnalysisOverviewPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const currentRole = useCurrentRole();
  const canAdminAnalysis = isAdminRole(currentRole);

  const [data, setData] = useState<AnalysisOverviewResponse | null>(null);
  const [deltaData, setDeltaData] = useState<AnalysisDeltaSummaryResponse | null>(null);
  const [auditData, setAuditData] = useState<AnalysisAuditResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [evaluatingStaleness, setEvaluatingStaleness] = useState(false);
  const [refreshingAnalysis, setRefreshingAnalysis] = useState(false);

  const sessionStartRef = useRef<number | null>(null);
  const sessionRecordedRef = useRef(false);

  const loadPage = useCallback(async () => {
    if (!id) return;

    setError(null);

    try {
      const overview = await getAnalysisOverview(id);
      setData(overview);

      if (overview.previous_analysis_id) {
        const delta = await getAnalysisDeltaSummary(id);
        setDeltaData(delta);
      } else {
        setDeltaData(null);
      }

      if (canAdminAnalysis) {
        const audit = await getAnalysisAudit(id);
        setAuditData(audit);
      } else {
        setAuditData(null);
      }
    } catch (err) {
      setError((err as Error).message);
    }
  }, [id, canAdminAnalysis]);

  useEffect(() => {
    loadPage();
  }, [loadPage]);

  useEffect(() => {
    if (!id) {
      return;
    }

    sessionStartRef.current = Date.now();
    sessionRecordedRef.current = false;

    const flushOverviewSession = () => {
      if (!id || sessionRecordedRef.current || sessionStartRef.current === null) {
        return;
      }

      const durationSeconds = Math.max(
        1,
        Math.round((Date.now() - sessionStartRef.current) / 1000),
      );

      if (durationSeconds < 5) {
        sessionRecordedRef.current = true;
        return;
      }

      sessionRecordedRef.current = true;

      void recordResultsOverviewSession({
        analysis_id: id,
        duration_seconds: durationSeconds,
      });
    };

    const handleVisibilityChange = () => {
      if (document.visibilityState === "hidden") {
        flushOverviewSession();
      }
    };

    window.addEventListener("pagehide", flushOverviewSession);
    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      window.removeEventListener("pagehide", flushOverviewSession);
      flushOverviewSession();
    };
  }, [id]);

  async function handleEvaluateStaleness() {
    if (!id || !data || !canAdminAnalysis) return;

    setEvaluatingStaleness(true);
    setError(null);
    setMessage(null);

    try {
      const result = await evaluateAnalysisStaleness(id);

      if (result.is_stale) {
        setData({
          ...data,
          overall_status: result.status,
          stale_reason: result.triggers.join(", "),
          stale_detected_utc: result.stale_detected_utc,
        });
        setMessage(`Analysis marked STALE. Triggers: ${result.triggers.join(", ")}`);
      } else {
        setMessage("No relevant source changes detected.");
      }
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setEvaluatingStaleness(false);
    }
  }

  async function handleRefreshAnalysis() {
    if (!id || !canAdminAnalysis) return;

    setRefreshingAnalysis(true);
    setError(null);
    setMessage(null);

    try {
      const result = await refreshAnalysis(id);
      navigate(`/analyses/${result.new_analysis_id}`);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setRefreshingAnalysis(false);
    }
  }

  if (error) {
    return (
      <ErrorState
        title="Could not load analysis overview"
        message={error}
        onRetry={loadPage}
        retryLabel="Retry Load"
      />
    );
  }

  if (!data) {
    return <LoadingState />;
  }

  const reviewNote =
    data.summary.unknown_count > 0
      ? "Overall status requires review because unresolved unknown findings remain."
      : data.summary.blocked_count > 0
        ? "Overall status requires review because blocked findings remain."
        : data.summary.review_required_count > 0
          ? "Overall status requires review because review-required findings remain."
          : null;

  const topRisks = data.top_risks ?? [];
  const topActions = data.top_actions ?? [];

  return (
    <AppShell
      title="Analysis Overview"
      subtitle="Review the run status, evidence-backed summary, delta context, and audit lineage for this analysis."
      actions={
        <>
          <ButtonLink to="/dashboard" variant="subtle">
            Back to Dashboard
          </ButtonLink>
          {id ? (
            <>
              <a className="ui-button" href={getAnalysisExportJsonUrl(id)}>
                Export Analysis JSON
              </a>
              <ButtonLink to={`/analyses/${id}/report`} variant="subtle">
                Printable Report
              </ButtonLink>
            </>
          ) : null}
        </>
      }
    >
      <div className="ui-stack">
        {message ? (
          <Card muted>
            <p style={{ margin: 0 }}>{message}</p>
          </Card>
        ) : null}

        <Card title="Analysis Summary">
          <div className="ui-meta-list">
            <div className="ui-meta-list__row">
              <span className="ui-meta-list__label">Analysis ID</span>
              <span>{data.analysis_id}</span>
            </div>
            <div className="ui-meta-list__row">
              <span className="ui-meta-list__label">Environment</span>
              <span>
                {data.customer_name} — {data.environment_name}
              </span>
            </div>
            <div className="ui-meta-list__row">
              <span className="ui-meta-list__label">Status</span>
              <span>{formatStatusLabel(data.overall_status)}</span>
            </div>
            <div className="ui-meta-list__row">
              <span className="ui-meta-list__label">Started</span>
              <span>{formatUnixSeconds(data.started_utc)}</span>
            </div>
            <div className="ui-meta-list__row">
              <span className="ui-meta-list__label">Completed</span>
              <span>{formatUnixSeconds(data.completed_utc)}</span>
            </div>
            <div className="ui-meta-list__row">
              <span className="ui-meta-list__label">Duration (ms)</span>
              <span>{data.duration_ms ?? "N/A"}</span>
            </div>
            {data.previous_analysis_id ? (
              <div className="ui-meta-list__row">
                <span className="ui-meta-list__label">Previous Analysis</span>
                <span>{data.previous_analysis_id}</span>
              </div>
            ) : null}
            {data.stale_reason ? (
              <div className="ui-meta-list__row">
                <span className="ui-meta-list__label">Stale Reason</span>
                <span>{data.stale_reason}</span>
              </div>
            ) : null}
            {data.stale_detected_utc ? (
              <div className="ui-meta-list__row">
                <span className="ui-meta-list__label">Stale Detected</span>
                <span>{formatUnixSeconds(data.stale_detected_utc)}</span>
              </div>
            ) : null}
          </div>

          <div style={{ marginTop: "1rem" }}>
            <StatusHelp status={data.overall_status} />
          </div>

          {reviewNote ? <p className="ui-status-note">{reviewNote}</p> : null}

          {canAdminAnalysis ? (
            <div className="ui-inline-actions" style={{ marginTop: "1rem" }}>
              <button
                type="button"
                className="ui-button"
                onClick={handleEvaluateStaleness}
                disabled={evaluatingStaleness || refreshingAnalysis}
              >
                {evaluatingStaleness ? "Evaluating..." : "Evaluate Staleness"}
              </button>

              {data.overall_status === "STALE" ? (
                <button
                  type="button"
                  className="ui-button ui-button--primary"
                  onClick={handleRefreshAnalysis}
                  disabled={refreshingAnalysis || evaluatingStaleness}
                >
                  {refreshingAnalysis ? "Refreshing..." : "Refresh Analysis"}
                </button>
              ) : null}
            </div>
          ) : null}
        </Card>

        <Card title="Finding Summary">
          <div className="ui-grid ui-grid--stats">
            <StatCard label="Applies" value={data.summary.applies_count} />
            <StatCard label="Requires Review" value={data.summary.review_required_count} />
            <StatCard label="Unknown" value={data.summary.unknown_count} />
            <StatCard label="Blocked" value={data.summary.blocked_count} />
          </div>
        </Card>

        {deltaData ? (
          <Card title="Delta Summary">
            <div className="ui-meta-list" style={{ marginBottom: "1rem" }}>
              <div className="ui-meta-list__row">
                <span className="ui-meta-list__label">Previous Analysis</span>
                <span>{deltaData.previous_analysis_id}</span>
              </div>
              <div className="ui-meta-list__row">
                <span className="ui-meta-list__label">Current Analysis</span>
                <span>{deltaData.current_analysis_id}</span>
              </div>
            </div>

            <div className="ui-grid ui-grid--stats" style={{ marginBottom: "1rem" }}>
              <StatCard label="New Findings" value={deltaData.new_findings_count} />
              <StatCard label="Resolved Findings" value={deltaData.resolved_findings_count} />
              <StatCard label="Updated Findings" value={deltaData.updated_findings_count} />
              <StatCard label="Unchanged Findings" value={deltaData.unchanged_findings_count} />
              <StatCard label="New KB Articles" value={deltaData.new_kb_articles_count} />
              <StatCard label="Updated KB Articles" value={deltaData.updated_kb_articles_count} />
            </div>

            {deltaData.applications_impacted.length > 0 ? (
              <>
                <h3 className="ui-section-title">Applications Impacted</h3>
                <ul className="ui-list ui-list--compact" style={{ marginBottom: "1rem" }}>
                  {deltaData.applications_impacted.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </>
            ) : null}

            {deltaData.summary_lines.length > 0 ? (
              <>
                <h3 className="ui-section-title">Delta Notes</h3>
                <ul className="ui-list ui-list--compact">
                  {deltaData.summary_lines.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </>
            ) : null}
          </Card>
        ) : null}

        <SectionList title="Top Risks" items={topRisks} />
        <SectionList title="Top Actions" items={topActions} />
        <SectionList title="Assumptions" items={data.assumptions} />
        <SectionList title="Missing Inputs" items={data.missing_inputs} />
        <SectionList title="Derived Risks" items={data.derived_risks} />

        {canAdminAnalysis && auditData ? (
          <Card title="Audit and Lineage">
            {auditData.lineage.length > 0 ? (
              <>
                <h3 className="ui-section-title">Lineage Chain</h3>
                <ul className="ui-list ui-list--compact" style={{ marginBottom: "1rem" }}>
                  {auditData.lineage.map((node) => {
                    const started = formatUnixSeconds(node.started_utc);
                    const completed = formatUnixSeconds(node.completed_utc);

                    return (
                      <li key={node.analysis_id}>
                        {node.analysis_id} | Status: {formatStatusLabel(node.overall_status)} |
                        Started: {started} | Completed: {completed}
                      </li>
                    );
                  })}
                </ul>
              </>
            ) : null}

            {auditData.transitions.length > 0 ? (
              <>
                <h3 className="ui-section-title">State Transitions</h3>
                <ul className="ui-list ui-list--compact">
                  {auditData.transitions.map((transition) => {
                    const previousState = transition.previous_state ?? "NONE";
                    const transitionTime = formatUnixSeconds(transition.transition_utc);

                    return (
                      <li key={transition.state_transition_id}>
                        {transition.analysis_id} | {previousState} -&gt; {transition.new_state} |
                        Trigger: {transition.trigger_event} | User:{" "}
                        {transition.user_id ?? "system"} | At: {transitionTime}
                      </li>
                    );
                  })}
                </ul>
              </>
            ) : null}
          </Card>
        ) : null}

        <Card title="Applications">
          <div className="ui-stack" style={{ gap: "1rem" }}>
            {data.applications.map((app) => (
              <article key={app.analysis_application_id} className="ui-analysis-card">
                <h3 className="ui-analysis-card__title">
                  <Link
                    to={`/analyses/${data.analysis_id}/applications/${app.analysis_application_id}`}
                  >
                    {app.application_name}
                  </Link>
                </h3>
                <p className="ui-analysis-card__summary">Status: {app.status}</p>
                <p className="ui-analysis-card__summary">
                  Current: {app.current_version} | Target: {app.target_version}
                </p>
                <p className="ui-analysis-card__summary">Findings: {app.findings_count}</p>
              </article>
            ))}
          </div>
        </Card>
      </div>
    </AppShell>
  );
}