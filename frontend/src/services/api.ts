import { getCurrentRole } from "../auth/role";

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

function buildHeaders(extraHeaders?: HeadersInit): HeadersInit {
  return {
    "X-User-Role": getCurrentRole(),
    ...extraHeaders,
  };
}

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: buildHeaders(),
  });

  if (!response.ok) {
    let detail = "";
    try {
      detail = await response.text();
    } catch {
      detail = "";
    }
    throw new Error(
      `GET ${path} failed with status ${response.status}${detail ? `: ${detail}` : ""}`,
    );
  }

  return response.json() as Promise<T>;
}

export async function apiPost<TResponse, TRequest>(
  path: string,
  payload: TRequest,
): Promise<TResponse> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      headers: buildHeaders({
        "Content-Type": "application/json",
      }),
      body: JSON.stringify(payload),
    });
  } catch {
    throw new Error(
      `POST ${path} could not reach the backend. Check that the API is running and reachable at ${API_BASE_URL}.`,
    );
  }

  if (!response.ok) {
    let detail = "";
    try {
      detail = await response.text();
    } catch {
      detail = "";
    }
    throw new Error(
      `POST ${path} failed with status ${response.status}${detail ? `: ${detail}` : ""}`,
    );
  }

  return response.json() as Promise<TResponse>;
}

export async function apiPatch<TResponse, TRequest>(
  path: string,
  payload: TRequest,
): Promise<TResponse> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: "PATCH",
      headers: buildHeaders({
        "Content-Type": "application/json",
      }),
      body: JSON.stringify(payload),
    });
  } catch {
    throw new Error(
      `PATCH ${path} could not reach the backend. Check that the API is running and reachable at ${API_BASE_URL}.`,
    );
  }

  if (!response.ok) {
    let detail = "";
    try {
      detail = await response.text();
    } catch {
      detail = "";
    }
    throw new Error(
      `PATCH ${path} failed with status ${response.status}${detail ? `: ${detail}` : ""}`,
    );
  }

  return response.json() as Promise<TResponse>;
}