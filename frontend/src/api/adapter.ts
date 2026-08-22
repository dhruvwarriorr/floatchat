import type { ChatApiResponse } from "./chatApi";
import type {
  Confidence,
  DataPoint,
  EvidenceGrade,
  MapContext,
  OceanResponse,
  ParameterSeries,
  ResponseKind,
  StatusDetails,
} from "../types/ocean";

const REGION_BOUNDS: Record<string, MapContext["region"]> = {
  "bay-of-bengal": { west: 80, east: 100, south: 5, north: 22, tone: "aqua" },
  "arabian-sea": { west: 55, east: 75, south: 8, north: 25, tone: "sand" },
  "lakshadweep-sea": { west: 70, east: 77, south: 7, north: 15, tone: "aqua" },
  "andaman-sea": { west: 92, east: 100, south: 6, north: 15, tone: "aqua" },
  "equatorial-indian": { west: 40, east: 100, south: -10, north: 10, tone: "aqua" },
  "southern-indian": { west: 20, east: 120, south: -50, north: -10, tone: "aqua" },
  "indian-ocean": { west: 20, east: 120, south: -50, north: 30, tone: "aqua" },
};

const PARAMETER_LABELS: Record<string, string> = {
  temperature: "Temperature",
  salinity: "Salinity",
  shallow_sst_proxy: "Shallow-water temperature proxy",
  all: "Temperature and salinity",
};

const RESULT_LABELS: Record<string, string> = {
  profile: "Depth profile",
  time_series: "Time series",
  regional_average: "Regional average",
};

function confidenceForGrade(grade: EvidenceGrade): Confidence {
  if (grade === "Insufficient") return "Low";
  if (grade === "Indicative") return "Medium";
  return "High";
}

function coordinates(response: ChatApiResponse): string {
  const { latitude, longitude, region_id } = response.params.location;
  if (region_id) return "Named regional selection";
  if (latitude === null || longitude === null) return "Location unavailable";
  return `${Math.abs(latitude).toFixed(2)}°${latitude >= 0 ? "N" : "S"}, ${Math.abs(longitude).toFixed(2)}°${longitude >= 0 ? "E" : "W"}`;
}

function trace(value: import("./chatApi").ApiTrace | undefined): DataPoint["trace"] {
  if (!value) return undefined;
  return {
    observationCount: value.observation_count,
    profileCount: value.profile_count,
    floatCount: value.float_count,
    profileIds: value.profile_ids,
    floatIds: value.float_ids,
    sourceRecords: value.source_records,
    truncated: value.truncated,
  };
}

function pointsForData(
  queryType: ChatApiResponse["query_type"],
  data: ChatApiResponse["data"],
  baselineMean?: number,
): DataPoint[] {
  if (queryType === "profile") {
    return (data.bins || []).map((bin) => ({
      label: String(bin.depth_mid),
      value: bin.value,
      trace: trace(bin.trace),
    }));
  }
  const series = queryType === "regional_average"
    ? data.monthly_means || []
    : data.series || [];
  return series.map((point) => ({
    label: point.month,
    value: point.value,
    baseline: baselineMean,
    trace: trace(point.trace),
  }));
}

function points(response: ChatApiResponse): DataPoint[] {
  return pointsForData(response.query_type, response.data, response.anomaly?.baseline_mean);
}

function parameterSeries(response: ChatApiResponse): Record<string, ParameterSeries> {
  const results = response.results_by_parameter || {};
  if (Object.keys(results).length === 0) {
    const key = response.data.parameter;
    return {
      [key]: {
        key,
        label: PARAMETER_LABELS[key] || key,
        unit: response.data.unit,
        data: points(response),
        averageValue: response.data.annual_mean ?? response.data.current_value ?? undefined,
      },
    };
  }
  return Object.fromEntries(
    Object.entries(results).map(([key, result]) => [
      key,
      {
        key,
        label: PARAMETER_LABELS[key] || key,
        unit: result.data.unit,
        data: pointsForData(response.query_type, result.data, result.anomaly?.baseline_mean),
        averageValue: result.data.annual_mean ?? result.data.current_value ?? undefined,
      },
    ]),
  );
}

function status(response: ChatApiResponse): StatusDetails | undefined {
  if (!response.anomaly || response.evidence_grade === "Insufficient") return undefined;
  const anomaly = response.anomaly;
  const positive = anomaly.z_score >= 0;
  return {
    label: anomaly.label.replaceAll("_", " "),
    currentLabel: "Current aggregate",
    currentValue: `${anomaly.current_value.toFixed(2)} ${response.data.unit}`,
    baselineLabel: `Baseline ${anomaly.baseline_period}`,
    baselineValue: `${anomaly.baseline_mean.toFixed(2)} ${response.data.unit}`,
    scoreLabel: "Z-score",
    scoreValue: `${anomaly.z_score >= 0 ? "+" : ""}${anomaly.z_score.toFixed(2)}`,
    interpretation: anomaly.explanation,
    tone: positive ? "sand" : "aqua",
  };
}

