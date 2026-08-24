import { useId, useState, type ReactNode } from "react";

const GLOSSARY = {
  "qc-passed": "Observations retained by FloatChat-Lite's ARGO quality policy: valid position, adjusted or delayed data mode, accepted adjusted quality flag (currently flag 1), and an available adjusted value.",
  profile: "A vertical column of measurements collected by one ARGO float during one dive. A profile contains values at multiple pressures or depths.",
  dbar: "Decibars, a pressure unit used in oceanography. Near the ocean surface, 1 dbar is approximately 1 metre of depth.",
  psu: "Practical Salinity Units, the conventional unit displayed for dissolved salt in seawater. Open-ocean values are often around 34–36 PSU.",
  "argo-float": "An autonomous instrument that drifts, dives, measures ocean temperature, salinity and pressure, then surfaces to transmit its observations.",
  "production-baseline": "A pre-computed historical reference built offline from QC-passed observations. Current query values are compared with the matching baseline month and selection.",
  "standard-deviation": "A measure of spread around an average. Small values mean observations cluster closely; large values mean they are more dispersed.",
  "adjusted-values": "ARGO measurements corrected for known sensor drift by oceanographic data centres. FloatChat-Lite uses adjusted values from accepted data modes.",
  "data-mode": "The review state of ARGO data. D means delayed mode, A means adjusted, and R means preliminary real-time data. This dataset's scientific aggregate accepts A and D.",
  "grid-cell": "A 2° × 2° geographic box used for point-baseline matching. The query anchor is matched to the corresponding box.",
  haversine: "A spherical-distance calculation used to select observations within the requested radius around a latitude and longitude.",
  "evidence-grade": "A trust category based on valid profiles, historical baseline size, independent float coverage, QC pass rate and usable baseline variation.",
  "distinct-floats": "The number of separate physical ARGO instruments contributing observations. More floats provide more independent confirmation.",
  "z-score": "The distance between a current value and its historical baseline mean, measured in baseline standard deviations.",
} as const;

export type GlossaryTerm = keyof typeof GLOSSARY;

