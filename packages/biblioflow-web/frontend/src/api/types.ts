export interface ApiEnvelope<T> {
  data: T;
  warnings: unknown[];
  metadata: Record<string, unknown>;
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
}

export interface DatasetSummary {
  documents: number;
  sources: number;
  authors: number;
  keywords: number;
  timespan_start: number | null;
  timespan_end: number | null;
  documents_with_doi: number;
}
