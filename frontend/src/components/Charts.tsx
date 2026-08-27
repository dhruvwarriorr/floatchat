import { useMemo, useState } from "react";
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { OceanResponse, ParameterSeries } from "../types/ocean";
import { ChartExplanation } from "./Transparency";

const axis = {
  stroke: "rgba(159, 184, 202, 0.52)",
  tick: { fill: "#9FB8CA", fontSize: 14 },
  tickLine: { stroke: "rgba(159, 184, 202, 0.38)" },
  axisLine: { stroke: "rgba(159, 184, 202, 0.3)" },
};

const grid = {
  stroke: "rgba(159, 184, 202, 0.16)",
  strokeDasharray: "3 6",
  vertical: false,
};

const labelStyle = { fill: "#9FB8CA", fontSize: 13.5, fontWeight: 600 };
const tooltip = {
  background: "#05203B",
  border: "1px solid rgba(45, 212, 200, 0.4)",
  borderRadius: "10px",
  color: "#F4F8FA",
  fontSize: "15px",
  boxShadow: "0 18px 44px rgba(3, 45, 88, 0.32)",
};
export const colours: Record<string, string> = {
  temperature: "#2DD4C8",
  shallow_sst_proxy: "#EBD096",
  salinity: "#60A5FA",
};

export const chartAxis = axis;
export const chartGrid = grid;
export const chartTooltip = tooltip;
export const chartLabelStyle = labelStyle;

function availableSeries(response: OceanResponse): ParameterSeries[] {
  if (response.parameterSeries && Object.keys(response.parameterSeries).length > 0) {
    return Object.values(response.parameterSeries);
  }
  const key = response.metadata.parameter === "Salinity" ? "salinity" : "temperature";
  return [{
    key,
    label: response.metadata.parameter,
    unit: response.averageUnit || (key === "salinity" ? "PSU" : "°C"),
    data: response.data,
    averageValue: response.averageValue,
  }];
}

function useParameterSelection(response: OceanResponse) {
  const series = useMemo(() => availableSeries(response), [response]);
  const [selection, setSelection] = useState(() => series[0].key);
  const selected = selection === "all"
    ? series
    : series.filter((item) => item.key === selection);
  return { series, selected, selection, setSelection };
}

