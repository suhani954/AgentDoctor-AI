export default function MetricCard({ label, value, helper, tone = "emerald" }) {
  return (
    <div className={`metric-card ${tone}`}>
      <p>{label}</p>
      <strong>{value}</strong>
      {helper && <span>{helper}</span>}
    </div>
  );
}
