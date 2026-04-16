import { useState } from "react";
import { useNavigate } from "react-router-dom";

import AppShell from "../components/layout/AppShell";
import ErrorState from "../components/ErrorState";
import Card from "../components/ui/Card";
import ButtonLink from "../components/ui/ButtonLink";
import { canManageIntakes, type UserRole } from "../auth/role";
import { useCurrentRole } from "../auth/AuthContext";
import {
  createIntake,
  startAnalysis,
  updateIntake,
  validateIntake,
} from "../services/intakes";

function HelperText({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <p
      style={{
        marginTop: "0.25rem",
        marginBottom: "0.75rem",
        maxWidth: "48rem",
        color: "#333",
      }}
    >
      {children}
    </p>
  );
}function HelperText({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <p
      style={{
        marginTop: "0.35rem",
        marginBottom: 0,
        maxWidth: "48rem",
        color: "var(--text-secondary)",
        fontSize: "0.95rem",
      }}
    >
      {children}
    </p>
  );
}

function WhyWeAsk({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <p
      style={{
        marginTop: "0.35rem",
        marginBottom: 0,
        maxWidth: "48rem",
        fontStyle: "italic",
        color: "var(--text-muted)",
        fontSize: "0.92rem",
      }}
    >
      Why we ask: {children}
    </p>
  );
}

function GuidanceBlock({
  title,
  body,
  lines,
}: {
  title: string;
  body: string;
  lines: string[];
}) {
  return (
    <Card title={title} muted>
      <p style={{ color: "var(--text-secondary)" }}>{body}</p>
      <ul className="ui-list ui-list--compact">
        {lines.map((line) => (
          <li key={line}>{line}</li>
        ))}
      </ul>
    </Card>
  );
}

const SAMPLE_PREP_CHECKLIST = [
  "Customer and environment names match what reviewers already use internally.",
  "Current and target versions are exact, not approximate.",
  "Enabled modules are listed in comma-separated form.",
  "Technical and business contacts are the people who can actually clear unknowns.",
  "The KB article number, title, date, and source link point to the real vendor change set.",
];

const SAMPLE_INTAKE_TEMPLATE_LINES = [
  "Customer Name: Acme Health",
  "Environment Name: Production Wave 2",
  "Environment Type: PROD",
  "Application Name: Accounts Payable",
  "Product Line: PeopleSoft",
  "Current Version: 9.2.40",
  "Target Version: 9.2.42",
  "Modules Enabled: Invoice Processing, Payment Scheduling, Supplier Management",
  "Technical Contact: Jane Admin <jane.admin@example.com>",
  "Business Contact: Bob Business <bob.business@example.com>",
  "KB Article Number: KB-4000001.1",
  "KB Title: AP Validation Changes for 9.2.42",
  "Publication Date: 2026-04-12",
  "Source Link: https://example.com/kb/4000001-1",
];

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

