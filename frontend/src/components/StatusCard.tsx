import { CircleMinus, TrendingUp, TriangleAlert } from "lucide-react";
import type { OceanResponse } from "../types/ocean";

export function StatusCard({ response }: { response: OceanResponse }) {
  if (!response.status) return null;

  const tone = response.confidence === "Low" ? "neutral" : response.status.tone;
  const tier = response.confidence.toLowerCase();
  const Icon = tone === "sand" ? TriangleAlert : tone === "aqua" ? TrendingUp : CircleMinus;
  const label = response.confidence === "Low" ? "Not enough data to assess" : response.status.label;

  return (
    <section className={`status-card ${tone} tier-${tier}`} aria-labelledby="status-title">
      <div className="status-title-row">
        <span className="status-icon"><Icon size={18} aria-hidden="true" /></span>
        <div><p className="section-kicker">Anomaly & trend context</p><h3 id="status-title">{label}</h3></div>
      </div>
      <dl className="status-values">
        <div><dt>{response.status.currentLabel}</dt><dd>{response.status.currentValue}</dd></div>
        <div><dt>{response.status.baselineLabel}</dt><dd>{response.status.baselineValue}</dd></div>
        <div><dt>{response.status.scoreLabel}</dt><dd>{response.status.scoreValue}</dd></div>
      </dl>
      <p><strong>{response.confidence} confidence.</strong> {response.confidence === "Medium" ? "Provisional. " : ""}{response.status.interpretation}</p>
    </section>
  );
}
