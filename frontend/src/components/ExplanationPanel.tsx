import { Braces, Database, Layers3, Scale } from "lucide-react";
import type { OceanResponse } from "../types/ocean";
import { ExplanationCard, TermDefinition } from "./Transparency";

const exclusionLabels: Record<string, string> = {
  position_qc_not_1: "invalid or unaccepted recorded position",
  real_time_mode_excluded: "preliminary real-time mode without accepted adjusted data",
  adjusted_qc_not_1: "adjusted measurement did not have the accepted quality flag",
  null_adjusted_value: "adjusted measurement value was missing",
};

const reasonLabel = (reason: string) => exclusionLabels[reason] || reason.replaceAll("_", " ");

const NO_BASELINE = "No production-baseline score was emitted for this answer.";
const NO_SCORE = "No Z-score was emitted because the evidence or production baseline was insufficient.";

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
  const profileWord = (count: number) => count === 1 ? "profile" : "profiles";
  const floatWord = (count: number) => count === 1 ? "float" : "floats";

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
            {panel.rawProfileCount} raw <TermDefinition term="profile">{profileWord(panel.rawProfileCount)}</TermDefinition>; {panel.validProfileCount} passed quality control
            {" "}({(panel.qcPassRate * 100).toFixed(0)}% pass rate) from {panel.distinctFloatCount}
            {" "}<TermDefinition term="distinct-floats">distinct ARGO {floatWord(panel.distinctFloatCount)}</TermDefinition>.
          </p>
          <p>
            <strong>Quality control:</strong> {panel.qcRule}.{" "}
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

        <div className="metric-explanation-grid">
          <ExplanationCard prompt={`How was the ${(panel.qcPassRate * 100).toFixed(1)}% QC pass rate calculated?`} className="metric-explanation">
            <h4>What is quality control?</h4>
            <p>Only <TermDefinition term="qc-passed">QC-passed</TermDefinition> observations enter the aggregation, protecting the result from unaccepted positions, modes, flags and missing adjusted values.</p>
            <h4>How was it calculated?</h4>
            <p>QC pass rate = valid observations ÷ retrieved observations × 100</p>
            <p className="formula-values"><strong>{panel.validObservationCount.toLocaleString()}</strong> ÷ <strong>{panel.rawObservationCount.toLocaleString()}</strong> × 100 = <strong>{(panel.qcPassRate * 100).toFixed(1)}%</strong></p>
            <h4>What was excluded?</h4>
            {Object.keys(panel.exclusionReasons).length > 0 ? (
              <ul>{Object.entries(panel.exclusionReasons).map(([reason, count]) => <li key={reason}><strong>{count.toLocaleString()}</strong> — {reasonLabel(reason)}</li>)}</ul>
            ) : <p>No retrieved observations were excluded.</p>}
            <h4>What does this result mean?</h4>
            <p><strong>{(panel.qcPassRate * 100).toFixed(1)}%</strong> means {panel.validObservationCount.toLocaleString()} of {panel.rawObservationCount.toLocaleString()} retrieved observations were eligible for the calculation. Excluded observations do not contribute to any chart, aggregate or Z-score.</p>
            <h4>Inputs used</h4>
            <p>{panel.rawProfileCount} retrieved {profileWord(panel.rawProfileCount)}, {panel.validProfileCount} valid {profileWord(panel.validProfileCount)} and {panel.distinctFloatCount} physical ARGO {floatWord(panel.distinctFloatCount)}.</p>
          </ExplanationCard>

          <ExplanationCard prompt="How was the production baseline matched?" className="metric-explanation">
            <h4>What is it?</h4>
            <p>The <TermDefinition term="production-baseline">production baseline</TermDefinition> is the offline historical reference used to decide whether the current aggregate is unusual.</p>
            <h4>How was it matched?</h4>
            {panel.baselineMonthUsed ? (
              <ul>
                <li>Matched calendar month: <strong>{panel.baselineMonthUsed}</strong>.</li>
                {panel.baselineGridCell && <li><TermDefinition term="grid-cell">Grid cell</TermDefinition>: <strong>{panel.baselineGridCell.south}° to {panel.baselineGridCell.north}° latitude, {panel.baselineGridCell.west}° to {panel.baselineGridCell.east}° longitude</strong>.</li>}
                {panel.baselineSelectionId && <li>Baseline selection ID: <strong>{panel.baselineSelectionId}</strong>.</li>}
                {panel.baselineDistinctFloatCount !== undefined && <li>Historical float coverage: <strong>{panel.baselineDistinctFloatCount} distinct floats</strong>.</li>}
              </ul>
            ) : <p>No matching production baseline was available, so no baseline formula can be shown.</p>}
            <h4>What does this result mean?</h4>
            {panel.baselineMonthUsed ? (
              <p>The current aggregate was compared only with the returned baseline matched to calendar month <strong>{panel.baselineMonthUsed}</strong> and selection <strong>{panel.baselineSelectionId || "reported by the backend"}</strong>.</p>
            ) : (
              <p>The result cannot be compared with historical conditions because no eligible production baseline was returned.</p>
            )}
            <h4>Inputs used</h4>
            <p>{response.preparation.baseline}</p>
          </ExplanationCard>
        </div>

        <ExplanationCard prompt="Open the scientific term glossary">
          <p className="glossary-links">
            <TermDefinition term="qc-passed">QC-passed</TermDefinition>
            <TermDefinition term="profile">Profile</TermDefinition>
            <TermDefinition term="dbar">dbar</TermDefinition>
            <TermDefinition term="psu">PSU</TermDefinition>
            <TermDefinition term="argo-float">ARGO float</TermDefinition>
            <TermDefinition term="production-baseline">Production baseline</TermDefinition>
            <TermDefinition term="standard-deviation">Standard deviation (σ)</TermDefinition>
            <TermDefinition term="adjusted-values">Adjusted values</TermDefinition>
            <TermDefinition term="data-mode">Data mode</TermDefinition>
            <TermDefinition term="grid-cell">Grid cell</TermDefinition>
            <TermDefinition term="haversine">Haversine</TermDefinition>
            <TermDefinition term="evidence-grade">Evidence grade</TermDefinition>
            <TermDefinition term="distinct-floats">Distinct floats</TermDefinition>
          </p>
        </ExplanationCard>

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
          {panel.depthBinsUsed.length > 0 && <p><strong>Depth bins</strong>{panel.depthBinsUsed.map((bin) => `${bin} dbar (${panel.aggregationCountsPerBin[bin] ?? 0} profiles)`).join(" • ")}</p>}
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
