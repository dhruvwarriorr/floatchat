import {
  Area,
  CartesianGrid,
  Cell,
  ComposedChart,
  Legend,
  Line,
  LineChart,
  ReferenceArea,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import { useEffect, useRef, useState } from "react";
import type { ApiSupplementary } from "../api/chatApi";
import { heatmapLayout } from "../utils/heatmap";
import { chartAxis, chartGrid, chartLabelStyle, chartTooltip } from "./Charts";

// Blue (cold/low) -> red (warm/high) ramp shared by the T-S dots and heatmap.
const RAMP = ["#2c7fb8", "#41b6c4", "#7fcdbb", "#c7e9b4", "#fed976", "#fd8d3c", "#e31a1c"];

function rampColour(fraction: number): string {
  const clamped = Math.min(1, Math.max(0, fraction));
  const scaled = clamped * (RAMP.length - 1);
  return RAMP[Math.round(scaled)];
}

const YEAR_COLOURS = ["#2DD4C8", "#EBD096", "#60A5FA", "#F472B6", "#A3E635", "#FB923C", "#C084FC"];

function TSDiagram({ data }: { data: NonNullable<ApiSupplementary["ts_diagram"]> }) {
  const pressures = data.points.map((point) => point.pressure ?? 0);
  const maxPressure = Math.max(1, ...pressures);
  return (
    <section className="supp-card" aria-label="Temperature–salinity diagram">
      <h4>T–S diagram</h4>
      <p className="supp-sub">How temperature and salinity occur together across {data.profile_count} profiles.</p>
      <div className="supp-canvas">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 10, right: 18, left: 4, bottom: 22 }}>
            <CartesianGrid {...chartGrid} vertical />
            <XAxis type="number" dataKey="temperature" name="Temperature" domain={["auto", "auto"]} {...chartAxis} label={{ value: "Temperature (°C)", position: "insideBottom", offset: -12, ...chartLabelStyle }} />
            <YAxis type="number" dataKey="salinity" name="Salinity" domain={["auto", "auto"]} {...chartAxis} label={{ value: "Salinity (PSU)", angle: -90, position: "insideLeft", ...chartLabelStyle }} />
            <ZAxis range={[24, 24]} />
            <Tooltip contentStyle={chartTooltip} cursor={{ strokeDasharray: "3 3" }} />
            <Scatter data={data.points} isAnimationActive={false}>
              {data.points.map((point, index) => (
                <Cell key={index} fill={rampColour((point.pressure ?? 0) / maxPressure)} fillOpacity={0.75} />
              ))}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>
      </div>
      <div className="depth-colour-key" aria-label={`Pressure colour scale from 0 to ${maxPressure.toFixed(0)} dbar`}>
        <span>Shallow • 0 dbar</span><span className="bar" aria-hidden="true" /><span>Deep • {maxPressure.toFixed(0)} dbar</span>
      </div>
    </section>
  );
}

function DensityProfile({ data }: { data: NonNullable<ApiSupplementary["density_profile"]> }) {
  const rows = data.bins.map((bin) => ({ density: bin.density, depth: bin.depth_mid }));
  return (
    <section className="supp-card" aria-label="Density profile">
      <h4>Density profile</h4>
      <p className="supp-sub">How tightly the sampled seawater is packed as depth increases.</p>
      <div className="supp-canvas">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={rows} layout="vertical" margin={{ top: 10, right: 18, left: 8, bottom: 22 }}>
            <CartesianGrid {...chartGrid} vertical />
            <XAxis type="number" dataKey="density" domain={["dataMin", "dataMax"]} tickCount={4} tickFormatter={(value: number) => value.toFixed(1)} {...chartAxis} label={{ value: "kg/m³", position: "insideBottom", offset: -12, ...chartLabelStyle }} />
            <YAxis type="number" dataKey="depth" domain={[0, "dataMax"]} reversed {...chartAxis} label={{ value: "dbar", angle: -90, position: "insideLeft", ...chartLabelStyle }} />
            <Tooltip contentStyle={chartTooltip} labelFormatter={(depth) => `${depth} dbar`} />
            <Line isAnimationActive={false} dataKey="density" type="monotone" stroke="#C084FC" strokeWidth={2.5} dot={{ r: 2.5, fill: "#C084FC" }} connectNulls />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <p className="chart-explainer">Simplified temperature–salinity density estimate; pressure effects are omitted, so use the shape rather than treating it as a laboratory density result.</p>
    </section>
  );
}

