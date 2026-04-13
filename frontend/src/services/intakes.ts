const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

export type IntakeCreateRequest = {
  customer_name: string;
  environment_name: string;
  environment_type: "DEV" | "TEST" | "PROD";
};

export type IntakeCreateResponse = {
  intake_id: string;
  status: string;
  created_utc: number;
};

export type IntakeDetailResponse = {
  intake_id: string;
  status: string;
  customer_name: string;
  environment_name: string;
  environment_type: string;
  applications: unknown[];
};

export async function createIntake(
  payload: IntakeCreateRequest,
): Promise<IntakeCreateResponse> {
  const response = await fetch(`${API_BASE_URL}/intakes`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`POST /intakes failed with status ${response.status}`);
  }

  return response.json() as Promise<IntakeCreateResponse>;
}

export async function getIntake(id: string): Promise<IntakeDetailResponse> {
  const response = await fetch(`${API_BASE_URL}/intakes/${id}`);
  if (!response.ok) {
    throw new Error(`GET /intakes/${id} failed with status ${response.status}`);
  }
  return response.json() as Promise<IntakeDetailResponse>;
}