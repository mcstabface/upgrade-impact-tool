export function formatStatusLabel(status: string): string {
  switch (status) {
    case "APPLIES":
      return "Applies";
    case "UNKNOWN":
      return "Unknown";
    case "BLOCKED":
      return "Blocked";
    case "RESOLVED":
      return "Resolved";
    case "READY":
      return "Ready";
    case "REQUIRES_REVIEW":
      return "Requires Review";
    case "REVIEW_REQUIRED":
      return "Review Required";
    case "ANALYSIS_RUNNING":
      return "Analysis Running";
    case "ANALYSIS_COMPLETE":
      return "Analysis Complete";
    case "INTAKE_VALIDATED":
      return "Intake Validated";
    case "DRAFT":
      return "Draft";
    case "FAILED":
      return "Failed";
    case "STALE":
      return "Stale";
    case "ARCHIVED":
      return "Archived";
    case "DOES_NOT_APPLY":
      return "Does Not Apply";
    default:
      return status.replaceAll("_", " ");
  }
}