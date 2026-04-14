type Props = {
  status: string;
};

const STATUS_BANNERS: Record<string, string> = {
  UNKNOWN:
    "This item could not be fully resolved because required customer context is incomplete.",
  REQUIRES_REVIEW:
    "This item needs manual review before it can be cleared with confidence.",
  BLOCKED:
    "This item cannot be evaluated safely because required source data is missing.",
};

export default function StatusBanner({ status }: Props) {
  const text = STATUS_BANNERS[status];

  if (!text) return null;

  return (
    <div
      style={{
        border: "1px solid #ccc",
        padding: "0.75rem 1rem",
        margin: "1rem 0",
      }}
    >
      <strong>{status}</strong>
      <p style={{ marginBottom: 0 }}>{text}</p>
    </div>
  );
}