export default function IntakeNewPage() {
  const navigate = useNavigate();

  const [customerName, setCustomerName] = useState("Acme Health");
  const [environmentName, setEnvironmentName] = useState("Production Wave 2");
  const [environmentType, setEnvironmentType] = useState<"DEV" | "TEST" | "PROD">("PROD");

  const [applicationName, setApplicationName] = useState("Accounts Payable");
  const [productLine, setProductLine] = useState("PeopleSoft");
  const [currentVersion, setCurrentVersion] = useState("9.2.40");
  const [targetVersion, setTargetVersion] = useState("9.2.42");
  const [modulesEnabled, setModulesEnabled] = useState("Invoice Processing, Payment Scheduling");

  const [technicalContactName, setTechnicalContactName] = useState("Jane Admin");
  const [technicalContactEmail, setTechnicalContactEmail] = useState("jane.admin@example.com");
  const [businessContactName, setBusinessContactName] = useState("Bob Business");
  const [businessContactEmail, setBusinessContactEmail] = useState("bob.business@example.com");

  const [kbArticleNumber, setKbArticleNumber] = useState("KB-4000001.1");
  const [kbTitle, setKbTitle] = useState("AP Validation Changes for 9.2.42");
  const [kbPublicationDate, setKbPublicationDate] = useState("2026-04-12");
  const [kbSourceLink, setKbSourceLink] = useState("https://example.com/kb/4000001-1");

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [missingFields, setMissingFields] = useState<string[]>([]);
  const [copyMessage, setCopyMessage] = useState<string | null>(null);

  const currentRole: UserRole = useCurrentRole();

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();

    if (!canManageIntakes(currentRole)) {
      setError(
        `Current role ${currentRole} is not permitted to create intakes.\nRecovery: Sign in with an ANALYST or ADMIN account, then retry the intake flow.`,
      );
      setSubmitting(false);
      return;
    }

    setSubmitting(true);
    setError(null);
    setWarnings([]);
    setMissingFields([]);

    try {
      const draft = await createIntake({
        customer_name: customerName,
        environment_name: environmentName,
        environment_type: environmentType,
      });

      const parsedModules = modulesEnabled
        .split(",")
        .map((value) => value.trim())
        .filter(Boolean);

      await updateIntake(draft.intake_id, {
        applications: [
          {
            application_name: applicationName,
            product_line: productLine,
            current_version: currentVersion,
            target_version: targetVersion,
            modules_enabled: parsedModules,
          },
        ],
        primary_technical_contact: {
          name: technicalContactName,
          email: technicalContactEmail,
        },
        primary_business_contact: {
          name: businessContactName,
          email: businessContactEmail,
        },
        environment_count: 1,
        environment_classification: [environmentType],
        upgrade_sequence: [environmentType],
        vendor_kb_documents: [
          {
            article_number: kbArticleNumber,
            title: kbTitle,
            publication_date: kbPublicationDate,
            source_link: kbSourceLink,
          },
        ],
      });

      const validation = await validateIntake(draft.intake_id);

      if (validation.status === "BLOCKED") {
        setMissingFields(validation.missing_required_fields);
        setWarnings(validation.warnings);
        setSubmitting(false);
        return;
      }

      setWarnings(validation.warnings);

      const analysis = await startAnalysis(draft.intake_id);
      navigate(`/analyses/${analysis.analysis_id}`);
    } catch (err) {
      setError((err as Error).message);
      setSubmitting(false);
      return;
    }

    setSubmitting(false);
  }

  async function handleCopyTemplate() {
    try {
      await navigator.clipboard.writeText(SAMPLE_INTAKE_TEMPLATE_LINES.join("\n"));
      setCopyMessage("Sample intake template copied.");
    } catch {
      setCopyMessage("Could not copy the sample intake template.");
    }
  }

  if (!canManageIntakes(currentRole)) {
    return (
      <ErrorState
        title="Permission denied"
        message="Analyst or admin role is required to create and run intakes."
      />
    );
  }

  return (
    <AppShell
      title="Create Intake"
      subtitle="Capture the minimum environment, application, contact, and source evidence needed to produce a reviewable pilot analysis."
      actions={<ButtonLink to="/dashboard" variant="subtle">Back to Dashboard</ButtonLink>}
    >
      <div className="ui-stack">
        <Card title="Before you start" muted>
          <p style={{ color: "var(--text-secondary)" }}>
            This form is meant to capture just enough environment, application, contact, and vendor
            KB context to produce a reviewable upgrade impact analysis.
          </p>
          <ul className="ui-list ui-list--compact">
            <li>Use the environment and application names your team already recognizes.</li>
            <li>Enter the exact current and target versions when possible.</li>
            <li>List enabled modules as comma-separated values.</li>
            <li>Use a KB article that actually represents the change set being reviewed.</li>
          </ul>
        </Card>

        <GuidanceBlock
          title="Sample intake prep checklist"
          body="Use this quick checklist before you submit the intake. It reduces blocked validation and later unknown findings."
          lines={SAMPLE_PREP_CHECKLIST}
        />

        <Card title="Sample intake template" muted>
          <p style={{ color: "var(--text-secondary)" }}>
            This is a simple example of the level of detail the system expects. Use it as prep
            guidance, not as a replacement for real customer context.
          </p>
          <pre
            style={{
              whiteSpace: "pre-wrap",
              border: "1px solid var(--border-subtle)",
              borderRadius: "12px",
              padding: "0.9rem",
              backgroundColor: "var(--bg-surface)",
              overflowX: "auto",
            }}
          >
            {SAMPLE_INTAKE_TEMPLATE_LINES.join("\n")}
          </pre>
          <div style={{ marginTop: "1rem" }}>
            <button type="button" className="ui-button" onClick={handleCopyTemplate}>
              Copy Sample Template
            </button>
          </div>
          {copyMessage ? <p className="ui-status-note">{copyMessage}</p> : null}
        </Card>

        <form onSubmit={handleSubmit} className="ui-stack">
          <Card title="Environment">
            <p style={{ color: "var(--text-secondary)" }}>
              Start with the environment this upgrade decision is actually about. Keep names practical
              and recognizable to both technical and business reviewers.
            </p>
            <p style={{ color: "var(--text-muted)", fontStyle: "italic" }}>
              Why we ask: environment identity drives analysis context, review expectations, and
              later staleness / refresh interpretation.
            </p>

            <div className="ui-field-grid">
              <FieldBlock label="Customer Name">
                <input
                  className="ui-input"
                  value={customerName}
                  onChange={(e) => setCustomerName(e.target.value)}
                />
                <HelperText>
                  Example: Acme Health, Northwind Distribution, City Utilities.
                </HelperText>
              </FieldBlock>

              <FieldBlock label="Environment Name">
                <input
                  className="ui-input"
                  value={environmentName}
                  onChange={(e) => setEnvironmentName(e.target.value)}
                />
                <HelperText>
                  Example: Production, UAT Wave 2, Payroll Test, AP Validation Sandbox.
                </HelperText>
              </FieldBlock>

              <FieldBlock label="Environment Type">
                <select
                  className="ui-select"
                  value={environmentType}
                  onChange={(e) => setEnvironmentType(e.target.value as "DEV" | "TEST" | "PROD")}
                >
                  <option value="DEV">DEV</option>
                  <option value="TEST">TEST</option>
                  <option value="PROD">PROD</option>
                </select>
                <HelperText>
                  Choose the type that matches the real operating context for this analysis.
                </HelperText>
              </FieldBlock>
            </div>
          </Card>

          <Card title="Application">
            <p style={{ color: "var(--text-secondary)" }}>
              Capture the application and version range as your team would describe them in an upgrade
              review or cutover discussion.
            </p>
            <p style={{ color: "var(--text-muted)", fontStyle: "italic" }}>
              Why we ask: version and module scope determine which findings may apply and which
              missing inputs will matter later.
            </p>

            <div className="ui-field-grid">
              <FieldBlock label="Application Name">
                <input
                  className="ui-input"
                  value={applicationName}
                  onChange={(e) => setApplicationName(e.target.value)}
                />
                <HelperText>
                  Use the specific application or functional area, not just the broad platform name.
                </HelperText>
              </FieldBlock>

              <FieldBlock label="Product Line">
                <input
                  className="ui-input"
                  value={productLine}
                  onChange={(e) => setProductLine(e.target.value)}
                />
              </FieldBlock>

              <FieldBlock label="Current Version">
                <input
                  className="ui-input"
                  value={currentVersion}
                  onChange={(e) => setCurrentVersion(e.target.value)}
                />
              </FieldBlock>

              <FieldBlock label="Target Version">
                <input
                  className="ui-input"
                  value={targetVersion}
                  onChange={(e) => setTargetVersion(e.target.value)}
                />
              </FieldBlock>
            </div>

            <div style={{ marginTop: "1rem" }}>
              <FieldBlock label="Modules Enabled">
                <input
                  className="ui-input"
                  value={modulesEnabled}
                  onChange={(e) => setModulesEnabled(e.target.value)}
                />
                <HelperText>
                  Enter modules as comma-separated values, for example: Invoice Processing, Payment
                  Scheduling, Supplier Management.
                </HelperText>
              </FieldBlock>
            </div>
          </Card>

          <Card title="Contacts">
            <p style={{ color: "var(--text-secondary)" }}>
              Add the people most likely to confirm whether a change is real, acceptable, or risky in
              this environment.
            </p>
            <p style={{ color: "var(--text-muted)", fontStyle: "italic" }}>
              Why we ask: contact context helps explain who can resolve unknowns, validate
              assumptions, and review findings when the system cannot fully infer customer-specific
              behavior.
            </p>

            <div className="ui-field-grid">
              <FieldBlock label="Technical Contact Name">
                <input
                  className="ui-input"
                  value={technicalContactName}
                  onChange={(e) => setTechnicalContactName(e.target.value)}
                />
              </FieldBlock>

              <FieldBlock label="Technical Contact Email">
                <input
                  className="ui-input"
                  value={technicalContactEmail}
                  onChange={(e) => setTechnicalContactEmail(e.target.value)}
                />
              </FieldBlock>

              <FieldBlock label="Business Contact Name">
                <input
                  className="ui-input"
                  value={businessContactName}
                  onChange={(e) => setBusinessContactName(e.target.value)}
                />
              </FieldBlock>

              <FieldBlock label="Business Contact Email">
                <input
                  className="ui-input"
                  value={businessContactEmail}
                  onChange={(e) => setBusinessContactEmail(e.target.value)}
                />
              </FieldBlock>
            </div>
          </Card>

          <Card title="KB Document">
            <p style={{ color: "var(--text-secondary)" }}>
              Use the vendor article that best represents the change set under review. Titles and
              links should be good enough for a reviewer to verify provenance later.
            </p>
            <p style={{ color: "var(--text-muted)", fontStyle: "italic" }}>
              Why we ask: visible source evidence is part of the system’s trust model. If provenance
              is weak here, the downstream report gets weaker too.
            </p>

            <div className="ui-field-grid">
              <FieldBlock label="KB Article Number">
                <input
                  className="ui-input"
                  value={kbArticleNumber}
                  onChange={(e) => setKbArticleNumber(e.target.value)}
                />
              </FieldBlock>

              <FieldBlock label="KB Title">
                <input
                  className="ui-input"
                  value={kbTitle}
                  onChange={(e) => setKbTitle(e.target.value)}
                />
              </FieldBlock>

              <FieldBlock label="Publication Date">
                <input
                  className="ui-input"
                  value={kbPublicationDate}
                  onChange={(e) => setKbPublicationDate(e.target.value)}
                />
                <HelperText>Use ISO format when possible: YYYY-MM-DD.</HelperText>
              </FieldBlock>

              <FieldBlock label="Source Link">
                <input
                  className="ui-input"
                  value={kbSourceLink}
                  onChange={(e) => setKbSourceLink(e.target.value)}
                />
              </FieldBlock>
            </div>
          </Card>

          <Card muted>
            <div className="ui-inline-actions">
              <button type="submit" className="ui-button ui-button--primary" disabled={submitting}>
                {submitting ? "Submitting..." : "Create, Validate, and Run Analysis"}
              </button>
            </div>
          </Card>
        </form>

        {error ? (
          <Card title="Submission Error" tone="danger">
            <p>{error}</p>
            <p style={{ color: "var(--text-secondary)" }}>
              Review the current values, correct anything incomplete or malformed, and retry the
              intake flow.
            </p>
          </Card>
        ) : null}

        {missingFields.length > 0 ? (
          <Card title="Blocked: Required intake details are still missing" tone="warning">
            <p style={{ color: "var(--text-secondary)" }}>
              The system could not validate this intake yet. Fill the missing items below, then retry
              the analysis flow.
            </p>
            <ul className="ui-list ui-list--compact">
              {missingFields.map((field) => (
                <li key={field}>{field}</li>
              ))}
            </ul>
          </Card>
        ) : null}

        {warnings.length > 0 ? (
          <Card title="Warnings" tone="warning">
            <p style={{ color: "var(--text-secondary)" }}>
              These warnings do not always block analysis, but they usually mean a reviewer will have
              less context later.
            </p>
            <ul className="ui-list ui-list--compact">
              {warnings.map((warning) => (
                <li key={warning}>{warning}</li>
              ))}
            </ul>
          </Card>
        ) : null}
      </div>
    </AppShell>
  );
}