import { CircleCheck, Gauge, Radar, TriangleAlert } from "lucide-react";
import type { OceanResponse } from "../types/ocean";

export function DataSufficiency({ response }: { response: OceanResponse }) {
  const tier = response.confidence.toLowerCase();
  const markerPosition = response.profileCount <= 5
    ? 5 + ((Math.max(1, response.profileCount) - 1) / 4) * 24
    : response.profileCount <= 20
      ? 36 + ((response.profileCount - 6) / 14) * 28
      : 71 + Math.min((response.profileCount - 21) / 20, 1) * 24;

  return (
    <section className={`sufficiency-card tier-${tier}`} id="data-coverage" aria-labelledby="sufficiency-title">
      <div className="sufficiency-copy">
        <div>
          <p className="section-kicker">Data sufficiency</p>
          <h3 id="sufficiency-title">
            {response.confidence === "Low" && <TriangleAlert size={16} aria-hidden="true" />}
            Context before confidence
          </h3>
          <p>Based on {response.profileCount} illustrative profiles {response.coverage.toLowerCase()}. {response.confidence} confidence for this displayed selection.</p>
        </div>
        <span className="confidence-tier-label">{response.confidence} confidence</span>
      </div>

      <div className="confidence-gauge" data-tier={tier} aria-label={`${response.confidence} confidence based on ${response.profileCount} profiles`}>
        <div className="gauge-track" aria-hidden="true">
          <div className="gauge-segment low" />
          <div className="gauge-segment medium" />
          <div className="gauge-segment high" />
          <div className="gauge-fill" style={{ width: `${markerPosition}%` }} />
          <div className="gauge-marker" style={{ left: `${markerPosition}%` }} />
        </div>
        <div className="gauge-labels"><span>Low · 1–5</span><span>Medium · 6–20</span><span>High · 21+</span></div>
      </div>

      <dl className="sufficiency-metrics">
        <div><span><Radar size={16} aria-hidden="true" /></span><dt>Profile count</dt><dd>{response.profileCount}</dd></div>
        <div><span><Gauge size={16} aria-hidden="true" /></span><dt>Coverage</dt><dd>{response.coverage}</dd></div>
        <div><span><CircleCheck size={16} aria-hidden="true" /></span><dt>Confidence</dt><dd>{response.confidence}</dd></div>
      </dl>
      <p className="confidence-note"><strong>Confidence bands:</strong> 1–5 profiles Low • 6–20 Medium • 21+ High. {response.confidenceNote}.</p>
    </section>
  );
}
