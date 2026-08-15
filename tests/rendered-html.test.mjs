import assert from "node:assert/strict";
import { access, readFile } from "node:fs/promises";
import test from "node:test";

const root = new URL("../", import.meta.url);

test("builds the FloatChat-Lite entry page", async () => {
  const html = await readFile(new URL("dist/index.html", root), "utf8");

  assert.match(html, /<title>FloatChat-Lite \| Indian Ocean intelligence<\/title>/i);
  assert.match(html, /name="description"/i);
  assert.match(html, /id="root"/i);
  assert.doesNotMatch(html, /codex-preview|react-loading-skeleton/i);
});

test("keeps the ocean workspace local, typed, neutral, and honest about illustrative values", async () => {
  const [data, types, charts, explanation, header, map, packageJson] = await Promise.all([
    readFile(new URL("src/data/oceanResponses.ts", root), "utf8"),
    readFile(new URL("src/types/ocean.ts", root), "utf8"),
    readFile(new URL("src/components/Charts.tsx", root), "utf8"),
    readFile(new URL("src/components/ExplanationPanel.tsx", root), "utf8"),
    readFile(new URL("src/components/Header.tsx", root), "utf8"),
    readFile(new URL("src/components/OceanMap.tsx", root), "utf8"),
    readFile(new URL("package.json", root), "utf8"),
  ]);

  assert.match(types, /interface OceanResponse/);
  assert.match(data, /28\.7, 28\.5, 28\.2/);
  assert.match(data, /Z-score/);
  assert.match(data, /Bay of Bengal/);
  assert.match(data, /Arabian Sea/);
  assert.match(header, /Temperature • Salinity • Trends/);
  assert.doesNotMatch(header, /prototype|production-ready|final product|ARGO[- ]ready/i);
  assert.match(explanation, /Displayed values are illustrative\. The intended operational source is quality-controlled INCOIS ARGO data\./);
  assert.match(explanation, /1–5 Low, 6–20 Medium, and 21 or more High/);
  assert.match(data, /Salinity describes the amount of dissolved salt in seawater/);
  assert.match(data, /Lower salinity indicates relatively fresher seawater/);
  assert.match(data, /32\.8, 32\.9, 33\.1, 33\.4, 33\.6, 33\.3, 32\.7, 32\.6, 32\.9, 33\.2, 33\.5, 33\.4/);
  assert.match(data, /confidenceForProfileCount\(24\)/);
  assert.match(charts, /Mean 33\.2 PSU/);
  assert.match(charts, /Salinity \(PSU\)/);
  assert.match(map, /src="\/indian-ocean-map\.png"/);
  assert.match(map, /Political map of the Indian Ocean region/);
  await access(new URL("public/indian-ocean-map.png", root));
  assert.doesNotMatch(packageJson, /drizzle|vinext|wrangler|cloudflare|react-loading-skeleton|langchain/i);

  await assert.rejects(access(new URL(".openai", root)));
  await assert.rejects(access(new URL("db", root)));
  await assert.rejects(access(new URL("worker", root)));
});

test("preserves query submission, empty-input protection, reset, and staged resolution", async () => {
  const [composer, app] = await Promise.all([
    readFile(new URL("src/components/QueryComposer.tsx", root), "utf8"),
    readFile(new URL("src/components/FloatChatApp.tsx", root), "utf8"),
  ]);

  assert.match(composer, /type="submit" disabled=\{isLoading \|\| !query\.trim\(\)\}/);
  assert.match(composer, /event\.key === "Enter"/);
  assert.match(composer, /onSubmit\(\)/);
  assert.match(composer, /onClick=\{onReset\}/);
  assert.match(app, /if \(!query\.trim\(\) \|\| view === "loading"\) return/);
  assert.match(app, /setTimeout\(\(\) => \{/);
  assert.match(app, /}, 1180\)\)/);
  assert.match(app, /setView\("idle"\)/);
  assert.match(app, /setQuery\(""\)/);
});

test("does not expose hardcoded suggested questions in the frontend", async () => {
  const [composer, errorState] = await Promise.all([
    readFile(new URL("src/components/QueryComposer.tsx", root), "utf8"),
    readFile(new URL("src/components/ErrorState.tsx", root), "utf8"),
  ]);

  assert.doesNotMatch(composer, /suggestedQueries|Suggested questions|query-chip/);
  assert.doesNotMatch(errorState, /suggestedQueries|error-suggestions|Show temperature profile near Mumbai/);
});

test("uses the supplied ocean video as an accessible decorative background", async () => {
  const [app, styles] = await Promise.all([
    readFile(new URL("src/components/FloatChatApp.tsx", root), "utf8"),
    readFile(new URL("src/globals.css", root), "utf8"),
  ]);

  assert.match(app, /className="background-video"/);
  assert.match(app, /autoPlay/);
  assert.match(app, /muted/);
  assert.match(app, /loop/);
  assert.match(app, /playsInline/);
  assert.match(app, /src="\/ocean-background\.mp4"/);
  assert.match(styles, /prefers-reduced-motion: reduce/);
  assert.match(styles, /\.background-video\s*\{[\s\S]*display: none/);

  await access(new URL("public/ocean-background.mp4", root));
  await access(new URL("public/ocean-shore.avif", root));
});