function ParameterToggle({
  series,
  selection,
  onChange,
}: {
  series: ParameterSeries[];
  selection: string;
  onChange: (value: string) => void;
}) {
  if (series.length < 2) return null;
  const options = [{ key: "all", label: "All" }, ...series];
  return (
    <div className="parameter-toggle" aria-label="Chart parameter">
      {options.map((option) => (
        <button
          key={option.key}
          type="button"
          className={selection === option.key ? "active" : ""}
          aria-pressed={selection === option.key}
          onClick={() => onChange(option.key)}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

type ChartRow = Record<string, string | number | [number, number]>;

function combinedData(series: ParameterSeries[]): ChartRow[] {
  const rows = new Map<string, ChartRow>();
  for (const item of series) {
    for (const point of item.data) {
      const row = rows.get(point.label) || { label: point.label };
      row[item.key] = point.value;
      if (point.baseline !== undefined) row[`${item.key}Baseline`] = point.baseline;
      if (point.baselineUpper !== undefined && point.baselineLower !== undefined) {
        row[`${item.key}Band`] = [point.baselineLower, point.baselineUpper];
      }
      rows.set(point.label, row);
    }
  }
  return Array.from(rows.values()).sort((left, right) =>
    String(left.label).localeCompare(String(right.label), undefined, { numeric: true }),
  );
}

function hasBand(item: ParameterSeries) {
  return item.data.some((point) => point.baselineUpper !== undefined);
}

function ChartText({ summary }: { summary: string }) {
  return <p className="chart-summary"><span>Chart reading</span>{summary}</p>;
}

export function DepthProfileChart({ response }: { response: OceanResponse }) {
  const { series, selected, selection, setSelection } = useParameterSelection(response);
  const data = combinedData(selected).map((row) => ({ ...row, depth: Number(row.label) }));

  return (
    <section className="chart-block" aria-label={response.chartSummary}>
      <div className="chart-heading">
        <div><p className="section-kicker">Vertical structure</p><h3>Parameter by pressure</h3></div>
        <ParameterToggle series={series} selection={selection} onChange={setSelection} />
      </div>
      <ChartExplanation
        kind="profile"
        method={response.preparation.grouped}
        inputs={`${response.profileCount} QC-passed profiles; pressure bins ${response.evidencePanel.depthBinsUsed.join(", ") || "not represented"} dbar.`}
      />
      <div className="chart-canvas depth-chart">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} layout="vertical" margin={{ top: 34, right: 28, left: 18, bottom: 32 }}>
            <CartesianGrid {...grid} vertical />
            {selected.map((item, index) => (
              <XAxis
                key={item.key}
                xAxisId={item.key}
                type="number"
                dataKey={item.key}
                domain={["dataMin", "dataMax"]}
                orientation={index === 0 ? "bottom" : "top"}
                {...axis}
                label={{
                  value: `${item.label} (${item.unit})`,
                  position: index === 0 ? "insideBottom" : "insideTop",
                  offset: index === 0 ? -20 : -8,
                  ...labelStyle,
                }}
              />
            ))}
            <YAxis type="number" dataKey="depth" domain={[0, "dataMax"]} reversed {...axis} label={{ value: "Pressure proxy (dbar)", angle: -90, position: "insideLeft", ...labelStyle }} />
            <Tooltip contentStyle={tooltip} labelFormatter={(depth) => `${depth} dbar`} />
            {selected.length > 1 && <Legend verticalAlign="top" height={26} />}
            {selected.map((item) => (
              <Line
                key={item.key}
                isAnimationActive={false}
                xAxisId={item.key}
                name={`${item.label} (${item.unit})`}
                dataKey={item.key}
                type="monotone"
                stroke={colours[item.key]}
                strokeWidth={3.25}
                dot={{ fill: colours[item.key], stroke: "#0D3157", strokeWidth: 2, r: 3.5 }}
                activeDot={{ r: 6, fill: colours[item.key] }}
                connectNulls
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
      <ChartText summary={response.chartSummary} />
    </section>
  );
}

export function TimeSeriesChart({ response }: { response: OceanResponse }) {
  const { series, selected, selection, setSelection } = useParameterSelection(response);
  const data = combinedData(selected);
  return (
    <section className="chart-block" aria-label={response.chartSummary}>
      <div className="chart-heading">
        <div><p className="section-kicker">Time series</p><h3>Monthly profile aggregates</h3></div>
        <ParameterToggle series={series} selection={selection} onChange={setSelection} />
      </div>
      <ChartExplanation
        kind="time_series"
        method={response.preparation.grouped}
        inputs={`${response.profileCount} QC-passed profiles from ${response.metadata.period}.`}
      />
      <div className="chart-canvas">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 14, right: 22, left: 4, bottom: 27 }}>
            <CartesianGrid {...grid} />
            <XAxis dataKey="label" {...axis} minTickGap={24} label={{ value: "Month", position: "insideBottom", offset: -17, ...labelStyle }} />
            {selected.map((item, index) => (
              <YAxis
                key={item.key}
                yAxisId={item.key}
                orientation={index === 0 ? "left" : "right"}
                domain={["auto", "auto"]}
                {...axis}
                label={{ value: `${item.label} (${item.unit})`, angle: -90, position: index === 0 ? "insideLeft" : "insideRight", ...labelStyle }}
              />
            ))}
            <Tooltip contentStyle={tooltip} />
            {(selected.length > 1 || selected.some((item) => item.data.some((point) => point.baseline !== undefined))) && <Legend verticalAlign="top" height={30} iconType="plainline" />}
            {selected.map((item) => hasBand(item) && (
              <Area key={`${item.key}-band`} isAnimationActive={false} yAxisId={item.key} name={`${item.label} baseline ±1σ`} dataKey={`${item.key}Band`} type="monotone" stroke="none" fill={colours[item.key]} fillOpacity={0.1} connectNulls legendType="none" />
            ))}
            {selected.map((item) => (
              <Line key={item.key} isAnimationActive={false} yAxisId={item.key} name={`${item.label} (${item.unit})`} dataKey={item.key} type="monotone" stroke={colours[item.key]} strokeWidth={3.25} dot={{ fill: colours[item.key], stroke: "#0D3157", strokeWidth: 2, r: 3.25 }} activeDot={{ r: 6, fill: colours[item.key] }} connectNulls />
            ))}
            {selected.map((item) => item.data.some((point) => point.baseline !== undefined) && (
              <Line key={`${item.key}-baseline`} isAnimationActive={false} yAxisId={item.key} name={`${item.label} production baseline`} dataKey={`${item.key}Baseline`} stroke={colours[item.key]} strokeWidth={1.75} strokeDasharray="8 6" dot={false} />
            ))}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      <ChartText summary={response.chartSummary} />
    </section>
  );
}

export function RegionalAverageView({ response }: { response: OceanResponse }) {
  const { series, selected, selection, setSelection } = useParameterSelection(response);
  const data = combinedData(selected);
  return (
    <section className="chart-block" aria-label={response.chartSummary}>
      <div className="regional-heading">
        <div>
          <p className="section-kicker">Regional average</p>
          <div className="multi-kpi">
            {selected.map((item) => (
              <div className="kpi" key={item.key}><strong>{item.averageValue?.toFixed(2) ?? "—"}</strong><span>{item.unit}<small>{item.label} mean</small></span></div>
            ))}
          </div>
        </div>
        <ParameterToggle series={series} selection={selection} onChange={setSelection} />
      </div>
      <ChartExplanation
        kind="regional_average"
        method={response.preparation.grouped}
        inputs={`${response.profileCount} QC-passed profiles inside ${response.metadata.location}.`}
      />
      <div className="chart-canvas compact-chart">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 10, right: 22, left: 4, bottom: 27 }}>
            <CartesianGrid {...grid} />
            <XAxis dataKey="label" {...axis} minTickGap={18} label={{ value: "Month", position: "insideBottom", offset: -17, ...labelStyle }} />
            {selected.map((item, index) => (
              <YAxis key={item.key} yAxisId={item.key} orientation={index === 0 ? "left" : "right"} domain={["auto", "auto"]} {...axis} label={{ value: `${item.label} (${item.unit})`, angle: -90, position: index === 0 ? "insideLeft" : "insideRight", ...labelStyle }} />
            ))}
            <Tooltip contentStyle={tooltip} />
            {selected.length > 1 && <Legend verticalAlign="top" height={28} />}
            {selected.map((item) => (
              <Line key={item.key} isAnimationActive={false} yAxisId={item.key} name={`${item.label} (${item.unit})`} dataKey={item.key} type="monotone" stroke={colours[item.key]} strokeWidth={3.25} dot={{ fill: colours[item.key], stroke: "#0D3157", strokeWidth: 2, r: 3.25 }} activeDot={{ r: 6, fill: colours[item.key] }} connectNulls />
            ))}
            {selected.length === 1 && selected[0].averageValue !== undefined && (
              <ReferenceLine yAxisId={selected[0].key} y={selected[0].averageValue} stroke={colours[selected[0].key]} strokeWidth={1.75} strokeDasharray="8 6" />
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>
      <ChartText summary={response.chartSummary} />
    </section>
  );
}
