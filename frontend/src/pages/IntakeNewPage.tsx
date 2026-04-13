import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { createIntake } from "../services/intakes";

export default function IntakeNewPage() {
  const navigate = useNavigate();
  const [customerName, setCustomerName] = useState("Acme Health");
  const [environmentName, setEnvironmentName] = useState("Production");
  const [environmentType, setEnvironmentType] = useState<"DEV" | "TEST" | "PROD">("PROD");
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    try {
      const result = await createIntake({
        customer_name: customerName,
        environment_name: environmentName,
        environment_type: environmentType,
      });
      navigate(`/intakes/${result.intake_id}`);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <main style={{ padding: "2rem", fontFamily: "sans-serif" }}>
      <h1>Create Intake</h1>
      <form onSubmit={handleSubmit}>
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
        <button type="submit">Create Draft</button>
      </form>
      {error && <p>Error: {error}</p>}
    </main>
  );
}