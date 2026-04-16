type StatCardProps = {
    label: string;
    value: number | string;
};

export default function StatCard({ label, value }: StatCardProps) {
    return (
        <div className="ui-stat-card">
            <div className="ui-stat-card__label">{label}</div>
            <div className="ui-stat-card__value">{value}</div>
        </div>
    );
}