import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ApiAggregateData } from "../api/chatApi";
import type { OceanResponse } from "../types/ocean";
import { chartAxis, chartGrid, chartLabelStyle, chartTooltip, colours } from "./Charts";

const TITLES: Record<string, string> = {
  profile: "Depth profile",
  time_series: "Time series",
  regional_average: "Regional average",
};

function seriesRows(view: ApiAggregateData) {
  if (view.type === "profile") {
    return (view.bins || []).map((bin) => ({ label: String(bin.depth_mid), value: bin.value }));
  }
  const points = view.type === "regional_average" ? view.monthly_means || [] : view.series || [];
  return points.map((point) => ({ label: point.month, value: point.value }));
}

function SecondaryChart({
  view,
  colour,
}: {
  view: ApiAggregateData;
  colour: string;
}) {
  const rows = seriesRows(view);
  const vertical = view.type === "profile";
  return (
    <section className="chart-block" aria-label={`${TITLES[view.type]} of the same data`}>
      <p className="secondary-chart-title">{TITLES[view.type]}</p>
      <div className="secondary-chart-canvas">
        <ResponsiveContainer width="100%" height="100%">
          {vertical ? (
            <LineChart data={rows.map((row) => ({ ...row, depth: Number(row.label) }))} layout="vertical" margin={{ top: 10, right: 18, left: 8, bottom: 22 }}>
              <CartesianGrid {...chartGrid} vertical />
              <XAxis type="number" dataKey="value" domain={["dataMin", "dataMax"]} {...chartAxis} label={{ value: view.unit, position: "insideBottom", offset: -12, ...chartLabelStyle }} />
              <YAxis type="number" dataKey="depth" domain={[0, "dataMax"]} reversed {...chartAxis} label={{ value: "dbar", angle: -90, position: "insideLeft", ...chartLabelStyle }} />
              <Tooltip contentStyle={chartTooltip} labelFormatter={(depth) => `${depth} dbar`} />
              <Line isAnimationActive={false} dataKey="value" type="monotone" stroke={colour} strokeWidth={2.5} dot={{ r: 2.5, fill: colour }} connectNulls />
            </LineChart>
          ) : (
            <LineChart data={rows} margin={{ top: 10, right: 18, left: 4, bottom: 22 }}>
              <CartesianGrid {...chartGrid} />
              <XAxis dataKey="label" {...chartAxis} minTickGap={24} />
              <YAxis domain={["auto", "auto"]} {...chartAxis} label={{ value: view.unit, angle: -90, position: "insideLeft", ...chartLabelStyle }} />
              <Tooltip contentStyle={chartTooltip} />
              <Line isAnimationActive={false} dataKey="value" type="monotone" stroke={colour} strokeWidth={2.5} dot={{ r: 2.5, fill: colour }} connectNulls />
            </LineChart>
          )}
        </ResponsiveContainer>
      </div>
    </section>
  );
}

export function SecondaryCharts({ response }: { response: OceanResponse }) {
  const views = response.secondaryViews;
  if (!views || Object.keys(views).length === 0) return null;
  const colour = colours[response.parameterKey ?? "temperature"] || colours.temperature;
  return (
    <div className="secondary-charts">
      <p className="section-kicker">Additional visualizations from the same data</p>
      <div className="secondary-grid">
        {Object.entries(views).map(([key, view]) => (
          <SecondaryChart key={key} view={view} colour={colour} />
        ))}
      </div>
    </div>
  );
}
