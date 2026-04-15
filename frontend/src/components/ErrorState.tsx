type Props = {
  message: string;
  title?: string;
};

export default function ErrorState({
  message,
  title = "Something went wrong",
}: Props) {
  const [primaryMessage, recoveryGuidance] = message.split("\nRecovery: ");

  return (
    <main style={{ padding: "2rem", fontFamily: "sans-serif", maxWidth: "48rem" }}>
      <h1>{title}</h1>
      <p>{primaryMessage}</p>
      <p>
        {recoveryGuidance ??
          "Try refreshing the page. If the problem continues, return to the previous screen and retry the action."}
      </p>
    </main>
  );
}