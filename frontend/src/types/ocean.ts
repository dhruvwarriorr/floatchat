import type { ApiAggregateData, ApiSupplementary } from "../api/chatApi";

export type Confidence = "Low" | "Medium" | "High";
export type ResponseKind = "depth" | "sst" | "salinity" | "warming";
export type EvidenceGrade = "Insufficient" | "Indicative" | "Supported";

export interface DataPoint {
  label: string;
  value: number;
  baseline?: number;
  baselineUpper?: number;
  baselineLower?: number;
  trend?: number;
  trace?: {
    observationCount: number;
    profileCount: number;
    floatCount: number;
    profileIds: string[];
    floatIds: string[];
    sourceRecords: string[];
    truncated: boolean;
  };
}

export interface ParameterSeries {
  key: string;
  label: string;
  unit: string;
  data: DataPoint[];
  averageValue?: number;
}

export interface QueryMetadata {
  location: string;
  coordinates: string;
  period: string;
  parameter: string;
  resultType: string;
  searchArea: string;
  nearestObservation?: string;
}

export interface DataSufficiencyDetails {
  requestedRadiusKm: number | null;
  actualRadiusKm: number | null;
  radiusExpanded: boolean;
  nearestObservationKm: number | null;
}

export interface MapContext {
  label: string;
  coordinates: string;
  marker: { longitude: number; latitude: number };
  radiusKm?: number;
  nearestObservationKm?: number;
  coordinatePrecision?: number;
  floatPositions?: Array<{
    floatId: string;
    latitude: number;
    longitude: number;
    profileCount: number;
  }>;
  region?: {
    west: number;
    east: number;
    south: number;
    north: number;
    tone: "aqua" | "sand";
  };
}

export interface StatusDetails {
  label: string;
  currentLabel: string;
  currentValue: string;
  baselineLabel: string;
  baselineValue: string;
  scoreLabel: string;
  scoreValue: string;
  interpretation: string;
  tone: "sand" | "aqua" | "neutral";
  currentNumeric: number;
  baselineNumeric: number;
  baselineStd: number;
  baselineN: number;
  zScore: number;
  baselinePeriod: string;
}

export interface PreparationDetails {
  calculated: string;
  grouped: string;
  baseline: string;
  score: string;
  caveat?: string;
}

export interface EvidenceDetails {
  rawProfileCount: number;
  validProfileCount: number;
  excludedProfileCount: number;
  rawObservationCount: number;
  validObservationCount: number;
  excludedObservationCount: number;
  distinctFloatCount: number;
  qcPassRate: number;
  qcRule: string;
  exclusionReasons: Record<string, number>;
  depthBinsUsed: string[];
  aggregationCountsPerBin: Record<string, number>;
  baselineGridCell?: { south: number; west: number; north: number; east: number };
  baselineSelectionId?: string;
  baselineMonthUsed?: number;
  baselineDistinctFloatCount?: number;
  evidenceChecks: Array<{
    key: string;
    label: string;
    value: number | string | null;
    threshold: number | string | null;
    passed: boolean | null;
    detail: string;
  }>;
  sourceVersion?: string;
  selectionSummary?: string;
  artifactPath?: string;
  artifactSha256?: string;
  contributingProfileIds?: string[];
  contributingFloatIds?: string[];
  sourceRecordSample?: string[];
  traceSampleTruncated?: boolean;
}

export interface OceanResponse {
  id: ResponseKind;
  query: string;
  interpretedQuery: string;
  metadata: QueryMetadata;
  insight: string;
  parameterDefinition?: string;
  valueContext?: string;
  chartSummary: string;
  explanation: string;
  data: DataPoint[];
  averageValue?: number;
  averageUnit?: string;
  profileCount: number;
  coverage: string;
  confidence: Confidence;
  confidenceNote: string;
  map: MapContext;
  status?: StatusDetails;
  preparation: PreparationDetails;
  evidenceGrade: EvidenceGrade;
  evidenceGradeReasons: string[];
  evidencePanel: EvidenceDetails;
  dataQualityWarning: boolean;
  parserUsed: "llm" | "rule_based";
  source: string;
  parameterSeries?: Record<string, ParameterSeries>;
  secondaryViews?: Record<string, ApiAggregateData>;
  supplementaryData?: ApiSupplementary;
  dataSufficiency: DataSufficiencyDetails;
  parameterKey?: string;
  unit?: string;
}
