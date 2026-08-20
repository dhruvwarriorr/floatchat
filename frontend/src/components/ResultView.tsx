import { CalendarRange, ChartSpline, Lightbulb, MapPinned, Thermometer } from "lucide-react";
import type { OceanResponse } from "../types/ocean";
import { DepthProfileChart, RegionalAverageView, TimeSeriesChart } from "./Charts";
import { DataSufficiency } from "./DataSufficiency";
import { ExplanationPanel } from "./ExplanationPanel";
import { OceanMap } from "./OceanMap";
import { StatusCard } from "./StatusCard";

const metadataIcons = [MapPinned, CalendarRange, Thermometer, ChartSpline];

export function ResultView({ response }: { response: OceanResponse }) {
  const metadata = [
    { label: response.metadata.coordinates === "Regional selection" ? "Region" : "Location", value: response.metadata.location, detail: response.metadata.coordinates },
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

      <div className="insight-banner">
        <span><Lightbulb size={20} aria-hidden="true" /></span>
        <div><p>Plain-language insight</p><h3>{response.insight}</h3></div>
      </div>

      <div className="result-grid">
        {response.id === "depth" && <DepthProfileChart response={response} />}
        {(response.id === "sst" || response.id === "warming") && <TimeSeriesChart response={response} />}
        {response.id === "salinity" && <RegionalAverageView response={response} />}
        <aside className="context-column">
          <OceanMap context={response.map} />
          <StatusCard response={response} />
        </aside>
      </div>

      <DataSufficiency response={response} />
      <ExplanationPanel response={response} />
    </section>
  );
}
