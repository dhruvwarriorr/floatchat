import { Braces, Database, Layers3, Scale } from "lucide-react";
import type { OceanResponse } from "../types/ocean";

const reasonLabel = (reason: string) => reason.replaceAll("_", " ");

const NO_BASELINE = "No production-baseline score was emitted for this answer.";
const NO_SCORE = "No Z-score was requested for this answer.";

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
  const exclusionText = Object.entries(panel.exclusionReasons)
    .map(([reason, count]) => `${count} for ${reasonLabel(reason)}`)
    .join(", ");

  return (
    <section className="explanation-panel" id="methodology" aria-labelledby="explanation-title">
      <details className="evidence-details" open>
        <summary>
          <span><span className="section-kicker">Computation transparency</span><strong id="explanation-title">Why this result?</strong></span>
          <small>Expand or collapse</small>
        </summary>

        {/* Section 1 — natural-language narrative (visible by default) */}
        <div className="transparency-narrative">
          <p>
            <strong>Data retrieval:</strong>{" "}
            {panel.selectionSummary || `Searched near ${response.metadata.location}`}. Found{" "}
            {panel.rawProfileCount} raw profiles; {panel.validProfileCount} passed quality control
            {" "}({(panel.qcPassRate * 100).toFixed(0)}% pass rate) from {panel.distinctFloatCount}
            {" "}distinct ARGO floats.
          </p>
          <p>
            <strong>Quality control:</strong> Applied {panel.qcRule}.{" "}
            {panel.excludedProfileCount > 0
              ? `${panel.excludedProfileCount} profiles were excluded${exclusionText ? ` (${exclusionText})` : ""}.`
              : "All retrieved profiles passed QC."}
          </p>
          <p><strong>Current period:</strong> {response.preparation.calculated}</p>
          {response.preparation.baseline !== NO_BASELINE && (
            <p><strong>Baseline comparison:</strong> {response.preparation.baseline}</p>
          )}
          {response.preparation.score !== NO_SCORE && (
            <p><strong>Anomaly score:</strong> {response.preparation.score}</p>
          )}
          {response.preparation.caveat && (
            <p><strong>Measurement note:</strong> {response.preparation.caveat}</p>
          )}
        </div>

        {/* Structured detail retained below the narrative */}
        <div className="preparation-grid">
          {items.map(({ icon: Icon, title, copy }) => (
            <article key={title}>
              <span><Icon size={15} aria-hidden="true" /></span>
              <div><h3>{title}</h3><p>{copy}</p></div>
            </article>
          ))}
        </div>

        {/* Human-readable provenance stays visible */}
        <div className="provenance-lines">
          <p><strong>QC rule</strong>{panel.qcRule}</p>
          {panel.selectionSummary && <p><strong>Selection</strong>{panel.selectionSummary}</p>}
        </div>

        {/* Section 2 — technical identifiers, collapsed by default */}
        <details className="value-trace">
          <summary>Data Source</summary>
          <div className="provenance-lines" style={{ marginTop: "9px" }}>
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
          )}
        </details>

        <p className="confidence-method"><strong>{response.evidenceGrade}</strong>{response.evidenceGradeReasons.map(reasonLabel).join(" • ")}</p>
      </details>
    </section>
  );
}
