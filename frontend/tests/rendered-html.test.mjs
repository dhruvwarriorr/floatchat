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
  assert.match(suggestions, /Arabian Sea/);
  assert.match(suggestions, /10N 70E/);
  assert.match(suggestions, /Bay of Bengal/);
});

test("adapts QC, evidence, parser, anomaly, and source fields", async () => {
  const [adapter, types, result] = await Promise.all([
    readFile(new URL("src/api/adapter.ts", root), "utf8"),
    readFile(new URL("src/types/ocean.ts", root), "utf8"),
    readFile(new URL("src/components/ResultView.tsx", root), "utf8"),
  ]);

  assert.match(types, /EvidenceGrade/);
  assert.match(types, /evidencePanel: EvidenceDetails/);
  assert.match(adapter, /evidence_grade_reasons/);
  assert.match(adapter, /qc_pass_rate/);
  assert.match(adapter, /parserUsed: response\.parser_used/);
  assert.match(adapter, /source: response\.source/);
  assert.match(result, /dataQualityWarning/);
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
  assert.match(panel, /rawProfileCount/);
  assert.match(panel, /rawObservationCount/);
  assert.match(panel, /qcPassRate/);
  assert.match(panel, /QC rule/);
  assert.match(panel, /Trace displayed values to source observations/);
  assert.doesNotMatch(panel, /explainable AI/i);
  assert.match(sufficiency, /Insufficient — not enough evidence to assess/);
  assert.match(sufficiency, /Supported — all implemented conditions met/);
});

test("preserves the reduced-motion background and typed error guidance", async () => {
  const [app, errorState, styles] = await Promise.all([
    readFile(new URL("src/components/FloatChatApp.tsx", root), "utf8"),
    readFile(new URL("src/components/ErrorState.tsx", root), "utf8"),
    readFile(new URL("src/globals.css", root), "utf8"),
  ]);

  assert.match(app, /className="background-video"/);
  assert.match(styles, /prefers-reduced-motion: reduce/);
  assert.match(errorState, /parse_error/);
  assert.match(errorState, /no_data/);
  assert.match(errorState, /general_error/);
  assert.match(errorState, /errorInfo\.suggestion/);
});
