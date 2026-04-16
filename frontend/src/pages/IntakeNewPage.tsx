import { useState } from "react";
import { useNavigate } from "react-router-dom";

import ErrorState from "../components/ErrorState";
import { canManageIntakes, getCurrentRole } from "../auth/role";
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
}

function WhyWeAsk({
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
        fontStyle: "italic",
        color: "#444",
      }}
    >
      Why we ask: {children}
    </p>
  );
}

export default function IntakeNewPage() {
  const navigate = useNavigate();
  const currentRole = getCurrentRole();

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

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
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

  if (!canManageIntakes(currentRole)) {
    return (
      <ErrorState
        title="Permission denied"
        message="Analyst or admin role is required to create and run intakes."
      />
    );
  }

  return (
    <main style={{ padding: "2rem", fontFamily: "sans-serif", maxWidth: "56rem" }}>
      <h1>Create Intake</h1>

      <section style={{ marginBottom: "2rem" }}>
        <h2>Before you start</h2>
        <p>
          This form is meant to capture just enough environment, application, contact, and vendor
          KB context to produce a reviewable upgrade impact analysis.
        </p>
        <ul>
          <li>Use the environment and application names your team already recognizes.</li>
          <li>Enter the exact current and target versions when possible.</li>
          <li>List enabled modules as comma-separated values.</li>
          <li>Use a KB article that actually represents the change set being reviewed.</li>
        </ul>
      </section>

      <form onSubmit={handleSubmit}>
        <h2>Environment</h2>
        <HelperText>
          Start with the environment this upgrade decision is actually about. Keep names practical
          and recognizable to both technical and business reviewers.
        </HelperText>
        <WhyWeAsk>
          environment identity drives analysis context, review expectations, and later staleness /
          refresh interpretation.
        </WhyWeAsk>

        <div style={{ marginBottom: "0.75rem" }}>
          <label>Customer Name </label>
          <input value={customerName} onChange={(e) => setCustomerName(e.target.value)} />
          <HelperText>
            Example: Acme Health, Northwind Distribution, City Utilities.
          </HelperText>
        </div>

        <div style={{ marginBottom: "0.75rem" }}>
          <label>Environment Name </label>
          <input value={environmentName} onChange={(e) => setEnvironmentName(e.target.value)} />
          <HelperText>
            Example: Production, UAT Wave 2, Payroll Test, AP Validation Sandbox.
          </HelperText>
        </div>

        <div style={{ marginBottom: "1rem" }}>
          <label>Environment Type </label>
          <select
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
        </div>

        <h2>Application</h2>
        <HelperText>
          Capture the application and version range as your team would describe them in an upgrade
          review or cutover discussion.
        </HelperText>
        <WhyWeAsk>
          version and module scope determine which findings may apply and which missing inputs will
          matter later.
        </WhyWeAsk>

        <div style={{ marginBottom: "0.75rem" }}>
          <label>Application Name </label>
          <input value={applicationName} onChange={(e) => setApplicationName(e.target.value)} />
          <HelperText>
            Use the specific application or functional area, not just the broad platform name.
          </HelperText>
        </div>

        <div style={{ marginBottom: "0.75rem" }}>
          <label>Product Line </label>
          <input value={productLine} onChange={(e) => setProductLine(e.target.value)} />
        </div>

        <div style={{ marginBottom: "0.75rem" }}>
          <label>Current Version </label>
          <input value={currentVersion} onChange={(e) => setCurrentVersion(e.target.value)} />
        </div>

        <div style={{ marginBottom: "0.75rem" }}>
          <label>Target Version </label>
          <input value={targetVersion} onChange={(e) => setTargetVersion(e.target.value)} />
        </div>

        <div style={{ marginBottom: "1rem" }}>
          <label>Modules Enabled </label>
          <input value={modulesEnabled} onChange={(e) => setModulesEnabled(e.target.value)} />
          <HelperText>
            Enter modules as comma-separated values, for example: Invoice Processing, Payment
            Scheduling, Supplier Management.
          </HelperText>
        </div>

        <h2>Contacts</h2>
        <HelperText>
          Add the people most likely to confirm whether a change is real, acceptable, or risky in
          this environment.
        </HelperText>
        <WhyWeAsk>
          contact context helps explain who can resolve unknowns, validate assumptions, and review
          findings when the system cannot fully infer customer-specific behavior.
        </WhyWeAsk>

        <div style={{ marginBottom: "0.75rem" }}>
          <label>Technical Contact Name </label>
          <input
            value={technicalContactName}
            onChange={(e) => setTechnicalContactName(e.target.value)}
          />
        </div>

        <div style={{ marginBottom: "0.75rem" }}>
          <label>Technical Contact Email </label>
          <input
            value={technicalContactEmail}
            onChange={(e) => setTechnicalContactEmail(e.target.value)}
          />
        </div>

        <div style={{ marginBottom: "0.75rem" }}>
          <label>Business Contact Name </label>
          <input
            value={businessContactName}
            onChange={(e) => setBusinessContactName(e.target.value)}
          />
        </div>

        <div style={{ marginBottom: "1rem" }}>
          <label>Business Contact Email </label>
          <input
            value={businessContactEmail}
            onChange={(e) => setBusinessContactEmail(e.target.value)}
          />
        </div>

        <h2>KB Document</h2>
        <HelperText>
          Use the vendor article that best represents the change set under review. Titles and links
          should be good enough for a reviewer to verify provenance later.
        </HelperText>
        <WhyWeAsk>
          visible source evidence is part of the system’s trust model. If provenance is weak here,
          the downstream report gets weaker too.
        </WhyWeAsk>

        <div style={{ marginBottom: "0.75rem" }}>
          <label>KB Article Number </label>
          <input value={kbArticleNumber} onChange={(e) => setKbArticleNumber(e.target.value)} />
        </div>

        <div style={{ marginBottom: "0.75rem" }}>
          <label>KB Title </label>
          <input value={kbTitle} onChange={(e) => setKbTitle(e.target.value)} />
        </div>

        <div style={{ marginBottom: "0.75rem" }}>
          <label>Publication Date </label>
          <input
            value={kbPublicationDate}
            onChange={(e) => setKbPublicationDate(e.target.value)}
          />
          <HelperText>Use ISO format when possible: YYYY-MM-DD.</HelperText>
        </div>

        <div style={{ marginBottom: "1rem" }}>
          <label>Source Link </label>
          <input value={kbSourceLink} onChange={(e) => setKbSourceLink(e.target.value)} />
        </div>

        <div style={{ marginTop: "1rem" }}>
          <button type="submit" disabled={submitting}>
            {submitting ? "Submitting..." : "Create, Validate, and Run Analysis"}
          </button>
        </div>
      </form>

      {error && (
        <section style={{ marginTop: "2rem" }}>
          <h2>Submission Error</h2>
          <p>{error}</p>
          <p>
            Review the current values, correct anything incomplete or malformed, and retry the
            intake flow.
          </p>
        </section>
      )}

      {missingFields.length > 0 && (
        <section style={{ marginTop: "2rem" }}>
          <h2>Blocked: Required intake details are still missing</h2>
          <p>
            The system could not validate this intake yet. Fill the missing items below, then retry
            the analysis flow.
          </p>
          <ul>
            {missingFields.map((field) => (
              <li key={field}>{field}</li>
            ))}
          </ul>
        </section>
      )}

      {warnings.length > 0 && (
        <section style={{ marginTop: "2rem" }}>
          <h2>Warnings</h2>
          <p>
            These warnings do not always block analysis, but they usually mean a reviewer will have
            less context later.
          </p>
          <ul>
            {warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </section>
      )}
    </main>
  );
}