function HeatContent({ data }: { data: NonNullable<ApiSupplementary["heat_content"]> }) {
  return (
    <section className="supp-card" aria-label="Ocean heat content">
      <h4>Ocean heat content</h4>
      <p className="supp-sub">Integrated temperature through {data.depth_range} across {data.profile_count} profiles.</p>
      <div className="supp-kpi">
        <strong>{data.value_mj_per_m2.toFixed(0)}</strong>
        <span>MJ/m²</span>
      </div>
      <p className="chart-explainer">A profile-based estimate for comparing selections; it is not a satellite heat-content product.</p>
    </section>
  );
}

function Hovmoller({ data }: { data: NonNullable<ApiSupplementary["hovmoller"]> }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [containerWidth, setContainerWidth] = useState(960);
  const months = Array.from(new Set(data.grid.map((cell) => cell.month))).sort();
  const bins = Array.from(
    new Map(data.grid.map((cell) => [cell.depth_bin, cell.depth_mid ?? 0])).entries(),
  ).sort((a, b) => a[1] - b[1]);
  const values = data.grid.map((cell) => cell.value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const lookup = new Map(data.grid.map((cell) => [`${cell.month}|${cell.depth_bin}`, cell.value]));
  const layout = heatmapLayout(containerWidth, months.length);
  const cellHeight = 32;
  const plotTop = 38;
  const plotHeight = Math.max(1, bins.length) * cellHeight;
  const svgHeight = plotTop + plotHeight + 48;

  useEffect(() => {
    const element = containerRef.current;
    if (!element) return undefined;

    const measure = () => setContainerWidth(element.clientWidth);
    measure();
    if (typeof ResizeObserver === "undefined") {
      window.addEventListener("resize", measure);
      return () => window.removeEventListener("resize", measure);
    }
    const observer = new ResizeObserver(measure);
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  return (
    <section className="supp-card hovmoller-card" aria-label="Hovmöller depth–time heatmap">
      <h4>Hovmöller heatmap</h4>
      <p className="supp-sub">Read left to right for time and top to bottom for increasing pressure. Colour shows {data.parameter.replaceAll("_", " ")} ({data.unit}).</p>
      {/* Keyboard focus is required when a long timeline creates a scrollable region. */}
      {/* eslint-disable-next-line jsx-a11y/no-noninteractive-tabindex */}
      <div ref={containerRef} className="hovmoller" role="region" aria-label="Scrollable depth by month heatmap" tabIndex={0}>
        <svg width={layout.svgWidth} height={svgHeight} role="img" aria-label={`${data.parameter.replaceAll("_", " ")} by month and pressure bin`}>
          <text x={14} y={21} className="heatmap-axis-title">Pressure</text>
          {bins.map(([bin], rowIndex) => (
            <text key={bin} x={layout.plotLeft - 12} y={plotTop + rowIndex * cellHeight + cellHeight / 2 + 4} textAnchor="end" className="heatmap-axis-label">{bin} dbar</text>
          ))}
          {layout.labelIndexes.map((columnIndex) => (
            <text key={months[columnIndex]} x={layout.plotLeft + columnIndex * layout.cellWidth + layout.cellWidth / 2} y={svgHeight - 12} textAnchor="middle" className="heatmap-axis-label">{months[columnIndex]}</text>
          ))}
          {bins.flatMap(([bin], rowIndex) => months.map((month, columnIndex) => {
            const value = lookup.get(`${month}|${bin}`);
            const description = value === undefined
              ? `${month}, ${bin} dbar: no data`
              : `${month}, ${bin} dbar: ${value.toFixed(2)} ${data.unit}`;
            return (
              <rect
                key={`${month}-${bin}`}
                x={layout.plotLeft + columnIndex * layout.cellWidth}
                y={plotTop + rowIndex * cellHeight}
                width={layout.cellWidth - 1}
                height={cellHeight - 1}
                rx={2}
                fill={value === undefined ? "rgba(159,184,202,0.08)" : rampColour((value - min) / span)}
              >
                <title>{description}</title>
              </rect>
            );
          }))}
        </svg>
      </div>
      <div className="hovmoller-legend">
        <span>{min.toFixed(1)}</span>
        <span className="bar" aria-hidden="true" />
        <span>{max.toFixed(1)} {data.unit}</span>
      </div>
      <p className="chart-explainer">Blue cells are lower values and red cells are higher values within this selection; hover a cell for its exact month, depth and value.</p>
    </section>
  );
}

function SeasonalCycle({ data }: { data: NonNullable<ApiSupplementary["seasonal_cycle"]> }) {
  const rows = data.months.map((month) => ({
    label: month.month_label,
    mean: month.mean,
    band: [month.mean - month.std, month.mean + month.std] as [number, number],
  }));
  return (
    <section className="supp-card" aria-label="Seasonal cycle">
      <h4>Seasonal cycle</h4>
      <p className="supp-sub">Typical calendar-year pattern across all represented years; the shaded band is ±1 standard deviation.</p>
      <div className="supp-canvas">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={rows} margin={{ top: 10, right: 18, left: 4, bottom: 22 }}>
            <CartesianGrid {...chartGrid} />
            <XAxis dataKey="label" {...chartAxis} />
            <YAxis domain={["auto", "auto"]} {...chartAxis} label={{ value: data.unit, angle: -90, position: "insideLeft", ...chartLabelStyle }} />
            <Tooltip contentStyle={chartTooltip} />
            <Area isAnimationActive={false} dataKey="band" type="monotone" stroke="none" fill="#2DD4C8" fillOpacity={0.12} />
            <Line isAnimationActive={false} dataKey="mean" type="monotone" stroke="#2DD4C8" strokeWidth={2.5} dot={{ r: 2.5, fill: "#2DD4C8" }} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}

function YearOverYear({ data }: { data: NonNullable<ApiSupplementary["year_over_year"]> }) {
  const years = Object.keys(data.years).sort();
  const rows = Array.from({ length: 12 }, (_, index) => {
    const row: Record<string, number | string> = { month: index + 1, label: MONTHS[index] };
    for (const year of years) {
      const found = data.years[year].find((point) => point.month === index + 1);
      if (found) row[year] = found.value;
    }
    return row;
  });
  return (
    <section className="supp-card" aria-label="Year over year">
      <h4>Year-over-year</h4>
      <p className="supp-sub">Each coloured line is one year, making repeated seasonal shape and year-to-year shifts easier to compare.</p>
      <div className="supp-canvas">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={rows} margin={{ top: 10, right: 18, left: 4, bottom: 22 }}>
            <CartesianGrid {...chartGrid} />
            <XAxis dataKey="label" {...chartAxis} />
            <YAxis domain={["auto", "auto"]} {...chartAxis} label={{ value: data.unit, angle: -90, position: "insideLeft", ...chartLabelStyle }} />
            <Tooltip contentStyle={chartTooltip} />
            <Legend verticalAlign="top" height={26} />
            {years.map((year, index) => (
              <Line key={year} isAnimationActive={false} dataKey={year} name={year} type="monotone" stroke={YEAR_COLOURS[index % YEAR_COLOURS.length]} strokeWidth={2} dot={false} connectNulls />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}

function AnomalyTrend({ data }: { data: NonNullable<ApiSupplementary["anomaly_trend"]> }) {
  const rows = data.series.map((point) => ({ label: point.month, z: point.z_score }));
  const values = rows.map((row) => row.z);
  const domainMin = Math.min(-3, Math.floor(Math.min(...values) - 0.5));
  const domainMax = Math.max(3, Math.ceil(Math.max(...values) + 0.5));
  return (
    <section className="supp-card" aria-label="Anomaly trend">
      <h4>Anomaly trend</h4>
      <p className="supp-sub">Distance from the production baseline: green is within ±1.5σ, amber is provisional, and red is beyond ±2.5σ.</p>
      <div className="supp-canvas">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={rows} margin={{ top: 10, right: 18, left: 4, bottom: 22 }}>
            <CartesianGrid {...chartGrid} />
            <XAxis dataKey="label" {...chartAxis} minTickGap={24} />
            <YAxis domain={[domainMin, domainMax]} {...chartAxis} label={{ value: "Z-score", angle: -90, position: "insideLeft", ...chartLabelStyle }} />
            <Tooltip contentStyle={chartTooltip} />
            <ReferenceArea y1={domainMin} y2={-2.5} fill="#e31a1c" fillOpacity={0.08} />
            <ReferenceArea y1={-2.5} y2={-1.5} fill="#E0A940" fillOpacity={0.08} />
            <ReferenceArea y1={-1.5} y2={1.5} fill="#2DD4C8" fillOpacity={0.06} />
            <ReferenceArea y1={1.5} y2={2.5} fill="#E0A940" fillOpacity={0.08} />
            <ReferenceArea y1={2.5} y2={domainMax} fill="#e31a1c" fillOpacity={0.08} />
            <ReferenceLine y={0} stroke="rgba(159,184,202,0.6)" />
            <ReferenceLine y={1.5} stroke="#E0A940" strokeDasharray="5 5" />
            <ReferenceLine y={-1.5} stroke="#E0A940" strokeDasharray="5 5" />
            <ReferenceLine y={2.5} stroke="#e31a1c" strokeDasharray="5 5" />
            <ReferenceLine y={-2.5} stroke="#e31a1c" strokeDasharray="5 5" />
            <Line isAnimationActive={false} dataKey="z" type="monotone" stroke="#2DD4C8" strokeWidth={2.5} dot={{ r: 2.5, fill: "#2DD4C8" }} connectNulls />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="anomaly-zone-key" aria-label="Anomaly threshold legend"><span className="normal">Within ±1.5σ</span><span className="mild">±1.5–2.5σ</span><span className="strong">Beyond ±2.5σ</span></div>
    </section>
  );
}

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export function SupplementaryCharts({ data }: { data?: ApiSupplementary }) {
  if (!data || Object.keys(data).length === 0) return null;
  const regularCount = [
    data.ts_diagram,
    data.seasonal_cycle,
    data.density_profile,
    data.anomaly_trend,
    data.year_over_year,
    data.heat_content,
  ].filter(Boolean).length;
  return (
    <div className="supplementary-charts">
      <p className="section-kicker">Supplementary scientific views</p>
      <div className={`supplementary-grid regular-count-${regularCount}`}>
        {data.ts_diagram && <TSDiagram data={data.ts_diagram} />}
        {data.seasonal_cycle && <SeasonalCycle data={data.seasonal_cycle} />}
        {data.density_profile && <DensityProfile data={data.density_profile} />}
        {data.anomaly_trend && <AnomalyTrend data={data.anomaly_trend} />}
        {data.year_over_year && <YearOverYear data={data.year_over_year} />}
        {data.heat_content && <HeatContent data={data.heat_content} />}
        {data.hovmoller && <Hovmoller data={data.hovmoller} />}
      </div>
    </div>
  );
}
