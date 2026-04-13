import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";
import { getIntake, type IntakeDetailResponse } from "../services/intakes";

export default function IntakeDetailPage() {
  const { id } = useParams();
  const [data, setData] = useState<IntakeDetailResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    getIntake(id).then(setData).catch((err: Error) => setError(err.message));
  }, [id]);

  if (error) return <ErrorState message={error} />;
  if (!data) return <LoadingState />;

  return (
    <main style={{ padding: "2rem", fontFamily: "sans-serif" }}>
      <h1>Intake Detail</h1>
      <p>Intake ID: {data.intake_id}</p>
      <p>Status: {data.status}</p>
      <p>Customer: {data.customer_name}</p>
      <p>Environment: {data.environment_name}</p>
      <p>Environment Type: {data.environment_type}</p>
      <p>Applications: {data.applications.length}</p>
    </main>
  );
}