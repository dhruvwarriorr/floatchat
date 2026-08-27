import { CircleCheck, Gauge, LocateFixed, Radar, TriangleAlert } from "lucide-react";
import type { OceanResponse } from "../types/ocean";
import { ExplanationCard, TermDefinition } from "./Transparency";

const gradeCopy = {
  Insufficient: "Insufficient — not enough evidence to assess",
  Indicative: "Indicative — provisional result",
  Supported: "Supported — all implemented conditions met",
} as const;

function checkValue(key: string, value: number | string | null) {
  if (value === null) return "Not available";
  if (key === "qc_pass_rate" && typeof value === "number") return `${(value * 100).toFixed(1)}%`;
  return String(value);
}

export function DataSufficiency({ response }: { response: OceanResponse }) {
  const tier = response.confidence.toLowerCase();
  const markerPosition = response.evidenceGrade === "Insufficient" ? 17 : response.evidenceGrade === "Indicative" ? 50 : 83;

  return (
    <section className={`sufficiency-card tier-${tier}`} id="data-coverage" aria-labelledby="sufficiency-title">
      <div className="sufficiency-copy">
        <div>
          <p className="section-kicker">Evidence grade</p>
          <h3 id="sufficiency-title">
            {response.evidenceGrade === "Insufficient" && <TriangleAlert size={16} aria-hidden="true" />}
            {gradeCopy[response.evidenceGrade]}
          </h3>
          <p>{response.profileCount} QC-passed profiles contribute to this result {response.coverage.toLowerCase()}.</p>
        </div>
        <span className="confidence-tier-label">{response.evidenceGrade}</span>
      </div>

      <div className="confidence-gauge" data-tier={tier} aria-label={`${response.evidenceGrade} evidence grade`}>
        <div className="gauge-track" aria-hidden="true">
          <div className="gauge-segment low" />
          <div className="gauge-segment medium" />
          <div className="gauge-segment high" />
          <div className="gauge-fill" style={{ width: `${markerPosition}%` }} />
          <div className="gauge-marker" style={{ left: `${markerPosition}%` }} />
        </div>
        <div className="gauge-labels"><span>Insufficient</span><span>Indicative</span><span>Supported</span></div>
      </div>

      <dl className="sufficiency-metrics">
        <div><span><Radar size={16} aria-hidden="true" /></span><dt>Valid profiles</dt><dd>{response.profileCount}</dd></div>
        <div><span><Gauge size={16} aria-hidden="true" /></span><dt>Coverage</dt><dd>{response.coverage}</dd></div>
        {response.dataSufficiency.actualRadiusKm !== null && <div><span><Gauge size={16} aria-hidden="true" /></span><dt>Search area</dt><dd>{response.metadata.searchArea}</dd></div>}
        {response.dataSufficiency.nearestObservationKm !== null && <div><span><LocateFixed size={16} aria-hidden="true" /></span><dt>Nearest data</dt><dd>{response.dataSufficiency.nearestObservationKm.toLocaleString(undefined, { maximumFractionDigits: 1 })} km</dd></div>}
        <div><span><CircleCheck size={16} aria-hidden="true" /></span><dt>Evidence</dt><dd>{response.evidenceGrade}</dd></div>
      </dl>
      <p className="confidence-note"><strong>Why this grade:</strong> {response.confidenceNote || "No grade reasons were returned."}</p>
      <ExplanationCard prompt="How was this grade determined?" className="metric-explanation">
        <h4>What is the <TermDefinition term="evidence-grade">evidence grade</TermDefinition>?</h4>
        <p>It indicates how much trust this result can carry based on data quantity, independent coverage, quality-control retention and baseline support.</p>
        <h4>Threshold checks</h4>
        <ul className="evidence-checks">
          {response.evidencePanel.evidenceChecks.map((check) => (
            <li key={check.key} data-status={check.passed === null ? "pending" : check.passed ? "pass" : "fail"}>
              <span aria-hidden="true">{check.passed === null ? "◇" : check.passed ? "✓" : "✕"}</span>
              <div>
                <strong>{check.label}: {checkValue(check.key, check.value)}</strong>
                <small>Threshold: {checkValue(check.key, check.threshold)}. {check.detail}</small>
              </div>
            </li>
          ))}
        </ul>
        <h4>What does the result mean?</h4>
        <p><strong>{response.evidenceGrade}</strong>: {gradeCopy[response.evidenceGrade]}. The implemented thresholds are versioned with the dataset and remain separate from external scientific validation.</p>
      </ExplanationCard>
    </section>
  );
}
