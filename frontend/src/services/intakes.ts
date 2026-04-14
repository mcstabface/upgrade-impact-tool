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

export type IntakeUpdateRequest = {
  applications?: {
    application_name: string;
    product_line: string;
    current_version: string;
    target_version: string;
    modules_enabled: string[];
  }[];
  primary_technical_contact?: {
    name: string;
    email?: string | null;
  };
  primary_business_contact?: {
    name: string;
    email?: string | null;
  };
  environment_count?: number;
  environment_classification?: string[];
  upgrade_sequence?: string[];
  vendor_kb_documents?: {
    article_number: string;
    title: string;
    publication_date: string;
    source_link: string;
  }[];
};

export type IntakeValidateResponse = {
  intake_id: string;
  status: string;
  completeness_score: number;
  missing_required_fields: string[];
  warnings: string[];
};

export type StartAnalysisResponse = {
  analysis_id: string;
  status: string;
  started_utc: number;
};

export async function updateIntake(id: string, payload: IntakeUpdateRequest) {
  const response = await fetch(`${API_BASE_URL}/intakes/${id}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`PATCH /intakes/${id} failed with status ${response.status}`);
  }

  return response.json();
}

export async function validateIntake(id: string): Promise<IntakeValidateResponse> {
  const response = await fetch(`${API_BASE_URL}/intakes/${id}/validate`, {
    method: "POST",
  });

  if (!response.ok) {
    throw new Error(`POST /intakes/${id}/validate failed with status ${response.status}`);
  }

  return response.json() as Promise<IntakeValidateResponse>;
}

export async function startAnalysis(id: string): Promise<StartAnalysisResponse> {
  const response = await fetch(`${API_BASE_URL}/intakes/${id}/analyses`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ run_mode: "STANDARD" }),
  });

  if (!response.ok) {
    throw new Error(`POST /intakes/${id}/analyses failed with status ${response.status}`);
  }

  return response.json() as Promise<StartAnalysisResponse>;
}