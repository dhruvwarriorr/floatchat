import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const root = new URL("../", import.meta.url);

test("builds the FloatChat-Lite entry page", async () => {
  const html = await readFile(new URL("dist/index.html", root), "utf8");

  assert.match(html, /<title>FloatChat-Lite \| Indian Ocean intelligence<\/title>/i);
  assert.match(html, /name="description"/i);
  assert.match(html, /id="root"/i);
});

test("submits every user question to the backend contract", async () => {
  const [app, api] = await Promise.all([
    readFile(new URL("src/components/FloatChatApp.tsx", root), "utf8"),
    readFile(new URL("src/api/chatApi.ts", root), "utf8"),
  ]);

  assert.match(app, /sendChatQuery\(submittedQuery/);
  assert.match(app, /adaptApiResponse\(result\)/);
  assert.doesNotMatch(app, /resolveOceanQuery|oceanResponses/);
  assert.match(api, /VITE_API_URL/);
  assert.match(api, /import\.meta\.env\.VITE_API_URL \|\| ""/);
  assert.doesNotMatch(api, /VITE_API_URL \|\| "http:\/\/localhost:8000"/);
  assert.match(api, /fetch\(`\$\{API_BASE\}\/chat`/);
  assert.match(api, /JSON\.stringify\(\{ query \}\)/);
  assert.match(api, /general_error/);
});

test("renders Recharts with an interactive Leaflet map and parameter controls", async () => {
  const [charts, map, packageJson] = await Promise.all([
    readFile(new URL("src/components/Charts.tsx", root), "utf8"),
    readFile(new URL("src/components/OceanMap.tsx", root), "utf8"),
    readFile(new URL("package.json", root), "utf8"),
  ]);

  assert.match(charts, /from "recharts"/);
  assert.match(charts, /DepthProfileChart/);
  assert.match(charts, /TimeSeriesChart/);
  assert.match(charts, /ParameterToggle/);
  assert.match(charts, /Temperature|temperature/);
  assert.match(charts, /salinity/);
  assert.match(map, /from "react-leaflet"/);
  assert.match(map, /basemaps\.cartocdn\.com/);
  assert.match(map, /CircleMarker/);
  assert.match(map, /Rectangle/);
  assert.match(map, /floatPositions/);
  assert.match(map, /Nearest float/);
  assert.match(packageJson, /react-leaflet/);
  assert.doesNotMatch(packageJson, /plotly|langchain|drizzle|cloudflare/i);
});

test("renders clickable, coverage-aware suggested questions", async () => {
  const [composer, suggestions] = await Promise.all([
    readFile(new URL("src/components/QueryComposer.tsx", root), "utf8"),
    readFile(new URL("src/data/suggestedQueries.ts", root), "utf8"),
  ]);

  assert.match(composer, /suggestedQueries\.map/);
  assert.match(composer, /onSuggestedClick\(suggestion\)/);
  assert.match(composer, /event\.key === "Enter"/);
  assert.match(suggestions, /Mumbai/);
  assert.match(suggestions, /Gujarat/);
  assert.match(suggestions, /Kerala/);
  assert.match(suggestions, /Arabian Sea/);
  assert.match(suggestions, /10N 70E/);
  assert.match(suggestions, /Bay of Bengal/);
});

test("adapts QC, evidence, parser, anomaly, and source fields", async () => {
  const [adapter, api, types, result] = await Promise.all([
    readFile(new URL("src/api/adapter.ts", root), "utf8"),
    readFile(new URL("src/api/chatApi.ts", root), "utf8"),
    readFile(new URL("src/types/ocean.ts", root), "utf8"),
    readFile(new URL("src/components/ResultView.tsx", root), "utf8"),
  ]);

  assert.match(api, /interpreted_title\?: string/);
  assert.match(types, /EvidenceGrade/);
  assert.match(types, /evidencePanel: EvidenceDetails/);
  assert.match(adapter, /evidence_grade_reasons/);
  assert.match(adapter, /qc_pass_rate/);
  assert.match(adapter, /parserUsed: response\.parser_used/);
  assert.match(adapter, /source: response\.source/);
  assert.match(adapter, /radius_expanded/);
  assert.match(adapter, /nearest_observation_km/);
  assert.match(adapter, /interpretedQuery: response\.interpreted_title \|\| response\.summary/);
  assert.match(result, /dataQualityWarning/);
  assert.match(result, /Nearest observation/);
  assert.match(result, /parserUsed === "rule_based"/);
  assert.match(result, /source-disclosure/);
});

test("shows real provenance in an expandable computation-transparency panel", async () => {
  const [panel, sufficiency] = await Promise.all([
    readFile(new URL("src/components/ExplanationPanel.tsx", root), "utf8"),
    readFile(new URL("src/components/DataSufficiency.tsx", root), "utf8"),
  ]);

  assert.match(panel, /<details className="evidence-details" open>/);
  assert.match(panel, /Why this result\?/);
  assert.match(panel, /transparency-narrative/);
  assert.match(panel, /Data retrieval:/);
  assert.match(panel, /rawProfileCount/);
  assert.match(panel, /qcPassRate/);
  assert.match(panel, /QC rule/);
  assert.match(panel, /<strong>Quality control:<\/strong> \{panel\.qcRule\}/);
  assert.doesNotMatch(panel, /Applied \{panel\.qcRule\}/);
  // Section 2 renamed to a collapsed "Data Source" block (v6 reorganization).
  assert.match(panel, /<summary>Data Source<\/summary>/);
  assert.match(panel, /How was the production baseline matched\?/);
  assert.match(panel, /aggregationCountsPerBin/);
  assert.match(panel, /Open the scientific term glossary/);
  assert.doesNotMatch(panel, /explainable AI/i);
  assert.match(sufficiency, /Insufficient — not enough evidence to assess/);
  assert.match(sufficiency, /Supported — all implemented conditions met/);
});

test("renders secondary and supplementary scientific charts (v6)", async () => {
  const [result, secondary, supplementary, adapter, styles] = await Promise.all([
    readFile(new URL("src/components/ResultView.tsx", root), "utf8"),
    readFile(new URL("src/components/SecondaryCharts.tsx", root), "utf8"),
    readFile(new URL("src/components/SupplementaryCharts.tsx", root), "utf8"),
    readFile(new URL("src/api/adapter.ts", root), "utf8"),
    readFile(new URL("src/globals.css", root), "utf8"),
  ]);

  assert.match(result, /<SecondaryCharts response=\{response\} \/>/);
  assert.match(result, /<SupplementaryCharts data=\{response\.supplementaryData\} \/>/);
  assert.match(secondary, /secondaryViews/);
  assert.match(supplementary, /T–S diagram/);
  assert.match(supplementary, /Seasonal cycle/);
  assert.match(supplementary, /Hovmöller heatmap/);
  assert.match(supplementary, /<svg/);
  assert.match(supplementary, /heatmapLayout/);
  assert.match(supplementary, /regular-count-/);
  assert.match(supplementary, /supplementary-column/);
  assert.match(supplementary, /tickFormatter=\{\(value: number\) => value\.toFixed\(1\)\}/);
  assert.match(supplementary, /ReferenceArea/);
  assert.match(supplementary, /ChartExplanation/);
  assert.match(styles, /\.supplementary-columns\.column-count-3/);
  assert.match(styles, /\.supplementary-grid > \.hovmoller-card/);
  assert.match(styles, /\.result-grid > \.chart-block \.chart-canvas/);
  assert.ok(result.indexOf("<StatusCard response={response} />") > result.indexOf("</aside>"));
  // Region geometry comes from backend bounds, not a duplicated frontend table.
  assert.match(adapter, /regionContext\(location\.region_id, location\.bounds/);
  assert.doesNotMatch(adapter, /const REGION_BOUNDS/);
});

test("map fits selection geometry and stays accessible (v6)", async () => {
  const [map, geo] = await Promise.all([
    readFile(new URL("src/components/OceanMap.tsx", root), "utf8"),
    readFile(new URL("src/utils/geo.ts", root), "utf8"),
  ]);

  assert.match(map, /fitBounds/);
  assert.match(map, /invalidateSize/);
  assert.match(map, /Reset view/);
  assert.match(map, /map-text-equivalent/);
  assert.match(geo, /export function formatLatitude/);
  assert.match(geo, /export function formatRadius/);
});

test("preserves the reduced-motion background and typed error guidance", async () => {
  const [app, boundary, errorState, styles] = await Promise.all([
    readFile(new URL("src/components/FloatChatApp.tsx", root), "utf8"),
    readFile(new URL("src/components/ResultErrorBoundary.tsx", root), "utf8"),
    readFile(new URL("src/components/ErrorState.tsx", root), "utf8"),
    readFile(new URL("src/globals.css", root), "utf8"),
  ]);

  assert.match(app, /className="background-video"/);
  assert.match(app, /ResultErrorBoundary/);
  assert.match(boundary, /could not be displayed/);
  assert.match(styles, /prefers-reduced-motion: reduce/);
  assert.match(styles, /@media \(max-width: 900px\)/);
  assert.match(errorState, /parse_error/);
  assert.match(errorState, /no_data/);
  assert.match(errorState, /general_error/);
  assert.match(errorState, /errorInfo\.suggestion/);
  assert.match(errorState, /!errorInfo\?\.suggested_query/);
  assert.match(errorState, /What I understood/);
  assert.match(errorState, /Nearest available/);
});

test("makes every metric, chart, and scientific term self-explaining (v7b)", async () => {
  const [transparency, status, sufficiency, charts, secondary, supplementary, css] = await Promise.all([
    readFile(new URL("src/components/Transparency.tsx", root), "utf8"),
    readFile(new URL("src/components/StatusCard.tsx", root), "utf8"),
    readFile(new URL("src/components/DataSufficiency.tsx", root), "utf8"),
    readFile(new URL("src/components/Charts.tsx", root), "utf8"),
    readFile(new URL("src/components/SecondaryCharts.tsx", root), "utf8"),
    readFile(new URL("src/components/SupplementaryCharts.tsx", root), "utf8"),
    readFile(new URL("src/globals.css", root), "utf8"),
  ]);

  assert.match(transparency, /export function TermDefinition/);
  assert.match(transparency, /export function ExplanationCard/);
  assert.match(transparency, /How was it calculated\?/);
  assert.match(transparency, /How to read it/);
  assert.match(transparency, /production-baseline/);
  assert.match(status, /Z-score = \(current value − baseline mean\)/);
  assert.match(status, /currentNumeric/);
  assert.match(status, /baselineStd/);
  assert.match(sufficiency, /evidenceChecks\.map/);
  assert.match(charts, /kind="profile"/);
  assert.match(charts, /kind="time_series"/);
  assert.match(charts, /kind="regional_average"/);
  assert.match(secondary, /<ChartExplanation/);
  assert.match(supplementary, /kind="ts_diagram"/);
  assert.match(supplementary, /kind="density_profile"/);
  assert.match(supplementary, /kind="hovmoller"/);
  assert.match(supplementary, /kind="seasonal_cycle"/);
  assert.match(supplementary, /kind="year_over_year"/);
  assert.match(supplementary, /kind="anomaly_trend"/);
  assert.match(css, /\.supplementary-columns\s*\{[^}]*align-items:\s*start/s);
  assert.match(css, /\.metric-explanation-grid:has\(> \.explanation-card\[open\]\)/);
});
