import type { Confidence, OceanResponse, ResponseKind } from "../types/ocean";

const points = (labels: Array<string | number>, values: number[]) =>
  labels.map((label, index) => ({ label: String(label), value: values[index] }));

const illustrativeTrust = (profileCount: number): Pick<
  OceanResponse,
  "evidenceGrade" | "evidenceGradeReasons" | "evidencePanel" | "dataQualityWarning" | "parserUsed" | "source"
> => ({
  evidenceGrade: profileCount <= 5 ? "Insufficient" : profileCount <= 20 ? "Indicative" : "Supported",
  evidenceGradeReasons: ["legacy_illustrative_profile_count_only"],
  evidencePanel: {
    rawProfileCount: profileCount,
    validProfileCount: profileCount,
    excludedProfileCount: 0,
    rawObservationCount: profileCount,
    validObservationCount: profileCount,
    excludedObservationCount: 0,
    distinctFloatCount: 0,
    qcPassRate: 1,
    qcRule: "Illustrative legacy response; no real QC computation",
    exclusionReasons: {},
    depthBinsUsed: [],
    aggregationCountsPerBin: {},
    evidenceChecks: [],
  },
  dataQualityWarning: false,
  parserUsed: "rule_based",
  source: "Illustrative local response; not live scientific data",
});

export const confidenceForProfileCount = (profileCount: number): Confidence => {
  if (profileCount <= 5) return "Low";
  if (profileCount <= 20) return "Medium";
  return "High";
};

export const suggestedQueries = [
  "Show temperature profile near Mumbai in July 2024",
  "Plot SST time series at 19N, 72.8E from 2015–2024 and tell me if it is unusual",
  "Show average salinity in the Bay of Bengal in 2023",
  "Is the Arabian Sea warming over time?",
] as const;