function responseKind(response: ChatApiResponse): ResponseKind {
  if (response.query_type === "profile") return "depth";
  if (response.query_type === "regional_average") return "salinity";
  return "sst";
}

function chartSummary(response: ChatApiResponse): string {
  const count = response.data_sufficiency.profile_count;
  const current = response.data.current_value;
  if (current === null) {
    return `No chartable QC-passed aggregate remained from the matching records.`;
  }
  return `${count} QC-passed profiles contribute to this view; the representative value is ${current.toFixed(2)} ${response.data.unit}.`;
}

export function adaptApiResponse(response: ChatApiResponse): OceanResponse {
  const location = response.params.location;
  const marker = {
    latitude: location.latitude ?? 0,
    longitude: location.longitude ?? 70,
  };
  const reasons = response.evidence_grade_reasons.map((reason) => reason.replaceAll("_", " "));
  return {
    id: responseKind(response),
    query: response.summary,
    interpretedQuery: response.summary,
    metadata: {
      location: location.label,
      coordinates: coordinates(response),
      period: `${response.params.date_from ?? "Unspecified"} to ${response.params.date_to ?? "Unspecified"}`,
      parameter: response.params.parameters.length > 1
        ? response.params.parameters.map((value) => PARAMETER_LABELS[value] || value).join(" and ")
        : PARAMETER_LABELS[response.params.parameter] || response.params.parameter,
      resultType: RESULT_LABELS[response.query_type] || response.query_type,
    },
    insight: response.summary,
    parameterDefinition: response.params.parameter === "salinity"
      ? "Salinity describes the amount of dissolved salt in seawater."
      : undefined,
    valueContext: response.params.parameter === "salinity"
      ? "Lower salinity indicates relatively fresher seawater; higher salinity indicates more dissolved salts."
      : undefined,
    chartSummary: chartSummary(response),
    explanation: response.answer_explanation,
    data: points(response),
    averageValue: response.data.annual_mean ?? response.data.current_value ?? undefined,
    averageUnit: response.data.unit,
    profileCount: response.data_sufficiency.profile_count,
    coverage: response.data_sufficiency.coverage,
    confidence: confidenceForGrade(response.evidence_grade),
    confidenceNote: reasons.join("; "),
    map: {
      label: location.label,
      coordinates: coordinates(response),
      marker,
      radiusKm: location.radius_km,
      region: location.region_id ? REGION_BOUNDS[location.region_id] : undefined,
    },
    status: status(response),
    preparation: {
      calculated: response.evidence_panel.current_period_summary,
      grouped: response.evidence_panel.aggregation_method || response.data.aggregation_method,
      baseline: response.evidence_panel.baseline_summary || "No production-baseline score was emitted for this answer.",
      score: response.evidence_panel.score_summary || "No Z-score was requested for this answer.",
      caveat: response.evidence_panel.proxy_caveat || response.data.proxy_note,
    },
    evidenceGrade: response.evidence_grade,
    evidenceGradeReasons: response.evidence_grade_reasons,
    evidencePanel: {
      rawProfileCount: response.evidence_panel.raw_profile_count,
      validProfileCount: response.evidence_panel.valid_profile_count,
      excludedProfileCount: response.evidence_panel.excluded_profile_count,
      rawObservationCount: response.evidence_panel.raw_observation_count,
      validObservationCount: response.evidence_panel.valid_observation_count,
      excludedObservationCount: response.evidence_panel.excluded_observation_count,
      distinctFloatCount: response.evidence_panel.distinct_float_count,
      qcPassRate: response.evidence_panel.qc_pass_rate,
      qcRule: response.evidence_panel.qc_rule,
      exclusionReasons: response.evidence_panel.exclusion_reasons,
      sourceVersion: response.evidence_panel.source_version || undefined,
      selectionSummary: response.evidence_panel.selection_summary || undefined,
      artifactPath: response.evidence_panel.artifact_path || undefined,
      artifactSha256: response.evidence_panel.artifact_sha256 || undefined,
      contributingProfileIds: response.evidence_panel.contributing_profile_ids,
      contributingFloatIds: response.evidence_panel.contributing_float_ids,
      sourceRecordSample: response.evidence_panel.source_record_sample,
      traceSampleTruncated: response.evidence_panel.trace_sample_truncated,
    },
    dataQualityWarning: response.data_quality_warning,
    parserUsed: response.parser_used,
    source: response.source,
    parameterSeries: parameterSeries(response),
  };
}
