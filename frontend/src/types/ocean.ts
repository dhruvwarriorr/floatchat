export type Confidence = "Low" | "Medium" | "High";
export type ResponseKind = "depth" | "sst" | "salinity" | "warming";

export interface DataPoint {
  label: string;
  value: number;
  baseline?: number;
  trend?: number;
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
}
