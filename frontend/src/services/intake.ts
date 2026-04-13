import { apiGet } from "./api";
import type { IntakeCreateResponse, IntakeRequest } from "../types/intake";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

export async function createIntake(
  payload: IntakeRequest,
): Promise<IntakeCreateResponse> {
  const response = await fetch(`${API_BASE_URL}/intake`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`POST /intake failed with status ${response.status}`);
  }

  return response.json() as Promise<IntakeCreateResponse>;
}

// keep import surface symmetrical with api service layer for now
export { apiGet };