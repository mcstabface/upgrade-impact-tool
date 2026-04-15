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
    <main style={{ padding: "2rem", fontFamily: "sans-serif" }}>
      <h1>Create Intake</h1>

      <form onSubmit={handleSubmit}>
        <h2>Environment</h2>

        <div>
          <label>Customer Name </label>
          <input value={customerName} onChange={(e) => setCustomerName(e.target.value)} />
        </div>

        <div>
          <label>Environment Name </label>
          <input value={environmentName} onChange={(e) => setEnvironmentName(e.target.value)} />
        </div>

        <div>
          <label>Environment Type </label>
          <select
            value={environmentType}
            onChange={(e) => setEnvironmentType(e.target.value as "DEV" | "TEST" | "PROD")}
          >
            <option value="DEV">DEV</option>
            <option value="TEST">TEST</option>
            <option value="PROD">PROD</option>
          </select>
        </div>

        <h2>Application</h2>

        <div>
          <label>Application Name </label>
          <input value={applicationName} onChange={(e) => setApplicationName(e.target.value)} />
        </div>

        <div>
          <label>Product Line </label>
          <input value={productLine} onChange={(e) => setProductLine(e.target.value)} />
        </div>

        <div>
          <label>Current Version </label>
          <input value={currentVersion} onChange={(e) => setCurrentVersion(e.target.value)} />
        </div>

        <div>
          <label>Target Version </label>
          <input value={targetVersion} onChange={(e) => setTargetVersion(e.target.value)} />
        </div>

        <div>
          <label>Modules Enabled </label>
          <input value={modulesEnabled} onChange={(e) => setModulesEnabled(e.target.value)} />
        </div>

        <h2>Contacts</h2>

        <div>
          <label>Technical Contact Name </label>
          <input
            value={technicalContactName}
            onChange={(e) => setTechnicalContactName(e.target.value)}
          />
        </div>

        <div>
          <label>Technical Contact Email </label>
          <input
            value={technicalContactEmail}
            onChange={(e) => setTechnicalContactEmail(e.target.value)}
          />
        </div>

        <div>
          <label>Business Contact Name </label>
          <input
            value={businessContactName}
            onChange={(e) => setBusinessContactName(e.target.value)}
          />
        </div>

        <div>
          <label>Business Contact Email </label>
          <input
            value={businessContactEmail}
            onChange={(e) => setBusinessContactEmail(e.target.value)}
          />
        </div>

        <h2>KB Document</h2>

        <div>
          <label>KB Article Number </label>
          <input value={kbArticleNumber} onChange={(e) => setKbArticleNumber(e.target.value)} />
        </div>

        <div>
          <label>KB Title </label>
          <input value={kbTitle} onChange={(e) => setKbTitle(e.target.value)} />
        </div>

        <div>
          <label>Publication Date </label>
          <input
            value={kbPublicationDate}
            onChange={(e) => setKbPublicationDate(e.target.value)}
          />
        </div>

        <div>
          <label>Source Link </label>
          <input value={kbSourceLink} onChange={(e) => setKbSourceLink(e.target.value)} />
        </div>

        <div style={{ marginTop: "1rem" }}>
          <button type="submit" disabled={submitting}>
            {submitting ? "Submitting..." : "Create, Validate, and Run Analysis"}
          </button>
        </div>
      </form>

      {error && <p>Error: {error}</p>}

      {missingFields.length > 0 && (
        <section>
          <h2>Missing Required Fields</h2>
          <ul>
            {missingFields.map((field) => (
              <li key={field}>{field}</li>
            ))}
          </ul>
        </section>
      )}

      {warnings.length > 0 && (
        <section>
          <h2>Warnings</h2>
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