export const oceanResponses: Record<ResponseKind, OceanResponse> = {
  depth: {
    ...illustrativeTrust(18),
    id: "depth",
    query: suggestedQueries[0],
    interpretedQuery: "Temperature by depth near the Mumbai coast during July 2024",
    metadata: {
      location: "Mumbai coast",
      coordinates: "19.0°N, 72.8°E",
      period: "July 2024",
      parameter: "Temperature",
      resultType: "Depth profile",
      searchArea: "50 km search radius",
    },
    insight: "Warm surface water gradually cools with depth, with the strongest temperature change occurring between approximately 50 m and 150 m.",
    chartSummary: "The illustrated profile falls from 28.7°C at 5 m to 10.1°C at 500 m. The steepest decline is visible between 50 m and 150 m.",
    explanation: "The chart represents an averaged temperature profile from illustrative observations near Mumbai. Measurements are grouped by depth to show how temperature changes below the surface.",
    data: points([5, 10, 25, 50, 75, 100, 150, 200, 300, 500], [28.7, 28.5, 28.2, 27.6, 26.7, 25.3, 23.1, 20.0, 15.2, 10.1]),
    profileCount: 18,
    coverage: "Within 50 km",
    confidence: confidenceForProfileCount(18),
    confidenceNote: "Moderate coverage within this illustrative view",
    map: { label: "Mumbai coast", coordinates: "19.0°N, 72.8°E", marker: { longitude: 72.8, latitude: 19 } },
    preparation: {
      calculated: "An average temperature was calculated for each displayed depth level.",
      grouped: "Illustrative observations were grouped into ten depth bands from 5 m to 500 m.",
      baseline: "No historical baseline is required for this depth-profile view.",
      score: "A Z-score is not used because this answer describes vertical structure, not an anomaly.",
    },
  },
  sst: {
    ...illustrativeTrust(34),
    id: "sst",
    query: suggestedQueries[1],
    interpretedQuery: "Annual shallow-water SST proxy at 19.0°N, 72.8°E from 2015 to 2024",
    metadata: {
      location: "Mumbai offshore point",
      coordinates: "19.0°N, 72.8°E",
      period: "2015–2024",
      parameter: "Shallow-water SST proxy",
      resultType: "Time series",
      searchArea: "50 km search radius",
    },
    insight: "The latest displayed value is warmer than the reference baseline. A Z-score of +1.8 places it in the mild positive anomaly band used for this view.",
    chartSummary: "The illustrated series rises from 28.1°C in 2015 to 29.3°C in 2024. The latest value is 0.9°C above the 28.4°C reference baseline.",
    explanation: "Annual shallow-water illustrative measurements are compared with a reference baseline to give the latest value anomaly context.",
    data: points([2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024], [28.1, 28.2, 28.3, 28.4, 28.7, 28.6, 28.8, 28.9, 29.1, 29.3]).map((point) => ({ ...point, baseline: 28.4 })),
    profileCount: 34,
    coverage: "Within 50 km",
    confidence: confidenceForProfileCount(34),
    confidenceNote: "Strong coverage within the displayed selection",
    map: { label: "Mumbai offshore point", coordinates: "19.0°N, 72.8°E", marker: { longitude: 72.8, latitude: 19 } },
    status: {
      label: "Mild positive anomaly",
      currentLabel: "Latest value",
      currentValue: "29.3°C",
      baselineLabel: "Baseline",
      baselineValue: "28.4°C",
      scoreLabel: "Z-score",
      scoreValue: "+1.8",
      interpretation: "Warmer than the displayed baseline and within the illustrated mild anomaly band.",
      tone: "sand",
      currentNumeric: 29.3,
      baselineNumeric: 28.4,
      baselineStd: 0.5,
      baselineN: 34,
      zScore: 1.8,
      baselinePeriod: "illustrative",
    },
    preparation: {
      calculated: "The latest annual shallow-water value was compared with the displayed mean.",
      grouped: "The illustrative measurements were grouped into one value per displayed year.",
      baseline: "The reference baseline is 28.4°C with an illustrative standard deviation of 0.5°C.",
      score: "The Z-score shows how many standard deviations the latest value sits above or below the baseline.",
      caveat: "SST is represented using the shallowest available illustrative measurement at or above the 10 m cutoff. It is not satellite SST.",
    },
  },
  salinity: {
    ...illustrativeTrust(24),
    id: "salinity",
    query: suggestedQueries[2],
    interpretedQuery: "Monthly average salinity across the Bay of Bengal during 2023",
    metadata: {
      location: "Bay of Bengal",
      coordinates: "Regional selection",
      period: "2023",
      parameter: "Salinity",
      resultType: "Regional average",
      searchArea: "Named region bounds",
    },
    insight: "The displayed regional average is 33.2 PSU. Salinity decreases during the monsoon-period months and rises again toward the end of the year.",
    parameterDefinition: "Salinity describes the amount of dissolved salt in seawater.",
    valueContext: "Lower salinity indicates relatively fresher seawater, while higher salinity indicates a greater concentration of dissolved salts.",
    chartSummary: "Monthly illustrative salinity ranges from 32.6 PSU in August to 33.6 PSU in May, with a yearly regional average of 33.2 PSU.",
    explanation: "The twelve displayed monthly salinity values are averaged across the Bay of Bengal selection. The seasonal variation described here is the pattern visible in this dataset, not a validated regional conclusion.",
    data: points(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], [32.8, 32.9, 33.1, 33.4, 33.6, 33.3, 32.7, 32.6, 32.9, 33.2, 33.5, 33.4]),
    averageValue: 33.2,
    averageUnit: "PSU",
    profileCount: 24,
    coverage: "Regional selection",
    confidence: confidenceForProfileCount(24),
    confidenceNote: "Strong regional coverage within the displayed selection",
    map: {
      label: "Bay of Bengal",
      coordinates: "Regional selection",
      marker: { longitude: 87, latitude: 14 },
      region: { west: 79, east: 96, south: 5, north: 22, tone: "aqua" },
    },
    preparation: {
      calculated: "A regional mean was calculated from the twelve displayed monthly salinity values.",
      grouped: "Illustrative observations were grouped by month across the selected region.",
      baseline: "No historical anomaly baseline is used for this regional-average answer.",
      score: "A Z-score is not shown because this response does not make an anomaly claim.",
    },
  },
  warming: {
    ...illustrativeTrust(27),
    id: "warming",
    query: suggestedQueries[3],
    interpretedQuery: "Ten-year temperature direction in illustrative Arabian Sea data",
    metadata: {
      location: "Arabian Sea",
      coordinates: "Regional selection",
      period: "2015–2024",
      parameter: "Temperature",
      resultType: "Trend direction",
      searchArea: "Named region bounds",
    },
    insight: "The displayed series shows an upward direction of approximately +1.1°C across the period. This direction describes only the displayed dataset.",
    chartSummary: "The illustrated series increases from approximately 28.0°C in 2015 to 29.1°C in 2024, alongside a dashed upward trend line.",
    explanation: "A simple linear direction is fitted across the ten annual illustrative values to make the change over the displayed period easier to understand.",
    data: points([2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024], [28.0, 28.1, 28.2, 28.25, 28.4, 28.55, 28.65, 28.8, 28.95, 29.1]).map((point, index) => ({ ...point, trend: Number((28.0 + index * (1.1 / 9)).toFixed(2)) })),
    profileCount: 27,
    coverage: "Regional selection",
    confidence: confidenceForProfileCount(27),
    confidenceNote: "Strong regional coverage within the displayed selection",
    map: {
      label: "Arabian Sea",
      coordinates: "Regional selection",
      marker: { longitude: 63, latitude: 15 },
      region: { west: 52, east: 73, south: 5, north: 23, tone: "sand" },
    },
    status: {
      label: "Upward direction in displayed data",
      currentLabel: "Displayed end",
      currentValue: "29.1°C",
      baselineLabel: "Displayed start",
      baselineValue: "28.0°C",
      scoreLabel: "Period change",
      scoreValue: "+1.1°C",
      interpretation: "The fitted direction rises across the displayed series; it is not a verified finding about the wider Arabian Sea.",
      tone: "aqua",
      currentNumeric: 29.1,
      baselineNumeric: 28,
      baselineStd: 1,
      baselineN: 27,
      zScore: 1.1,
      baselinePeriod: "illustrative",
    },
    preparation: {
      calculated: "A simple linear trend direction was fitted to the ten displayed annual values.",
      grouped: "Illustrative temperature values were grouped into one average per displayed year.",
      baseline: "The first displayed year is used as the comparison point, not as a scientific climatology.",
      score: "No Z-score is used for this trend answer; the result describes change across the displayed period.",
    },
  },
};

export function resolveOceanQuery(query: string): OceanResponse | null {
  const normalized = query.toLowerCase().replace(/°/g, "");

  if (normalized.includes("mumbai") && normalized.includes("temperature")) return oceanResponses.depth;
  if (normalized.includes("19n") || normalized.includes("72.8") || normalized.includes("sst") || normalized.includes("unusual")) return oceanResponses.sst;
  if (normalized.includes("bay of bengal") && normalized.includes("salinity")) return oceanResponses.salinity;
  if (normalized.includes("arabian sea") && normalized.includes("warming")) return oceanResponses.warming;

  return null;
}
