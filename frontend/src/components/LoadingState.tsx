type Props = {
  message?: string;
};

export default function LoadingState({ message = "Loading data..." }: Props) {
  return (
    <main style={{ padding: "2rem", fontFamily: "sans-serif" }}>
      <h1>Loading</h1>
      <p>{message}</p>
    </main>
  );
}