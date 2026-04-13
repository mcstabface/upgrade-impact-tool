export type CustomerEnvironmentType = "PRODUCTION" | "TEST" | "DEVELOPMENT";

export type CustomizationObjectType =
  | "WORKFLOW"
  | "REPORT"
  | "SCRIPT"
  | "EXTENSION"
  | "DATABASE_OBJECT";

export type IntegrationInterfaceType =
  | "API"
  | "BATCH"
  | "FILE"
  | "MESSAGE_QUEUE";

export type CriticalityLevel = "HIGH" | "MEDIUM" | "LOW";

export type JobType = "BATCH" | "REPORT" | "SCHEDULED_TASK";

export interface ContactInfo {
  name: string;
  email?: string | null;
}

export interface ModuleEnabled {
  module_name: string;
}

export interface ApplicationInScope {
  application_name: string;
  product_line: string;
  current_version: string;
  target_version: string;
  modules_enabled: ModuleEnabled[];
}

export interface VendorKnowledgeBaseDocument {
  article_number: string;
  title: string;
  publication_date: string;
  source_link: string;
}

export interface CustomizationItem {
  object_name: string;
  object_type: CustomizationObjectType;
  description?: string | null;
  owning_team?: string | null;
}

export interface IntegrationItem {
  integration_name: string;
  source_system: string;
  target_system: string;
  interface_type: IntegrationInterfaceType;
  schedule?: string | null;
  criticality?: CriticalityLevel | null;
}

export interface JobItem {
  job_name: string;
  job_type: JobType;
  schedule?: string | null;
  owner?: string | null;
}

export interface IntakeRequest {
  customer_name: string;
  environment_name: string;
  environment_type: CustomerEnvironmentType;
  primary_technical_contact: ContactInfo;
  primary_business_contact: ContactInfo;
  applications: ApplicationInScope[];
  environment_count: number;
  environment_classification: string[];
  upgrade_sequence?: string[] | null;
  vendor_kb_documents: VendorKnowledgeBaseDocument[];
  customizations?: CustomizationItem[] | null;
  integrations?: IntegrationItem[] | null;
  jobs?: JobItem[] | null;
}

export interface IntakeCreateResponse {
  analysis_id: string;
  analysis_status: string;
  warnings: string[];
  applications_in_scope: number;
  environment_count: number;
}