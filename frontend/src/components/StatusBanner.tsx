import { formatStatusLabel } from "../utils/status";

type Props = {
  status: string;
};

const STATUS_BANNERS: Record<
  string,
  {
    headline: string;
    detail: string;
    next_steps: string[];
  }
> = {
  UNKNOWN: {
    headline: "Customer context is incomplete.",
    detail:
      "The system found a change that may matter, but it does not have enough customer-specific detail to resolve the finding confidently.",
    next_steps: [
      "Confirm whether the affected module, configuration, or customization exists in this environment.",
      "Check the intake details and supporting KB evidence for missing scope information.",
      "Create a review item if this needs explicit follow-up.",
    ],
  },
  REQUIRES_REVIEW: {
    headline: "Manual review is still required.",
    detail:
      "This item needs a person to confirm whether the change is acceptable, risky, or out of scope for the current environment.",
    next_steps: [
      "Review the source KB evidence and recommended action.",
      "Validate the finding with the right technical or business contact.",
      "Resolve or track the item through the review queue.",
    ],
  },
  BLOCKED: {
    headline: "Required source data is missing.",
    detail:
      "The system cannot evaluate this item safely because required intake details, source evidence, or supporting context are not available.",
    next_steps: [
      "Return to intake or source data collection and fill the missing context.",
      "Confirm the relevant KB article, version range, and environment scope are correct.",
      "Re-run or refresh analysis only after the missing context is available.",
    ],
  },
};

export default function StatusBanner({ status }: Props) {
  const content = STATUS_BANNERS[status];

  if (!content) return null;

  return (
    <div
      style={{
        border: "1px solid #ccc",
        padding: "0.75rem 1rem",
        margin: "1rem 0",
      }}
    >
      <strong>{formatStatusLabel(status)}</strong>
      <p>{content.headline}</p>
      <p>{content.detail}</p>

      <div>
        <strong>What to do next</strong>
        <ul style={{ marginBottom: 0 }}>
          {content.next_steps.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}