import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";
import StatusBanner from "../components/StatusBanner";
import StatusHelp from "../components/StatusHelp";
import { formatStatusLabel } from "../utils/status";
import {
  getAnalysisApplicationDetail,
  type AnalysisApplicationDetailResponse,
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

export default function ApplicationReportPage() {
  const { id, applicationId } = useParams();
  const [data, setData] = useState<AnalysisApplicationDetailResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadReport = useCallback(async () => {
    if (!id || !applicationId) return;

    setError(null);

    try {
      const result = await getAnalysisApplicationDetail(id, applicationId);
      setData(result);
    } catch (err) {
      setError((err as Error).message);
    }
  }, [id, applicationId]);

  useEffect(() => {
    loadReport();
  }, [loadReport]);

  if (error) {
    return (
      <ErrorState
        title="Could not load application report"
        message={error}
        onRetry={loadReport}
        retryLabel="Retry Load"
      />
    );
  }

  if (!data) {
    return <LoadingState message="Loading application report..." />;
  }

  return (
    <main style={{ padding: "2rem", fontFamily: "sans-serif", maxWidth: "72rem" }}>
      <h1>Application Report</h1>

      <p>
        <Link to={`/analyses/${id}/applications/${applicationId}`}>Back to Application Detail</Link>
      </p>

      <p>
        <button type="button" onClick={() => window.print()}>
          Print / Save PDF
        </button>
      </p>

      <ReportSection title="Report Header">
        <SummaryTable
          rows={[
            { label: "Analysis ID", value: id ?? "" },
            { label: "Application ID", value: data.analysis_application_id },
            { label: "Application Name", value: data.application_name },
            { label: "Status", value: formatStatusLabel(data.application_status) },
            { label: "Current Version", value: data.current_version },
            { label: "Target Version", value: data.target_version },
            { label: "Findings Count", value: data.findings.length },
          ]}
        />
      </ReportSection>

      <ReportSection title="Application Status">
        <p>Status: {formatStatusLabel(data.application_status)}</p>
        <StatusHelp status={data.application_status} />
        <StatusBanner status={data.application_status} />
      </ReportSection>

      <ReportSection title="Findings">
        {data.findings.length === 0 ? (
          <p>No findings available for this application.</p>
        ) : (
          <table
            style={{
              borderCollapse: "collapse",
              width: "100%",
            }}
          >
            <thead>
              <tr>
                <th style={{ border: "1px solid #ccc", padding: "0.5rem", textAlign: "left" }}>
                  Finding ID
                </th>
                <th style={{ border: "1px solid #ccc", padding: "0.5rem", textAlign: "left" }}>
                  Status
                </th>
                <th style={{ border: "1px solid #ccc", padding: "0.5rem", textAlign: "left" }}>
                  Severity
                </th>
                <th style={{ border: "1px solid #ccc", padding: "0.5rem", textAlign: "left" }}>
                  Change Taxonomy
                </th>
                <th style={{ border: "1px solid #ccc", padding: "0.5rem", textAlign: "left" }}>
                  Headline
                </th>
                <th style={{ border: "1px solid #ccc", padding: "0.5rem", textAlign: "left" }}>
                  KB Reference
                </th>
                <th style={{ border: "1px solid #ccc", padding: "0.5rem", textAlign: "left" }}>
                  Recommended Action
                </th>
              </tr>
            </thead>
            <tbody>
              {data.findings.map((finding) => (
                <tr key={finding.finding_id}>
                  <td style={{ border: "1px solid #ccc", padding: "0.5rem" }}>
                    {finding.finding_id}
                  </td>
                  <td style={{ border: "1px solid #ccc", padding: "0.5rem" }}>
                    {formatStatusLabel(finding.status)}
                  </td>
                  <td style={{ border: "1px solid #ccc", padding: "0.5rem" }}>
                    {finding.severity}
                  </td>
                  <td style={{ border: "1px solid #ccc", padding: "0.5rem" }}>
                    {finding.change_taxonomy}
                  </td>
                  <td style={{ border: "1px solid #ccc", padding: "0.5rem" }}>
                    {finding.headline}
                  </td>
                  <td style={{ border: "1px solid #ccc", padding: "0.5rem" }}>
                    {finding.kb_reference}
                  </td>
                  <td style={{ border: "1px solid #ccc", padding: "0.5rem" }}>
                    {finding.recommended_action ?? "N/A"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </ReportSection>
    </main>
  );
}