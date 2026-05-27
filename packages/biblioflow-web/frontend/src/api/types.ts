export interface ApiEnvelope<T> {
  data: T;
  warnings: unknown[];
  metadata: Record<string, unknown>;
}

export interface ApiErrorPayload {
  error?: {
    code?: string;
    message?: string;
    details?: Record<string, unknown>;
  };
}

export interface HealthResponse {
  service: string;
  status: string;
  version: string;
  biblioflow_version: string | null;
}

export interface Project {
  project_id: string;
  name: string;
  created_at: string;
  updated_at: string;
  active_dataset_id?: string | null;
  source_files?: Upload[];
  datasets?: DatasetListItem[];
  filters?: FilterSpec;
  metadata?: Record<string, unknown>;
}

export interface Upload {
  upload_id: string;
  filename: string;
  stored_name?: string;
  content_type?: string | null;
  size: number;
  sha256?: string;
  created_at: string;
}

export interface DatasetListItem {
  dataset_id: string;
  created_at: string;
  records: number;
  upload_ids: string[];
}

export type BibliographicRecord = Record<string, unknown>;

export interface DatasetPayload {
  dataset_id: string;
  created_at: string;
  upload_ids: string[];
  records: BibliographicRecord[];
  warnings: ApiWarning[];
  metadata: Record<string, unknown>;
}

export interface ApiWarning {
  field?: string;
  message?: string;
  record_index?: number;
  type?: string;
  level?: string;
  [key: string]: unknown;
}

export interface DatasetSummary {
  documents: number;
  sources: number;
  authors: number;
  keywords: number;
  timespan_start: number | null;
  timespan_end: number | null;
  documents_with_doi: number;
  warnings?: ApiWarning[];
  metadata?: Record<string, unknown>;
}

export interface ValidationPayload {
  dataset_id: string;
  records: number;
  warnings: ApiWarning[];
  metadata: Record<string, unknown>;
}

export interface FilterSpec {
  year_min?: number | null;
  year_max?: number | null;
  document_types?: string[] | null;
  sources?: string[] | null;
  authors?: string[] | null;
  affiliations?: string[] | null;
  countries?: string[] | null;
  keywords?: string[] | null;
  include_missing_year?: boolean;
  min_global_citations?: number | null;
  custom_field_filters?: Record<string, unknown[]>;
}

export interface FilterOptions {
  years: number[];
  document_types: string[];
  sources: string[];
  authors: string[];
  affiliations: string[];
  countries: string[];
  keywords: string[];
}

export interface FilterPreview {
  input_records: number;
  output_records: number;
  spec: FilterSpec;
  summary: DatasetSummary;
}

export interface AnalysisOverview {
  main_information: Record<string, unknown>;
  annual_production: Record<string, unknown>[];
  top_authors: Record<string, unknown>[];
  top_sources: Record<string, unknown>[];
  top_keywords: Record<string, unknown>[];
  metadata: Record<string, unknown>;
}

export interface DatasetLoadRequest {
  upload_ids?: string[] | null;
  provider: string;
  format: string;
}

export type RemoteSource = "pubmed" | "pmc" | "pubmed_central";

export interface RemoteSourceImportRequest {
  source: RemoteSource;
  query: string;
  limit: number;
  email?: string | null;
  api_key?: string | null;
  tool?: string;
  name?: string | null;
}

export interface AnalysisRequest {
  top_n?: number;
  filters?: FilterSpec;
}

export interface MatrixRequest {
  kind: string;
  unit: string;
  normalize?: string | null;
  min_occurrences: number;
  filters?: FilterSpec;
}

export interface MatrixResult {
  kind: string;
  unit: string;
  metadata: Record<string, unknown>;
  table: Record<string, unknown>[];
}

export interface NetworkNode {
  id: string;
  label?: string;
  weight?: number;
  [key: string]: unknown;
}

export interface NetworkEdge {
  source: string;
  target: string;
  weight?: number;
  [key: string]: unknown;
}

export interface NetworkResult {
  kind?: string;
  unit?: string;
  nodes: NetworkNode[];
  edges: NetworkEdge[];
  metadata?: Record<string, unknown>;
}

export interface PrismaValidationMessage {
  level: "error" | "warning";
  field: string;
  message: string;
  expected?: number | null;
  found?: number | null;
}

export interface PrismaValidationReport {
  errors: PrismaValidationMessage[];
  warnings: PrismaValidationMessage[];
}

export interface PrismaRenderPayload {
  svg: string;
  mermaid: string;
}

export interface PrismaFlowPayload {
  flow: Record<string, unknown>;
  validation: PrismaValidationReport;
  renders: PrismaRenderPayload;
  counts: Record<string, unknown>;
  metadata: Record<string, unknown>;
}

export interface PrismaFlowRequest {
  dataset_id?: string | null;
  title?: string | null;
  counts?: Record<string, unknown>;
}

export interface ExportRequest {
  dataset_id: string;
  kind: string;
  format: string;
}

export interface ExportArtifact {
  export_id: string;
  kind: string;
  format: string;
  filename: string;
  path?: string;
  size: number;
  created_at: string;
}

export interface ActiveWorkspace {
  projectId: string | null;
  activeDatasetId: string | null;
  hasDataset: boolean;
}
