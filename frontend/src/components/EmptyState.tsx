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
        <main className="ui-state-page">
            <section className="ui-empty-block">
                <h1 className="ui-state-page__title">{title}</h1>
                <p className="ui-state-page__message">{message}</p>

                {guidanceItems.length > 0 ? (
                    <section style={{ marginTop: "1rem" }}>
                        <h2 className="ui-section-title">{guidanceTitle ?? "What to do next"}</h2>
                        <ul className="ui-list ui-list--compact">
                            {guidanceItems.map((item) => (
                                <li key={item}>{item}</li>
                            ))}
                        </ul>
                    </section>
                ) : null}
            </section>
        </main>
    );
}