type Props = {
  title?: string;
  message: string;
};

export default function EmptyState({
  title = "Nothing to show",
  message,
}: Props) {
  return (
    <main style={{ padding: "2rem", fontFamily: "sans-serif", maxWidth: "48rem" }}>
      <h1>{title}</h1>
      <p>{message}</p>
    </main>
  );
}