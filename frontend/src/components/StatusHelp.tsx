type Props = {
  status: string;
};

const STATUS_HELP: Record<string, string> = {
  APPLIES:
    "This change matches the current customer context with enough evidence to treat it as in scope.",
  UNKNOWN:
    "This change may apply, but the system is missing customer-specific context needed to resolve it confidently.",
  REQUIRES_REVIEW:
    "This change needs a human reviewer to confirm whether it is acceptable, risky, or not applicable for this environment.",
  BLOCKED:
    "This change cannot be evaluated safely because required source data or intake context is missing.",
  READY:
    "No unresolved blocking or review conditions remain for this item or analysis.",
  REVIEW_REQUIRED:
    "At least one finding still needs review or clarification before the analysis can be treated as settled.",
  ANALYSIS_RUNNING:
    "This analysis is still running. Results may be incomplete until execution finishes.",
  ANALYSIS_COMPLETE:
    "Analysis execution finished successfully.",
  STALE:
    "This analysis no longer matches current source conditions and should be reviewed or refreshed before reuse.",
};

export default function StatusHelp({ status }: Props) {
  const text = STATUS_HELP[status];

  if (!text) return null;

  return <p>{text}</p>;
}