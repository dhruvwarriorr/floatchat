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
}

export interface MapContext {
  label: string;
  coordinates: string;
  marker: { longitude: number; latitude: number };
  radiusKm?: number;
  coordinatePrecision?: number;
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
  parameterKey?: string;
  unit?: string;
}