export function TermDefinition({ term, children }: { term: GlossaryTerm; children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const tooltipId = useId();
  return (
    <span className="term-definition">
      <button
        type="button"
        aria-expanded={open}
        aria-describedby={open ? tooltipId : undefined}
        onClick={() => setOpen((value) => !value)}
      >
        {children}
      </button>
      {open && <span className="term-popover" id={tooltipId} role="tooltip">{GLOSSARY[term]}</span>}
    </span>
  );
}

export function ExplanationCard({
  prompt,
  children,
  className = "",
}: {
  prompt: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <details className={`explanation-card ${className}`.trim()}>
      <summary>{prompt}</summary>
      <div className="explanation-card-body">{children}</div>
    </details>
  );
}

type ChartKind =
  | "profile"
  | "time_series"
  | "regional_average"
  | "ts_diagram"
  | "density_profile"
  | "heat_content"
  | "hovmoller"
  | "seasonal_cycle"
  | "year_over_year"
  | "anomaly_trend";

const CHART_COPY: Record<ChartKind, { what: string; read: string[]; look: string[] }> = {
  profile: {
    what: "A depth profile shows how a measured property changes as the ARGO float moves down through the water column.",
    read: ["The top is the sea surface; pressure increases downward.", "The horizontal position is the measured temperature or salinity.", "Each point combines the QC-passed profiles represented in that pressure bin."],
    look: ["A rapid temperature drop can mark a thermocline.", "Bends or inversions can reflect changing water layers, currents or eddies."],
  },
  time_series: {
    what: "A time series shows how the profile aggregate changes from month to month.",
    read: ["The horizontal axis is time and the vertical axis is the measured value.", "A dashed line is the production-baseline mean when available.", "A shaded band is one baseline standard deviation above and below that mean."],
    look: ["Repeated peaks and troughs can be seasonal.", "A sustained rise or fall suggests change that should be judged with the evidence grade."],
  },
  regional_average: {
    what: "A regional average summarises the QC-passed upper-ocean profiles inside the complete named-region bounds.",
    read: ["Each point is a represented month's mean.", "The reference line is the mean across represented months."],
    look: ["Compare months for seasonal shape.", "Missing months mean no chartable QC-passed aggregate was available."],
  },
  ts_diagram: {
    what: "A temperature–salinity diagram plots both properties for each paired observation so water-property clusters become visible.",
    read: ["Temperature is horizontal and salinity is vertical.", "Colour changes from shallow to deep pressure.", "Only rows passing the policy for both measurements are included."],
    look: ["Tight clusters show similar water properties.", "A spread can indicate mixing between different water types."],
  },
  density_profile: {
    what: "A density profile estimates how tightly seawater is packed as pressure increases.",
    read: ["Pressure increases downward.", "The curve's horizontal position is estimated density in kg/m³."],
    look: ["Denser water normally lies below lighter water.", "Use the curve's shape; this simplified estimate omits pressure effects."],
  },
  heat_content: {
    what: "This value estimates the temperature integrated through the displayed upper-ocean pressure range.",
    read: ["The result is shown in megajoules per square metre.", "It averages the eligible profile integrals in this selection."],
    look: ["Use it to compare like-for-like selections.", "It is a profile-based estimate, not a satellite heat-content product."],
  },
  hovmoller: {
    what: "A Hovmöller diagram shows change across time and pressure simultaneously.",
    read: ["Move left to right through months and top to bottom through pressure bins.", "Blue cells are lower values and red cells are higher values within this selection.", "Hover a cell for its exact month, pressure bin and value; blank cells have no data."],
    look: ["Horizontal bands show persistent structure at a pressure level.", "Vertical or diagonal colour shifts show changes through much of the water column."],
  },
  seasonal_cycle: {
    what: "The seasonal cycle averages all represented years into one typical calendar-year pattern.",
    read: ["The horizontal axis runs from January to December.", "The solid line is the multi-year monthly mean.", "The shaded band is plus or minus one sample standard deviation."],
    look: ["Peaks and troughs reveal the typical seasonal rhythm.", "A wide band means stronger year-to-year variation."],
  },
  year_over_year: {
    what: "Each coloured line represents one year, overlaid on the same January-to-December axis.",
    read: ["Follow one colour to read a single year.", "Compare the same calendar month across different coloured lines."],
    look: ["A single separated line marks an unusual year.", "A gradual shift among years can suggest longer-term change."],
  },
  anomaly_trend: {
    what: "The anomaly trend shows each monthly value's Z-score against its matching production-baseline month.",
    read: ["Zero is the historical mean.", "The green zone is within ±1.5σ, amber is ±1.5–2.5σ, and red is beyond ±2.5σ.", "Positive values are above the baseline and negative values are below it."],
    look: ["Repeated same-direction scores can reveal persistent departures.", "Interpret every point alongside its evidence and baseline coverage."],
  },
};

export function ChartExplanation({
  kind,
  method,
  inputs,
}: {
  kind: ChartKind;
  method: string;
  inputs?: string;
}) {
  const copy = CHART_COPY[kind];
  return (
    <ExplanationCard prompt="What is this chart?" className="chart-explanation">
      <section><h5>What is it?</h5><p>{copy.what}</p></section>
      <section><h5>How to read it</h5><ul>{copy.read.map((item) => <li key={item}>{item}</li>)}</ul></section>
      <section><h5>How was it calculated?</h5><p>{method}</p>{inputs && <p><strong>Inputs used:</strong> {inputs}</p>}</section>
      <section><h5>What to look for</h5><ul>{copy.look.map((item) => <li key={item}>{item}</li>)}</ul></section>
    </ExplanationCard>
  );
}
