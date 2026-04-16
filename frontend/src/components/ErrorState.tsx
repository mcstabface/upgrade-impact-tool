type Props = {
    message: string;
    title?: string;
    onRetry?: () => void;
    retryLabel?: string;
};

export default function ErrorState({
    message,
    title = "Something went wrong",
    onRetry,
    retryLabel = "Retry",
}: Props) {
    const [primaryMessage, recoveryGuidance] = message.split("\nRecovery: ");

    return (
        <main className="ui-state-page">
            <section className="ui-card ui-card--danger">
                <h1 className="ui-state-page__title">{title}</h1>
                <p className="ui-state-page__message">{primaryMessage}</p>
                <p className="ui-state-page__guidance">
                    {recoveryGuidance ??
                        "Try refreshing the page. If the problem continues, return to the previous screen and retry the action."}
                </p>

                {onRetry ? (
                    <div style={{ marginTop: "1rem" }}>
                        <button type="button" className="ui-button ui-button--primary" onClick={onRetry}>
                            {retryLabel}
                        </button>
                    </div>
                ) : null}
            </section>
        </main>
    );
}