import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";
import { formatStatusLabel } from "../utils/status";
import { formatUnixSeconds } from "../utils/time";
import {
  getAnalysisAudit,
  getAnalysisDeltaSummary,
  getAnalysisOverview,
  type AnalysisAuditResponse,
  type AnalysisDeltaSummaryResponse,
  type AnalysisOverviewResponse,
} from "../services/analyses";

function ReportSection({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section style={{ marginBottom: "2rem" }}>
      <h2>{title}</h2>
      {children}
    </section>
  );
}

function SummaryTable({
  rows,
}: {
  rows: Array<{ label: string; value: string | number }>;
}) {
  return (
    <table
      style={{
        borderCollapse: "collapse",
        width: "100%",
        maxWidth: "48rem",
      }}
    >
      <tbody>
        {rows.map((row) => (
          <tr key={row.label}>
            <th
              style={{
                textAlign: "left",
                border: "1px solid #ccc",
                padding: "0.5rem",
                width: "16rem",
              }}
            >
              {row.label}
            </th>
            <td
              style={{
                border: "1px solid #ccc",
                padding: "0.5rem",
              }}
            >
              {row.value}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default function AnalysisReportPage() {
  const { id } = useParams();
  const [overview, setOverview] = useState<AnalysisOverviewResponse | null>(null);
  const [delta, setDelta] = useState<AnalysisDeltaSummaryResponse | null>(null);
  const [audit, setAudit] = useState<AnalysisAuditResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadReport = useCallback(async () => {
    if (!id) return;

    setError(null);

    try {
      const overviewResult = await getAnalysisOverview(id);
      setOverview(overviewResult);

      if (overviewResult.previous_analysis_id) {
        const deltaResult = await getAnalysisDeltaSummary(id);
        setDelta(deltaResult);
      } else {
        setDelta(null);
      }

      const auditResult = await getAnalysisAudit(id);
      setAudit(auditResult);
    } catch (err) {
      setError((err as Error).message);
    }
  }, [id]);

  useEffect(() => {
    loadReport();
  }, [loadReport]);

  if (error) {
    return (
      <ErrorState
        title="Could not load analysis report"
        message={error}
        onRetry={loadReport}
        retryLabel="Retry Load"
      />
    );
  }

  if (!overview || !audit) {
    return <LoadingState message="Loading analysis report..." />;
  }

  return (
    <main style={{ padding: "2rem", fontFamily: "sans-serif", maxWidth: "72rem" }}>
      <h1>Analysis Report</h1>

      <p>
        <Link to={`/analyses/${overview.analysis_id}`}>Back to Analysis Overview</Link>
      </p>

      <p>
        <button type="button" onClick={() => window.print()}>
          Print / Save PDF
        </button>
      </p>

      <ReportSection title="Report Header">
        <SummaryTable
          rows={[
            { label: "Analysis ID", value: overview.analysis_id },
            { label: "Customer", value: overview.customer_name },
            { label: "Environment", value: overview.environment_name },
            { label: "Status", value: formatStatusLabel(overview.overall_status) },
            { label: "Analysis Date", value: formatUnixSeconds(overview.analysis_date) },
            { label: "Started", value: formatUnixSeconds(overview.started_utc) },
            { label: "Completed", value: formatUnixSeconds(overview.completed_utc) },
            { label: "Duration (ms)", value: overview.duration_ms ?? "N/A" },
            { label: "Previous Analysis", value: overview.previous_analysis_id ?? "N/A" },
            { label: "Stale Reason", value: overview.stale_reason ?? "N/A" },
            {
              label: "Stale Detected",
              value: overview.stale_detected_utc
                ? formatUnixSeconds(overview.stale_detected_utc)
                : "N/A",
            },
          ]}
        />
      </ReportSection>

      <ReportSection title="Summary">
        <SummaryTable
          rows={[
            { label: "Applies", value: overview.summary.applies_count },
            { label: "Requires Review", value: overview.summary.review_required_count },
            { label: "Unknown", value: overview.summary.unknown_count },
            { label: "Blocked", value: overview.summary.blocked_count },
          ]}
        />
      </ReportSection>

      {overview.top_risks.length > 0 && (
        <ReportSection title="Top Risks">
          <ul>
            {overview.top_risks.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </ReportSection>
      )}

      {overview.top_actions.length > 0 && (
        <ReportSection title="Top Actions">
          <ul>
            {overview.top_actions.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </ReportSection>
      )}

      {overview.assumptions.length > 0 && (
        <ReportSection title="Assumptions">
          <ul>
            {overview.assumptions.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </ReportSection>
      )}

      {overview.missing_inputs.length > 0 && (
        <ReportSection title="Missing Inputs">
          <ul>
            {overview.missing_inputs.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </ReportSection>
      )}

      {overview.derived_risks.length > 0 && (
        <ReportSection title="Derived Risks">
          <ul>
            {overview.derived_risks.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </ReportSection>
      )}

      {delta && (
        <ReportSection title="Delta Summary">
          <SummaryTable
            rows={[
              { label: "Previous Analysis", value: delta.previous_analysis_id },
              { label: "Current Analysis", value: delta.current_analysis_id },
              { label: "New Findings", value: delta.new_findings_count },
              { label: "Resolved Findings", value: delta.resolved_findings_count },
              { label: "Updated Findings", value: delta.updated_findings_count },
              { label: "Unchanged Findings", value: delta.unchanged_findings_count },
              { label: "New KB Articles", value: delta.new_kb_articles_count },
              { label: "Updated KB Articles", value: delta.updated_kb_articles_count },
            ]}
          />

          {delta.applications_impacted.length > 0 && (
            <>
              <h3>Applications Impacted</h3>
              <ul>
                {delta.applications_impacted.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </>
          )}

          <h3>Delta Notes</h3>
          <ul>
            {delta.summary_lines.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </ReportSection>
      )}

      <ReportSection title="Applications">
        <table
          style={{
            borderCollapse: "collapse",
            width: "100%",
          }}
        >
          <thead>
            <tr>
              <th style={{ border: "1px solid #ccc", padding: "0.5rem", textAlign: "left" }}>
                Application
              </th>
              <th style={{ border: "1px solid #ccc", padding: "0.5rem", textAlign: "left" }}>
                Status
              </th>
              <th style={{ border: "1px solid #ccc", padding: "0.5rem", textAlign: "left" }}>
                Current Version
              </th>
              <th style={{ border: "1px solid #ccc", padding: "0.5rem", textAlign: "left" }}>
                Target Version
              </th>
              <th style={{ border: "1px solid #ccc", padding: "0.5rem", textAlign: "left" }}>
                Findings
              </th>
            </tr>
          </thead>
          <tbody>
            {overview.applications.map((app) => (
              <tr key={app.analysis_application_id}>
                <td style={{ border: "1px solid #ccc", padding: "0.5rem" }}>
                  {app.application_name}
                </td>
                <td style={{ border: "1px solid #ccc", padding: "0.5rem" }}>
                  {formatStatusLabel(app.status)}
                </td>
                <td style={{ border: "1px solid #ccc", padding: "0.5rem" }}>
                  {app.current_version}
                </td>
                <td style={{ border: "1px solid #ccc", padding: "0.5rem" }}>
                  {app.target_version}
                </td>
                <td style={{ border: "1px solid #ccc", padding: "0.5rem" }}>
                  {app.findings_count}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </ReportSection>

      <ReportSection title="Audit and Lineage">
        <h3>Lineage Chain</h3>
        <ul>
          {audit.lineage.map((node) => (
            <li key={node.analysis_id}>
              {node.analysis_id} | Status: {formatStatusLabel(node.overall_status)} | Started:{" "}
              {formatUnixSeconds(node.started_utc)} | Completed:{" "}
              {formatUnixSeconds(node.completed_utc)}
            </li>
          ))}
        </ul>

        <h3>State Transitions</h3>
        <ul>
          {audit.transitions.map((transition) => (
            <li key={transition.state_transition_id}>
              {transition.analysis_id} | {transition.previous_state ?? "NONE"} -&gt;{" "}
              {transition.new_state} | Trigger: {transition.trigger_event} | User:{" "}
              {transition.user_id ?? "system"} | At:{" "}
              {formatUnixSeconds(transition.transition_utc)}
            </li>
          ))}
        </ul>
      </ReportSection>
    </main>
  );
}