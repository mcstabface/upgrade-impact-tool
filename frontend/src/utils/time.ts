export function formatUnixSeconds(value: number | null | undefined): string {
  if (!value) return "N/A";

  const date = new Date(value * 1000);

  if (Number.isNaN(date.getTime())) {
    return "N/A";
  }

  return date.toLocaleString();
}