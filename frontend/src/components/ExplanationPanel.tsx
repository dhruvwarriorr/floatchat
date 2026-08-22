import { Braces, Database, Layers3, Scale } from "lucide-react";
import type { OceanResponse } from "../types/ocean";

const reasonLabel = (reason: string) => reason.replaceAll("_", " ");

export function ExplanationPanel({ response }: { response: OceanResponse }) {
  const items = [
    { icon: Braces, title: "What was calculated", copy: response.preparation.calculated },
    { icon: Layers3, title: "How values were grouped", copy: response.preparation.grouped },
    { icon: Database, title: "Production baseline", copy: response.preparation.baseline },
    { icon: Scale, title: "Score decision", copy: response.preparation.score },
  ];
  const panel = response.evidencePanel;
  const traceSeries = response.parameterSeries
    ? Object.values(response.parameterSeries)
    : [];

  return (
    <section className="explanation-panel" id="methodology" aria-labelledby="explanation-title">
      <details className="evidence-details" open>
        <summary>
          <span><span className="section-kicker">Computation transparency</span><strong id="explanation-title">Why this result?</strong></span>
          <small>Expand or collapse</small>
        </summary>
        <p className="answer-explanation">{response.explanation}</p>
        <dl className="evidence-metrics">
          <div><dt>Profiles</dt><dd>{panel.rawProfileCount} raw • {panel.validProfileCount} valid • {panel.excludedProfileCount} excluded</dd></div>
          <div><dt>Observations</dt><dd>{panel.rawObservationCount} raw • {panel.validObservationCount} valid • {panel.excludedObservationCount} excluded</dd></div>
          <div><dt>Distinct floats</dt><dd>{panel.distinctFloatCount}</dd></div>
          <div><dt>QC pass rate</dt><dd>{(panel.qcPassRate * 100).toFixed(1)}%</dd></div>
        </dl>
        <div className="preparation-grid">
          {items.map(({ icon: Icon, title, copy }) => (
            <article key={title}>
              <span><Icon size={15} aria-hidden="true" /></span>
              <div><h3>{title}</h3><p>{copy}</p></div>
            </article>
          ))}
        </div>
        <div className="provenance-lines">
          <p><strong>QC rule</strong>{panel.qcRule}</p>
          {panel.selectionSummary && <p><strong>Selection</strong>{panel.selectionSummary}</p>}
          {panel.sourceVersion && <p><strong>Dataset version</strong>{panel.sourceVersion}</p>}
          {panel.artifactPath && <p><strong>Artifact</strong>{panel.artifactPath}</p>}
          {panel.artifactSha256 && <p><strong>Artifact SHA-256</strong><code>{panel.artifactSha256}</code></p>}
          {(panel.contributingFloatIds?.length ?? 0) > 0 && (
            <p><strong>Float IDs</strong>{panel.contributingFloatIds?.join(", ")}{panel.traceSampleTruncated ? " (sample)" : ""}</p>
          )}
          {(panel.contributingProfileIds?.length ?? 0) > 0 && (
            <p><strong>Profile IDs</strong>{panel.contributingProfileIds?.join(", ")}{panel.traceSampleTruncated ? " (sample)" : ""}</p>
          )}
          {(panel.sourceRecordSample?.length ?? 0) > 0 && (
            <p><strong>Source rows</strong>{panel.sourceRecordSample?.join(", ")}{panel.traceSampleTruncated ? " (sample)" : ""}</p>
          )}
          {Object.keys(panel.exclusionReasons).length > 0 && (
            <p><strong>Exclusions</strong>{Object.entries(panel.exclusionReasons).map(([reason, count]) => `${reasonLabel(reason)}: ${count}`).join(" • ")}</p>
          )}
        </div>
        {traceSeries.some((series) => series.data.some((point) => point.trace)) && (
          <details className="value-trace">
            <summary>Trace displayed values to source observations</summary>
            <div className="value-trace-table-wrap">
              <table>
                <thead><tr><th>Parameter</th><th>Chart point</th><th>Value</th><th>Profiles</th><th>Source-row sample</th></tr></thead>
                <tbody>
                  {traceSeries.flatMap((series) => series.data.map((point) => (
                    <tr key={`${series.key}-${point.label}`}>
                      <td>{series.label}</td>
                      <td>{point.label}</td>
                      <td>{point.value.toFixed(3)} {series.unit}</td>
                      <td>{point.trace?.profileIds.join(", ") || "—"}</td>
                      <td>{point.trace?.sourceRecords.join(", ") || "—"}{point.trace?.truncated ? " (sample)" : ""}</td>
                    </tr>
                  )))}</tbody>
              </table>
            </div>
          </details>
        )}
        {response.preparation.caveat && <p className="method-caveat"><strong>Measurement note</strong>{response.preparation.caveat}</p>}
        <p className="confidence-method"><strong>{response.evidenceGrade}</strong>{response.evidenceGradeReasons.map(reasonLabel).join(" • ")}</p>
      </details>
    </section>
  );
}
