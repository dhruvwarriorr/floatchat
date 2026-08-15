import { CircleCheck, Gauge, Radar } from "lucide-react";
import type { OceanResponse } from "../types/ocean";

export function DataSufficiency({ response }: { response: OceanResponse }) {
  return (
    <section className="sufficiency-card" id="data-coverage" aria-labelledby="sufficiency-title">
      <div className="sufficiency-copy">
        <p className="section-kicker">Data sufficiency</p>
        <h3 id="sufficiency-title">Context before confidence</h3>
        <p>Based on {response.profileCount} illustrative profiles {response.coverage.toLowerCase()}. {response.confidence} confidence for this displayed selection.</p>
      </div>
      <dl className="sufficiency-metrics">
        <div><span><Radar size={16} aria-hidden="true" /></span><dt>Profile count</dt><dd>{response.profileCount}</dd></div>
        <div><span><Gauge size={16} aria-hidden="true" /></span><dt>Coverage</dt><dd>{response.coverage}</dd></div>
        <div><span><CircleCheck size={16} aria-hidden="true" /></span><dt>Confidence</dt><dd className={`confidence-${response.confidence.toLowerCase()}`}>{response.confidence}</dd></div>
      </dl>
      <p className="confidence-note"><strong>Confidence bands:</strong> 1–5 profiles Low • 6–20 Medium • 21+ High. {response.confidenceNote}.</p>
    </section>
  );
}
