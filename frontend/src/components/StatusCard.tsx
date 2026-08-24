import { CircleMinus, TrendingUp, TriangleAlert } from "lucide-react";
import type { OceanResponse } from "../types/ocean";
import { ExplanationCard, TermDefinition } from "./Transparency";

export function StatusCard({ response }: { response: OceanResponse }) {
  // The Z-score card always renders. When no score was produced (Insufficient
  // evidence or no baseline for the selection) it shows a muted, honest note
  // instead of disappearing.
  if (!response.status) {
    return (
      <section className="status-card neutral tier-low" aria-labelledby="status-title">
        <div className="status-title-row">
          <span className="status-icon"><CircleMinus size={18} aria-hidden="true" /></span>
          <div>
            <p className="section-kicker">Anomaly &amp; trend context</p>
            <h3 id="status-title">Anomaly assessment unavailable</h3>
          </div>
        </div>
        <p>
          Not enough QC-passed data to compute a meaningful Z-score for this
          selection against the production baseline.
        </p>
        <ExplanationCard prompt="What does this mean?">
          <h4>What is it?</h4>
          <p>A <TermDefinition term="z-score">Z-score</TermDefinition> compares a current aggregate with its matching historical reference.</p>
          <h4>Why is it unavailable?</h4>
          <p>The service suppresses the calculation when evidence is insufficient, no matching production baseline exists, or the baseline has no usable variation.</p>
        </ExplanationCard>
      </section>
    );
  }

  const tone = response.confidence === "Low" ? "neutral" : response.status.tone;
  const tier = response.confidence.toLowerCase();
  const Icon = tone === "sand" ? TriangleAlert : tone === "aqua" ? TrendingUp : CircleMinus;
  const label = response.confidence === "Low" ? "Not enough data to assess" : response.status.label;
  const magnitude = Math.abs(response.status.zScore);
  const range = magnitude < 1.5 ? "normal" : magnitude < 2.5 ? "provisional" : "strong anomaly";

  return (
    <section className={`status-card ${tone} tier-${tier}`} aria-labelledby="status-title">
      <div className="status-title-row">
        <span className="status-icon"><Icon size={18} aria-hidden="true" /></span>
        <div><p className="section-kicker">Anomaly &amp; trend context</p><h3 id="status-title">{label}</h3></div>
      </div>
      <dl className="status-values">
        <div><dt>{response.status.currentLabel}</dt><dd>{response.status.currentValue}</dd></div>
        <div><dt>{response.status.baselineLabel}</dt><dd>{response.status.baselineValue}</dd></div>
        <div><dt>{response.status.scoreLabel}</dt><dd>{response.status.scoreValue}</dd></div>
      </dl>
      <p><strong>{response.confidence} confidence.</strong> {response.confidence === "Medium" ? "Provisional. " : ""}{response.status.interpretation}</p>
      <ExplanationCard prompt="What does this mean?" className="metric-explanation">
        <section>
          <h4>What is a <TermDefinition term="z-score">Z-score</TermDefinition>?</h4>
          <p>It tells you how far the current aggregate is from the production-baseline average, in units of baseline standard deviation.</p>
        </section>
        <section>
          <h4>How was it calculated?</h4>
          <p>Z-score = (current value − baseline mean) ÷ baseline standard deviation</p>
          <p className="formula-values">
            Z = ({response.status.currentNumeric.toFixed(2)} − {response.status.baselineNumeric.toFixed(2)}) ÷ {response.status.baselineStd.toFixed(2)} = <strong>{response.status.zScore >= 0 ? "+" : ""}{response.status.zScore.toFixed(2)}</strong>
          </p>
        </section>
        <section>
          <h4>What does this result mean?</h4>
          <p>This score is in the <strong>{range}</strong> range: within ±1.5σ is normal, ±1.5–2.5σ is provisional, and beyond ±2.5σ is strong.</p>
        </section>
        <section>
          <h4>Inputs used</h4>
          <ul>
            <li>Current aggregate: <strong>{response.status.currentNumeric.toFixed(2)} {response.unit}</strong> from {response.profileCount} QC-passed profiles.</li>
            <li>Baseline mean: <strong>{response.status.baselineNumeric.toFixed(2)} {response.unit}</strong> for {response.status.baselinePeriod}.</li>
            <li>Baseline standard deviation: <strong>{response.status.baselineStd.toFixed(2)} {response.unit}</strong> from {response.status.baselineN} observations.</li>
            <li>Selection: <strong>{response.evidencePanel.selectionSummary || response.metadata.searchArea}</strong>.</li>
            <li>Aggregation: {response.preparation.grouped}</li>
          </ul>
        </section>
      </ExplanationCard>
    </section>
  );
}
