import type { ChatApiResponse } from "./chatApi";
import type {
  Confidence,
  DataSufficiencyDetails,
  DataPoint,
  EvidenceGrade,
  MapContext,
  OceanResponse,
  ParameterSeries,
  ResponseKind,
  StatusDetails,
} from "../types/ocean";
import { formatCoordinates } from "../utils/geo";

// Region rectangles are taken from the backend `location.bounds` (the scientific
// selection source of truth) so the map cannot drift from retrieval. Only the
// cosmetic tone is chosen here.
const REGION_TONE: Record<string, "aqua" | "sand"> = {
  "arabian-sea": "sand",
};

function regionContext(
  regionId: string | null,
  bounds: ChatApiResponse["params"]["location"]["bounds"],
): MapContext["region"] | undefined {
  if (!regionId || !bounds) return undefined;
  return {
    west: bounds.west,
    east: bounds.east,
    south: bounds.south,
    north: bounds.north,
    tone: REGION_TONE[regionId] ?? "aqua",
  };
}

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
  const { latitude, longitude, coordinate_precision } = response.params.location;
  return formatCoordinates(latitude, longitude, coordinate_precision ?? 2);
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
  anomaly?: { baseline_mean: number; baseline_std: number } | null,
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
  const hasBand = anomaly != null && anomaly.baseline_std > 0;
  return series.map((point) => ({
    label: point.month,
    value: point.value,
    baseline: anomaly?.baseline_mean,
    baselineUpper: hasBand ? anomaly!.baseline_mean + anomaly!.baseline_std : undefined,
    baselineLower: hasBand ? anomaly!.baseline_mean - anomaly!.baseline_std : undefined,
    trace: trace(point.trace),
  }));
}

function points(response: ChatApiResponse): DataPoint[] {
  return pointsForData(response.query_type, response.data, response.anomaly);
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
        data: pointsForData(response.query_type, result.data, result.anomaly),
        averageValue: result.data.annual_mean ?? result.data.current_value ?? undefined,
      },
    ]),
  );
}

function status(response: ChatApiResponse): StatusDetails | undefined {
  // The Z-score card is shown whenever a score exists, regardless of the
  // original query intent. When evidence is Insufficient no anomaly is emitted,
  // and the StatusCard renders a muted "unavailable" state instead.
  if (!response.anomaly) return undefined;
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
    currentNumeric: anomaly.current_value,
    baselineNumeric: anomaly.baseline_mean,
    baselineStd: anomaly.baseline_std,
    baselineN: anomaly.baseline_n,
    zScore: anomaly.z_score,
    baselinePeriod: anomaly.baseline_period,
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

function distanceLabel(value: number): string {
  return `${value.toLocaleString(undefined, { maximumFractionDigits: 1 })} km`;
}

function retrievalDetails(response: ChatApiResponse): DataSufficiencyDetails {
  return {
    requestedRadiusKm: response.data_sufficiency.requested_radius_km,
    actualRadiusKm: response.data_sufficiency.actual_radius_km,
    radiusExpanded: response.data_sufficiency.radius_expanded,
    nearestObservationKm: response.data_sufficiency.nearest_observation_km,
  };
}

export function adaptApiResponse(response: ChatApiResponse): OceanResponse {
  const location = response.params.location;
  const sufficiency = retrievalDetails(response);
  const actualRadius = sufficiency.actualRadiusKm ?? response.data_sufficiency.coverage_radius_km ?? location.radius_km;
  const searchArea = location.region_id
    ? `Named region bounds centred at ${coordinates(response)}`
    : sufficiency.radiusExpanded && sufficiency.requestedRadiusKm !== null
      ? `${distanceLabel(actualRadius)} (auto-expanded from ${distanceLabel(sufficiency.requestedRadiusKm)})`
      : `${distanceLabel(actualRadius)} search radius`;
  const nearestObservation = !location.region_id && sufficiency.nearestObservationKm !== null
    ? `${distanceLabel(sufficiency.nearestObservationKm)} from ${location.label}`
    : undefined;
  const marker = {
    latitude: location.latitude,
    longitude: location.longitude,
  };
  const reasons = response.evidence_grade_reasons.map((reason) => reason.replaceAll("_", " "));
  return {
    id: responseKind(response),
    query: response.summary,
    interpretedQuery: response.interpreted_title || response.summary,
    metadata: {
      location: location.label,
      coordinates: coordinates(response),
      period: `${response.params.date_from ?? "Unspecified"} to ${response.params.date_to ?? "Unspecified"}`,
      parameter: response.params.parameters.length > 1
        ? response.params.parameters.map((value) => PARAMETER_LABELS[value] || value).join(" and ")
        : PARAMETER_LABELS[response.params.parameter] || response.params.parameter,
      resultType: RESULT_LABELS[response.query_type] || response.query_type,
      searchArea,
      nearestObservation,
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
      radiusKm: location.region_id ? undefined : actualRadius,
      nearestObservationKm: sufficiency.nearestObservationKm ?? undefined,
      coordinatePrecision: location.coordinate_precision ?? 2,
      floatPositions: response.evidence_panel.float_positions.map((position) => ({
        floatId: position.float_id,
        latitude: position.latitude,
        longitude: position.longitude,
        profileCount: position.profile_count,
      })),
      region: regionContext(location.region_id, location.bounds ?? null),
    },
    status: status(response),
    preparation: {
      calculated: response.evidence_panel.current_period_summary,
      grouped: response.evidence_panel.aggregation_method || response.data.aggregation_method,
      baseline: response.evidence_panel.baseline_summary || "No production-baseline score was emitted for this answer.",
      score: response.evidence_panel.score_summary || "No Z-score was emitted because the evidence or production baseline was insufficient.",
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
      depthBinsUsed: response.evidence_panel.depth_bins_used,
      aggregationCountsPerBin: response.evidence_panel.aggregation_counts_per_bin,
      baselineGridCell: response.evidence_panel.baseline_grid_cell || undefined,
      baselineSelectionId: response.evidence_panel.baseline_selection_id || undefined,
      baselineMonthUsed: response.evidence_panel.baseline_month_used || undefined,
      baselineDistinctFloatCount: response.evidence_panel.baseline_distinct_float_count ?? undefined,
      evidenceChecks: response.evidence_panel.evidence_checks,
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
    secondaryViews: response.secondary_views,
    supplementaryData: response.supplementary_data,
    dataSufficiency: sufficiency,
    parameterKey: response.data.parameter,
    unit: response.data.unit,
  };
}
