export type UploadResponse = {
  temp_path: string;
  columns: string[];
  row_count: number;
  preview_rows: Record<string, string | number | null>[];
};

export type BiasedGroup = {
  group: string;
  approval_rate: number;
  baseline_rate: number;
  difference: number;
  disparate_impact: number;
  severity: "low" | "medium" | "high";
  count: number;
  ranking_reason?: string;
};

export type ScanResponse = {
  total_rows: number;
  groups_scanned: number;
  biased_groups_found: number;
  fairness_score: number;
  target_column: string;
  dataset_path?: string;
  top_biased_groups: BiasedGroup[];
};

export type SimulateRequest = {
  dataset_path?: string;
  target_column?: string;
  baseline_features: Record<string, string | number>;
  scenario_features: Record<string, string | number>;
};

export type SimulateField = {
  name: string;
  label: string;
  type: "categorical" | "numeric" | string;
  options?: string[];
  default?: string | number | null;
};

export type SimulateSchemaResponse = {
  dataset_path: string;
  target_column: string;
  fields: SimulateField[];
};

export type SimulateResponse = {
  baseline: {
    prediction: number;
    probability: number;
  };
  scenario: {
    prediction: number;
    probability: number;
  };
  baseline_prediction?: number;
  baseline_probability?: number;
  scenario_prediction?: number;
  scenario_probability?: number;
  changed?: boolean;
  message: string;
};

export type ExplainResponse = {
  explanation: string;
  recommendations: string[];
};
