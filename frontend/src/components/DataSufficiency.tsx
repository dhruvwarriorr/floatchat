import { CircleCheck, Gauge, Radar, TriangleAlert } from "lucide-react";
import type { OceanResponse } from "../types/ocean";

const gradeCopy = {
  Insufficient: "Insufficient — not enough evidence to assess",
  Indicative: "Indicative — provisional result",
  Supported: "Supported — all implemented conditions met",
} as const;

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
        <div><span><CircleCheck size={16} aria-hidden="true" /></span><dt>Evidence</dt><dd>{response.evidenceGrade}</dd></div>
      </dl>
      <p className="confidence-note"><strong>Why this grade:</strong> {response.confidenceNote || "No grade reasons were returned."}</p>
    </section>
  );
}
