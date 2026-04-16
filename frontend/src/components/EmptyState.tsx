type Props = {
  title?: string;
  message: string;
  guidanceTitle?: string;
  guidanceItems?: string[];
};

export default function EmptyState({
  title = "Nothing to show",
  message,
  guidanceTitle,
  guidanceItems = [],
}: Props) {
  return (
    <main style={{ padding: "2rem", fontFamily: "sans-serif", maxWidth: "48rem" }}>
      <h1>{title}</h1>
      <p>{message}</p>

      {guidanceItems.length > 0 && (
        <section style={{ marginTop: "1rem" }}>
          <h2 style={{ fontSize: "1.1rem" }}>{guidanceTitle ?? "What to do next"}</h2>
          <ul>
            {guidanceItems.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>
      )}
    </main>
  );
}