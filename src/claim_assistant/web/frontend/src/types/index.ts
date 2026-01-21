export type BoundingRegion = {
  page: number;
  polygon: number[]; // length 8
};

export type FieldEvidence = {
  source?: string;
  confidence?: number | null;
  bounding_region?: BoundingRegion | null;
};

export type FormFieldAnswer = {
  value?: unknown;
  evidences?: FieldEvidence[];
};

export type FormField = {
  order: number;
  text: string;
  description?: string | null;
  alias?: string | null;
  data_type?: string | null;
  meta?: Record<string, unknown>;
  answer?: FormFieldAnswer | null;
};

export type MockPolicyRecord = {
  policy_number?: string;
  policy_holder_first_name?: string;
  policy_holder_last_name?: string;
  start_date?: string;
  end_data?: string; // note: your API returns end_data key
  policy_coverage?: string;
  policy_file_name?: string | null;
};

export type CoverageAnalysisResponse = {
  executive_summary: string;
  conclusion: "positive" | "negative" | "uncertain";
  confidence: number;
  form: FormField[];
  policy: MockPolicyRecord | null;
};
