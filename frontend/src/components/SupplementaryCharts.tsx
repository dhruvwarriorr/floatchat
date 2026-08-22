import {
  Area,
  CartesianGrid,
  Cell,
  ComposedChart,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import type { ApiSupplementary } from "../api/chatApi";
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
      <p className="supp-sub">{data.profile_count} profiles • dot colour = pressure (dbar)</p>
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
    </section>
  );
}

function DensityProfile({ data }: { data: NonNullable<ApiSupplementary["density_profile"]> }) {
  const rows = data.bins.map((bin) => ({ density: bin.density, depth: bin.depth_mid }));
  return (
    <section className="supp-card" aria-label="Density profile">
      <h4>Density profile</h4>
      <p className="supp-sub">Approximate potential density (surface EOS)</p>
      <div className="supp-canvas">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={rows} layout="vertical" margin={{ top: 10, right: 18, left: 8, bottom: 22 }}>
            <CartesianGrid {...chartGrid} vertical />
            <XAxis type="number" dataKey="density" domain={["dataMin", "dataMax"]} {...chartAxis} label={{ value: "kg/m³", position: "insideBottom", offset: -12, ...chartLabelStyle }} />
            <YAxis type="number" dataKey="depth" domain={[0, "dataMax"]} reversed {...chartAxis} label={{ value: "dbar", angle: -90, position: "insideLeft", ...chartLabelStyle }} />
            <Tooltip contentStyle={chartTooltip} labelFormatter={(depth) => `${depth} dbar`} />
            <Line isAnimationActive={false} dataKey="density" type="monotone" stroke="#C084FC" strokeWidth={2.5} dot={{ r: 2.5, fill: "#C084FC" }} connectNulls />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}

function HeatContent({ data }: { data: NonNullable<ApiSupplementary["heat_content"]> }) {
  return (
    <section className="supp-card" aria-label="Ocean heat content">
      <h4>Ocean heat content</h4>
      <p className="supp-sub">{data.depth_range} • {data.profile_count} profiles</p>
      <div className="supp-kpi">
        <strong>{data.value_mj_per_m2.toFixed(0)}</strong>
        <span>MJ/m²</span>
      </div>
    </section>
  );
}

function Hovmoller({ data }: { data: NonNullable<ApiSupplementary["hovmoller"]> }) {
  const months = Array.from(new Set(data.grid.map((cell) => cell.month))).sort();
  const bins = Array.from(
    new Map(data.grid.map((cell) => [cell.depth_bin, cell.depth_mid ?? 0])).entries(),
  ).sort((a, b) => a[1] - b[1]);
  const values = data.grid.map((cell) => cell.value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const lookup = new Map(data.grid.map((cell) => [`${cell.month}|${cell.depth_bin}`, cell.value]));
  return (
    <section className="supp-card" aria-label="Hovmöller depth–time heatmap">
      <h4>Hovmöller heatmap</h4>
      <p className="supp-sub">{data.parameter.replaceAll("_", " ")} ({data.unit}) by depth and month</p>
      <div className="hovmoller">
        <table>
          <thead>
            <tr>
              <th className="row-head">dbar \ month</th>
              {months.map((month) => (
                <th key={month}>{month.slice(2)}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {bins.map(([bin]) => (
              <tr key={bin}>
                <th className="row-head">{bin}</th>
                {months.map((month) => {
                  const value = lookup.get(`${month}|${bin}`);
                  return (
                    <td
                      key={month}
                      title={value !== undefined ? `${month} ${bin} dbar: ${value.toFixed(2)} ${data.unit}` : "no data"}
                      style={{ background: value === undefined ? "transparent" : rampColour((value - min) / span) }}
                    />
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="hovmoller-legend">
        <span>{min.toFixed(1)}</span>
        <span className="bar" aria-hidden="true" />
        <span>{max.toFixed(1)} {data.unit}</span>
      </div>
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
      <p className="supp-sub">Monthly climatology across all years (± 1σ)</p>
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
      <p className="supp-sub">Monthly means compared across years</p>
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
  return (
    <section className="supp-card" aria-label="Anomaly trend">
      <h4>Anomaly trend</h4>
      <p className="supp-sub">Monthly Z-score vs the production baseline</p>
      <div className="supp-canvas">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={rows} margin={{ top: 10, right: 18, left: 4, bottom: 22 }}>
            <CartesianGrid {...chartGrid} />
            <XAxis dataKey="label" {...chartAxis} minTickGap={24} />
            <YAxis domain={["auto", "auto"]} {...chartAxis} label={{ value: "Z-score", angle: -90, position: "insideLeft", ...chartLabelStyle }} />
            <Tooltip contentStyle={chartTooltip} />
            <ReferenceLine y={0} stroke="rgba(159,184,202,0.6)" />
            <ReferenceLine y={1.5} stroke="#E0A940" strokeDasharray="5 5" />
            <ReferenceLine y={-1.5} stroke="#E0A940" strokeDasharray="5 5" />
            <ReferenceLine y={2.5} stroke="#e31a1c" strokeDasharray="5 5" />
            <ReferenceLine y={-2.5} stroke="#e31a1c" strokeDasharray="5 5" />
            <Line isAnimationActive={false} dataKey="z" type="monotone" stroke="#2DD4C8" strokeWidth={2.5} dot={{ r: 2.5, fill: "#2DD4C8" }} connectNulls />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export function SupplementaryCharts({ data }: { data?: ApiSupplementary }) {
  if (!data || Object.keys(data).length === 0) return null;
  return (
    <div className="supplementary-charts">
      <p className="section-kicker">Supplementary scientific views</p>
      <div className="supplementary-grid">
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
