import { CalendarRange, ChartSpline, CircleDashed, Lightbulb, MapPinned, Thermometer } from "lucide-react";
import { lazy, Suspense } from "react";
import type { OceanResponse } from "../types/ocean";
import { DataSufficiency } from "./DataSufficiency";
import { ExplanationPanel } from "./ExplanationPanel";
import { StatusCard } from "./StatusCard";

const DepthProfileChart = lazy(() => import("./Charts").then((module) => ({ default: module.DepthProfileChart })));
const TimeSeriesChart = lazy(() => import("./Charts").then((module) => ({ default: module.TimeSeriesChart })));
const RegionalAverageView = lazy(() => import("./Charts").then((module) => ({ default: module.RegionalAverageView })));
const OceanMap = lazy(() => import("./OceanMap").then((module) => ({ default: module.OceanMap })));
const SecondaryCharts = lazy(() => import("./SecondaryCharts").then((module) => ({ default: module.SecondaryCharts })));
const SupplementaryCharts = lazy(() => import("./SupplementaryCharts").then((module) => ({ default: module.SupplementaryCharts })));

const metadataIcons = [MapPinned, CircleDashed, CalendarRange, Thermometer, ChartSpline];

export function ResultView({ response }: { response: OceanResponse }) {
  const metadata = [
    { label: response.map.region ? "Region" : "Location", value: response.metadata.location, detail: response.metadata.coordinates },
    { label: "Search area", value: response.metadata.searchArea },
    { label: "Period", value: response.metadata.period },
    { label: "Parameter", value: response.metadata.parameter },
    { label: "Result type", value: response.metadata.resultType },
  ];

  return (
    <section className="result-view" aria-labelledby="result-title">
      <div className="result-topline">
        <div>
          <p className="section-kicker">Interpreted query</p>
          <h2 id="result-title">{response.interpretedQuery}</h2>
        </div>
        <span className="response-id">Analysis • {response.id === "sst" ? "SST-02" : response.id === "depth" ? "TMP-01" : response.id === "salinity" ? "SAL-03" : "TRD-04"}</span>
      </div>

      <dl className="metadata-grid">
        {metadata.map(({ value, label, detail }, index) => {
          const Icon = metadataIcons[index];
          return <div key={label}><span><Icon size={15} aria-hidden="true" /></span><dt>{label}</dt><dd>{value}</dd>{detail && <small>{detail}</small>}</div>;
        })}
      </dl>

      <div className="result-disclosures" aria-label="Result provenance disclosures">
        {response.dataQualityWarning && (
          <p className="quality-warning">Limited QC-passed data are available for this query.</p>
        )}
        {response.parserUsed === "rule_based" && (
          <p className="parser-disclosure">Query parsed in deterministic simplified mode.</p>
        )}
        <p className="source-disclosure">{response.source}</p>
      </div>

      <div className="insight-banner">
        <span><Lightbulb size={20} aria-hidden="true" /></span>
        <div><p>Plain-language insight</p><h3>{response.insight}</h3></div>
      </div>

      <div className="result-grid">
        <Suspense fallback={<div className="visualization-loading">Preparing chart…</div>}>
          {response.id === "depth" && <DepthProfileChart response={response} />}
          {(response.id === "sst" || response.id === "warming") && <TimeSeriesChart response={response} />}
          {response.id === "salinity" && <RegionalAverageView response={response} />}
        </Suspense>
        <aside className="context-column">
          <Suspense fallback={<div className="visualization-loading">Preparing map…</div>}>
            <OceanMap context={response.map} />
          </Suspense>
        </aside>
      </div>

      <StatusCard response={response} />

      <DataSufficiency response={response} />

      <Suspense fallback={<div className="visualization-loading">Preparing additional charts…</div>}>
        <SecondaryCharts response={response} />
        <SupplementaryCharts data={response.supplementaryData} />
      </Suspense>

      <ExplanationPanel response={response} />
    </section>
  );
}
