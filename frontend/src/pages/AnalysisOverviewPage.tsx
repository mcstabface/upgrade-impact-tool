import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { formatStatusLabel } from "../utils/status";
import StatusHelp from "../components/StatusHelp";
import { formatUnixSeconds } from "../utils/time";
import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";
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

function SectionList({
  title,
  items,
}: {
  title: string;
  items: string[];
}) {
  if (items.length === 0) return null;

  return (
    <section style={{ marginBottom: "2rem" }}>
      <h2>{title}</h2>
      <ul>
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
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

export default function AnalysisOverviewPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState<AnalysisOverviewResponse | null>(null);
  const [deltaData, setDeltaData] = useState<AnalysisDeltaSummaryResponse | null>(null);
  const [auditData, setAuditData] = useState<AnalysisAuditResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [evaluatingStaleness, setEvaluatingStaleness] = useState(false);
  const [refreshingAnalysis, setRefreshingAnalysis] = useState(false);

  useEffect(() => {
    if (!id) return;

    async function loadPage() {
      try {
        const overview = await getAnalysisOverview(id);
        setData(overview);

        if (overview.previous_analysis_id) {
          const delta = await getAnalysisDeltaSummary(id);
          setDeltaData(delta);
        } else {
          setDeltaData(null);
        }

        const audit = await getAnalysisAudit(id);
        setAuditData(audit);
      } catch (err) {
        setError((err as Error).message);
      }
    }

    loadPage();
  }, [id]);

  async function handleEvaluateStaleness() {
    if (!id || !data) return;

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
    if (!id) return;

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

  if (error) return <ErrorState message={error} />;
  if (!data) return <LoadingState />;

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
    <main style={{ padding: "2rem", fontFamily: "sans-serif", maxWidth: "64rem" }}>
      <h1>Analysis Overview</h1>

      <p>
        <Link to="/dashboard">Back to Dashboard</Link>
      </p>

      {id && (
        <p>
          <a href={getAnalysisExportJsonUrl(id)}>Export Analysis JSON</a>
        </p>
      )}

      {message && <p>{message}</p>}

      <section style={{ marginBottom: "2rem" }}>
        <p>Analysis ID: {data.analysis_id}</p>
        <p>
          {data.customer_name} — {data.environment_name}
        </p>
        <p>Status: {formatStatusLabel(data.overall_status)}</p>
        <StatusHelp status={data.overall_status} />
        <p>Started: {formatUnixSeconds(data.started_utc)}</p>
        <p>Completed: {formatUnixSeconds(data.completed_utc)}</p>
        <p>Duration (ms): {data.duration_ms ?? "N/A"}</p>
        {data.stale_reason && <p>Stale Reason: {data.stale_reason}</p>}
        {data.stale_detected_utc && (
          <p>Stale Detected: {formatUnixSeconds(data.stale_detected_utc)}</p>
        )}
        {data.previous_analysis_id && <p>Previous Analysis: {data.previous_analysis_id}</p>}
        {reviewNote && <p>{reviewNote}</p>}

        <div style={{ marginTop: "1rem", display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
          <button
            type="button"
            onClick={handleEvaluateStaleness}
            disabled={evaluatingStaleness || refreshingAnalysis}
          >
            {evaluatingStaleness ? "Evaluating..." : "Evaluate Staleness"}
          </button>

          {data.overall_status === "STALE" && (
            <button
              type="button"
              onClick={handleRefreshAnalysis}
              disabled={refreshingAnalysis || evaluatingStaleness}
            >
              {refreshingAnalysis ? "Refreshing..." : "Refresh Analysis"}
            </button>
          )}
        </div>
      </section>

      {deltaData && (
        <section style={{ marginBottom: "2rem" }}>
          <h2>Delta Summary</h2>
          <p>Previous Analysis: {deltaData.previous_analysis_id}</p>
          <p>Current Analysis: {deltaData.current_analysis_id}</p>

          <div
            style={{
              display: "flex",
              gap: "1rem",
              flexWrap: "wrap",
              marginBottom: "1rem",
            }}
          >
            <SummaryCard label="New Findings" value={deltaData.new_findings_count} />
            <SummaryCard label="Resolved Findings" value={deltaData.resolved_findings_count} />
            <SummaryCard label="Updated Findings" value={deltaData.updated_findings_count} />
            <SummaryCard label="Unchanged Findings" value={deltaData.unchanged_findings_count} />
            <SummaryCard label="New KB Articles" value={deltaData.new_kb_articles_count} />
            <SummaryCard label="Updated KB Articles" value={deltaData.updated_kb_articles_count} />
          </div>

          <SectionList title="Applications Impacted" items={deltaData.applications_impacted} />
          <SectionList title="Delta Notes" items={deltaData.summary_lines} />
        </section>
      )}

      {auditData && (
        <section style={{ marginBottom: "2rem" }}>
          <h2>Audit and Lineage</h2>

          <SectionList
            title="Lineage Chain"
            items={auditData.lineage.map((node) => {
              const started = formatUnixSeconds(node.started_utc);
              const completed = formatUnixSeconds(node.completed_utc);
              return `${node.analysis_id} | Status: ${formatStatusLabel(node.overall_status)} | Started: ${started} | Completed: ${completed}`;
            })}
          />

          <SectionList
            title="State Transitions"
            items={auditData.transitions.map((transition) => {
              const previousState = transition.previous_state ?? "NONE";
              const transitionTime = formatUnixSeconds(transition.transition_utc);
              return `${transition.analysis_id} | ${previousState} -> ${transition.new_state} | Trigger: ${transition.trigger_event} | User: ${transition.user_id ?? "system"} | At: ${transitionTime}`;
            })}
          />
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
          <SummaryCard label="Applies" value={data.summary.applies_count} />
          <SummaryCard label="Requires Review" value={data.summary.review_required_count} />
          <SummaryCard label="Unknown" value={data.summary.unknown_count} />
          <SummaryCard label="Blocked" value={data.summary.blocked_count} />
        </div>
      </section>

      <SectionList title="Top Risks" items={topRisks} />
      <SectionList title="Top Actions" items={topActions} />
      <SectionList title="Assumptions" items={data.assumptions} />
      <SectionList title="Missing Inputs" items={data.missing_inputs} />
      <SectionList title="Derived Risks" items={data.derived_risks} />

      <section>
        <h2>Applications</h2>
        <ul>
          {data.applications.map((app) => (
            <li key={app.analysis_application_id} style={{ marginBottom: "1rem" }}>
              <div>
                <Link to={`/analyses/${data.analysis_id}/applications/${app.analysis_application_id}`}>
                  {app.application_name}
                </Link>{" "}
                — {app.status}
              </div>
              <div>
                Current: {app.current_version} | Target: {app.target_version} | Findings:{" "}
                {app.findings_count}
              </div>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}