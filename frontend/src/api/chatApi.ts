export interface ApiBounds {
  south: number;
  west: number;
  north: number;
  east: number;
}

export interface ApiLocation {
  label: string;
  latitude: number | null;
  longitude: number | null;
  region_id: string | null;
  radius_km: number;
  bounds?: ApiBounds | null;
}

export interface ApiQueryParams {
  query_type: "profile" | "time_series" | "regional_average";
  parameter: "temperature" | "salinity" | "shallow_sst_proxy" | "all";
  parameters: Array<"temperature" | "salinity" | "shallow_sst_proxy">;
  location: ApiLocation;
  year_start: number | null;
  year_end: number | null;
  month: number | null;
  anomaly_requested: boolean;
  date_from: string | null;
  date_to: string | null;
  include_anomaly: boolean;
  parser_used: "llm" | "rule_based";
}

export interface ApiSeriesPoint {
  month: string;
  value: number;
  profile_count: number;
  float_count?: number;
  unit: string;
  trace?: ApiTrace;
}

export interface ApiTrace {
  observation_count: number;
  profile_count: number;
  float_count: number;
  profile_ids: string[];
  float_ids: string[];
  source_records: string[];
  truncated: boolean;
}

export interface ApiDepthBin {
  depth_bin: string;
  depth_min: number;
  depth_max: number;
  depth_mid: number;
  value: number;
  profile_count: number;
  float_count: number;
  unit: string;
  trace?: ApiTrace;
}

export interface ApiAggregateData {
  type: "profile" | "time_series" | "regional_average";
  parameter: string;
  unit: string;
  aggregation_method: string;
  current_value: number | null;
  profile_count?: number;
  bins?: ApiDepthBin[];
  series?: ApiSeriesPoint[];
  monthly_means?: ApiSeriesPoint[];
  annual_mean?: number | null;
  represented_months?: number;
  depth_range?: string;
  proxy_note?: string;
  trace?: ApiTrace;
}

export interface ApiAnomaly {
  z_score: number;
  label: string;
  current_value: number;
  baseline_mean: number;
  baseline_std: number;
  baseline_period: string;
  baseline_n: number;
  explanation: string;
}

export interface ApiEvidencePanel {
  raw_profile_count: number;
  valid_profile_count: number;
  excluded_profile_count: number;
  raw_observation_count: number;
  valid_observation_count: number;
  excluded_observation_count: number;
  distinct_float_count: number;
  qc_pass_rate: number;
  qc_rule: string;
  exclusion_reasons: Record<string, number>;
  current_period_summary: string;
  baseline_summary: string | null;
  score_summary: string | null;
  source_version: string | null;
  selection_summary: string | null;
  aggregation_method: string | null;
  proxy_caveat: string | null;
  artifact_path: string | null;
  artifact_sha256: string | null;
  contributing_profile_ids: string[];
  contributing_float_ids: string[];
  source_record_sample: string[];
  trace_sample_truncated: boolean;
}

export interface ApiSupplementary {
  ts_diagram?: {
    points: Array<{ temperature: number; salinity: number; pressure: number | null; profile_id: string }>;
    profile_count: number;
    float_count: number;
  };
  density_profile?: {
    bins: Array<{ depth_bin: string; depth_mid: number; density: number; unit: string }>;
  };
  heat_content?: {
    value_mj_per_m2: number;
    profile_count: number;
    depth_range: string;
  };
  hovmoller?: {
    grid: Array<{ month: string; depth_bin: string; depth_mid: number | null; value: number }>;
    parameter: string;
    unit: string;
  };
  seasonal_cycle?: {
    months: Array<{ month: number; month_label: string; mean: number; std: number; count: number }>;
    parameter: string;
    unit: string;
  };
  year_over_year?: {
    years: Record<string, Array<{ month: number; month_label: string; value: number }>>;
    parameter: string;
    unit: string;
  };
  anomaly_trend?: {
    series: Array<{ month: string; z_score: number; label: string; current_value: number; baseline_mean: number }>;
    parameter: string;
    unit: string;
  };
}

export interface ApiParameterResult {
  parameter: "temperature" | "salinity" | "shallow_sst_proxy";
  summary: string;
  data: ApiAggregateData;
  anomaly: ApiAnomaly | null;
  evidence_grade: "Insufficient" | "Indicative" | "Supported";
  evidence_grade_reasons: string[];
  evidence_panel: ApiEvidencePanel;
  data_quality_warning: boolean;
  answer_explanation: string;
  data_sufficiency: {
    profile_count: number;
    coverage: string;
    coverage_radius_km: number | null;
  };
  secondary_views?: Record<string, ApiAggregateData>;
  supplementary_data?: ApiSupplementary;
}

export interface ChatApiResponse {
  summary: string;
  query_type: "profile" | "time_series" | "regional_average";
  params: ApiQueryParams;
  data: ApiAggregateData;
  anomaly: ApiAnomaly | null;
  evidence_grade: "Insufficient" | "Indicative" | "Supported";
  evidence_grade_reasons: string[];
  evidence_panel: ApiEvidencePanel;
  data_quality_warning: boolean;
  answer_explanation: string;
  data_sufficiency: {
    profile_count: number;
    coverage: string;
    coverage_radius_km: number | null;
  };
  parser_used: "llm" | "rule_based";
  source: string;
  results_by_parameter: Record<string, ApiParameterResult>;
  secondary_views?: Record<string, ApiAggregateData>;
  supplementary_data?: ApiSupplementary;
}

export interface ChatApiError {
  error: {
    type: string;
    message: string;
    suggestion: string | null;
  };
}

const API_BASE = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/$/, "");

export function isErrorResponse(value: unknown): value is ChatApiError {
  if (!value || typeof value !== "object" || !("error" in value)) return false;
  const error = (value as { error?: unknown }).error;
  return Boolean(error && typeof error === "object" && "type" in error && "message" in error);
}

function isSuccessResponse(value: unknown): value is ChatApiResponse {
  return Boolean(
    value &&
      typeof value === "object" &&
      "summary" in value &&
      "evidence_grade" in value &&
      "evidence_panel" in value &&
      "data" in value,
  );
}

export async function sendChatQuery(
  query: string,
  signal?: AbortSignal,
): Promise<ChatApiResponse | ChatApiError> {
  try {
    const response = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
      signal,
    });
    const payload: unknown = await response.json();
    if (isErrorResponse(payload)) return payload;
    if (response.ok && isSuccessResponse(payload)) return payload;
    return {
      error: {
        type: "general_error",
        message: "The server returned an unexpected response.",
        suggestion: "Try again or check that the API and data artifacts are ready.",
      },
    };
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    return {
      error: {
        type: "general_error",
        message: "The FloatChat-Lite API could not be reached.",
        suggestion: "Start the API on port 8000 and try again.",
      },
    };
  }
}
