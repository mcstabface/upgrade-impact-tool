import { getCurrentRole } from "../auth/role";

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

function buildHeaders(extraHeaders?: HeadersInit): HeadersInit {
  return {
    "X-User-Role": getCurrentRole(),
    ...extraHeaders,
  };
}

async function buildErrorMessage(response: Response, fallbackMessage: string): Promise<string> {
  try {
    const responseText = await response.text();

    if (!responseText) {
      return fallbackMessage;
    }

    const parsed = JSON.parse(responseText) as {
      message?: string;
      recovery_guidance?: string;
      detail?: string;
      error_class?: string;
    };

    const message = parsed.message ?? parsed.detail ?? fallbackMessage;
    const recoveryGuidance = parsed.recovery_guidance;

    if (recoveryGuidance) {
      return `${message}\nRecovery: ${recoveryGuidance}`;
    }

    return message;
  } catch {
    return fallbackMessage;
  }
}

export async function apiGet<T>(path: string): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      headers: buildHeaders(),
    });
  } catch {
    throw new Error(
      `Could not reach the backend.\nRecovery: Check that the API is running and reachable at ${API_BASE_URL}, then retry the action.`,
    );
  }

  if (!response.ok) {
    const fallbackMessage = `Request failed with status ${response.status}.`;
    throw new Error(await buildErrorMessage(response, fallbackMessage));
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
      `Could not reach the backend.\nRecovery: Check that the API is running and reachable at ${API_BASE_URL}, then retry the action.`,
    );
  }

  if (!response.ok) {
    const fallbackMessage = `Request failed with status ${response.status}.`;
    throw new Error(await buildErrorMessage(response, fallbackMessage));
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
      `Could not reach the backend.\nRecovery: Check that the API is running and reachable at ${API_BASE_URL}, then retry the action.`,
    );
  }

  if (!response.ok) {
    const fallbackMessage = `Request failed with status ${response.status}.`;
    throw new Error(await buildErrorMessage(response, fallbackMessage));
  }

  return response.json() as Promise<TResponse>;
}