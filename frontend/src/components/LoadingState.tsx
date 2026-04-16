type Props = {
    message?: string;
};

export default function LoadingState({ message = "Loading data..." }: Props) {
    return (
        <main className="ui-state-page">
            <h1 className="ui-state-page__title">Loading</h1>
            <p className="ui-state-page__message">{message}</p>
        </main>
    );
}