type Props = {
  status: string;
};

const STATUS_HELP: Record<string, string> = {
  APPLIES: "This change deterministically matches the customer context.",
  UNKNOWN: "This change may apply, but customer context is incomplete.",
  REQUIRES_REVIEW: "This change needs manual review before it can be cleared.",
  BLOCKED: "This change cannot be evaluated safely because required source data is missing.",
  READY: "No unresolved blocking or review conditions remain.",
  REVIEW_REQUIRED: "At least one finding still needs review or clarification.",
  ANALYSIS_RUNNING: "This analysis is still running.",
  ANALYSIS_COMPLETE: "Analysis execution finished successfully.",
};

export default function StatusHelp({ status }: Props) {
  const text = STATUS_HELP[status];

  if (!text) return null;

  return <p>{text}</p>;
}