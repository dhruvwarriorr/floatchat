import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { OceanResponse } from "../types/ocean";

const axis = {
  stroke: "rgba(159, 184, 202, 0.52)",
  tick: { fill: "#9FB8CA", fontSize: 12.5 },
  tickLine: { stroke: "rgba(159, 184, 202, 0.38)" },
  axisLine: { stroke: "rgba(159, 184, 202, 0.3)" },
};

const grid = {
  stroke: "rgba(159, 184, 202, 0.16)",
  strokeDasharray: "3 6",
  vertical: false,
};

const labelStyle = { fill: "#9FB8CA", fontSize: 12, fontWeight: 600 };

const tooltip = {
  background: "#05203B",
  border: "1px solid rgba(45, 212, 200, 0.4)",
  borderRadius: "10px",
  color: "#F4F8FA",
  boxShadow: "0 18px 44px rgba(3, 45, 88, 0.32)",
};

function ChartText({ summary }: { summary: string }) {
  return <p className="chart-summary"><span>Chart reading</span>{summary}</p>;
}

export function DepthProfileChart({ response }: { response: OceanResponse }) {
  const data = response.data.map((point) => ({ depth: Number(point.label), temperature: point.value }));

  return (
    <div className="chart-block" role="img" aria-label={response.chartSummary}>
      <div className="chart-heading">
        <div><p className="section-kicker">Vertical structure</p><h3>Temperature by depth</h3></div>
        <span className="chart-unit">°C / metres</span>
      </div>
      <div className="chart-canvas depth-chart">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} layout="vertical" margin={{ top: 12, right: 26, left: 18, bottom: 27 }}>
            <CartesianGrid {...grid} vertical />
            <XAxis type="number" dataKey="temperature" domain={[8, 30]} ticks={[10, 15, 20, 25, 30]} {...axis} label={{ value: "Temperature (°C)", position: "insideBottom", offset: -17, ...labelStyle }} />
            <YAxis type="number" dataKey="depth" domain={[0, 500]} reversed ticks={[0, 100, 200, 300, 400, 500]} {...axis} label={{ value: "Depth (m)", angle: -90, position: "insideLeft", ...labelStyle }} />
            <Tooltip contentStyle={tooltip} labelStyle={{ color: "#9FB8CA" }} itemStyle={{ color: "#F4F8FA" }} labelFormatter={(depth) => `${depth} m depth`} formatter={(value) => [`${value} °C`, "Temperature"]} />
            <Line isAnimationActive={false} dataKey="temperature" type="monotone" stroke="#2DD4C8" strokeWidth={3.5} dot={{ fill: "#2DD4C8", stroke: "#0D3157", strokeWidth: 2, r: 4 }} activeDot={{ r: 6, fill: "#F7E6BD", stroke: "#05203B", strokeWidth: 2 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <ChartText summary={response.chartSummary} />
    </div>
  );
}

export function TimeSeriesChart({ response }: { response: OceanResponse }) {
  const isWarming = response.id === "warming";

  return (
    <div className="chart-block" role="img" aria-label={response.chartSummary}>
      <div className="chart-heading">
        <div>
          <p className="section-kicker">{isWarming ? "Direction over time" : "Baseline comparison"}</p>
          <h3>{isWarming ? "Arabian Sea temperature direction" : "Shallow-water SST proxy"}</h3>
        </div>
        <span className="chart-unit">Temperature °C</span>
      </div>
      <div className="chart-canvas">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={response.data} margin={{ top: 14, right: 22, left: 4, bottom: 27 }}>
            <CartesianGrid {...grid} />
            <XAxis dataKey="label" {...axis} interval={0} label={{ value: "Year", position: "insideBottom", offset: -17, ...labelStyle }} />
            <YAxis domain={isWarming ? [27.8, 29.4] : [27.8, 29.6]} ticks={isWarming ? [28, 28.5, 29] : [28, 28.5, 29, 29.5]} {...axis} unit="°" label={{ value: "Temperature (°C)", angle: -90, position: "insideLeft", ...labelStyle }} />
            <Tooltip contentStyle={tooltip} labelStyle={{ color: "#9FB8CA" }} itemStyle={{ color: "#F4F8FA" }} labelFormatter={(label) => `Year ${label}`} formatter={(value, name) => [`${value} °C`, name === "trend" ? "Trend line" : name === "baseline" ? "Baseline" : "Temperature"]} />
            {isWarming ? (
              <>
                <Legend verticalAlign="top" height={30} iconType="plainline" wrapperStyle={{ fontSize: 12, color: "#9FB8CA" }} />
                <Line isAnimationActive={false} name="Annual value" dataKey="value" type="monotone" stroke="#2DD4C8" strokeWidth={3.5} dot={{ fill: "#2DD4C8", stroke: "#0D3157", strokeWidth: 2, r: 3.5 }} activeDot={{ r: 6, fill: "#F7E6BD" }} />
                <Line isAnimationActive={false} name="Trend line" dataKey="trend" type="linear" stroke="#F7E6BD" strokeWidth={2.25} strokeDasharray="8 6" dot={false} />
              </>
            ) : (
              <>
                <ReferenceLine y={28.4} stroke="#EBD096" strokeWidth={2} strokeDasharray="8 6" label={{ value: "Baseline 28.4°C", fill: "#F7E6BD", fontSize: 10, fontWeight: 700, position: "insideTopRight" }} />
                <Line isAnimationActive={false} dataKey="value" type="monotone" stroke="#2DD4C8" strokeWidth={3.5} dot={{ fill: "#2DD4C8", stroke: "#0D3157", strokeWidth: 2, r: 4 }} activeDot={{ r: 6, fill: "#F7E6BD", stroke: "#05203B", strokeWidth: 2 }} />
              </>
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>
      <ChartText summary={response.chartSummary} />
    </div>
  );
}

export function RegionalAverageView({ response }: { response: OceanResponse }) {
  return (
    <div className="chart-block" role="img" aria-label={response.chartSummary}>
      <div className="regional-heading">
        <div>
          <p className="section-kicker">Regional average</p>
          <div className="kpi"><strong>{response.averageValue}</strong><span>{response.averageUnit}<small>2023 mean</small></span></div>
        </div>
        <span className="chart-unit">Monthly salinity</span>
      </div>
      {response.parameterDefinition && <p className="parameter-definition">{response.parameterDefinition}</p>}
      <div className="chart-canvas compact-chart">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={response.data} margin={{ top: 10, right: 22, left: 4, bottom: 27 }}>
            <CartesianGrid {...grid} />
            <XAxis dataKey="label" {...axis} interval={0} label={{ value: "Month", position: "insideBottom", offset: -17, ...labelStyle }} />
            <YAxis domain={[32.4, 33.8]} ticks={[32.5, 33, 33.5]} {...axis} label={{ value: "Salinity (PSU)", angle: -90, position: "insideLeft", ...labelStyle }} />
            <Tooltip contentStyle={tooltip} labelStyle={{ color: "#9FB8CA" }} itemStyle={{ color: "#F4F8FA" }} formatter={(value) => [`${value} PSU`, "Salinity"]} />
            <ReferenceLine y={33.2} stroke="#EBD096" strokeWidth={2} strokeDasharray="8 6" label={{ value: "Mean 33.2 PSU", fill: "#F7E6BD", fontSize: 10, fontWeight: 700, position: "insideTopRight" }} />
            <Line isAnimationActive={false} dataKey="value" type="monotone" stroke="#2DD4C8" strokeWidth={3.5} dot={{ fill: "#2DD4C8", stroke: "#0D3157", strokeWidth: 2, r: 3.5 }} activeDot={{ r: 6, fill: "#F7E6BD" }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <ChartText summary={response.chartSummary} />
      {response.valueContext && <p className="parameter-context"><span>How to read salinity</span>{response.valueContext}</p>}
    </div>
  );
}
