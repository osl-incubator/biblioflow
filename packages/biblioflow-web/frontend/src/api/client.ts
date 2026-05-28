import type {
  AnalysisOverview,
  AnalysisRequest,
  ApiEnvelope,
  ApiErrorPayload,
  BibliographicRecord,
  CandidateDecisionRequest,
  CandidatePromotionRequest,
  DatasetListItem,
  DatasetLoadRequest,
  DatasetPayload,
  DatasetSummary,
  ExportArtifact,
  ExportRequest,
  FilterOptions,
  FilterPreview,
  FilterSpec,
  HealthResponse,
  MatrixRequest,
  MatrixResult,
  NetworkResult,
  PrismaFlowPayload,
  PrismaFlowRequest,
  Project,
  RemoteSearchListItem,
  RemoteSearchPayload,
  RemoteSourceImportRequest,
  RemoteSourceSearchRequest,
  Upload,
  ValidationPayload,
} from "./types";

const API_BASE_URL = import.meta.env.VITE_BIBLIOFLOW_WEB_API_BASE_URL ?? "/api";

async function parseError(response: Response): Promise<Error> {
  const payload = (await response.json().catch(() => ({}))) as ApiErrorPayload;
  return new Error(
    payload.error?.message ?? `Request failed: ${response.status}`,
  );
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  if (!response.ok) {
    throw await parseError(response);
  }
  return response.json() as Promise<T>;
}

async function multipartRequest<T>(
  path: string,
  formData: FormData,
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    throw await parseError(response);
  }
  return response.json() as Promise<T>;
}

export async function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/health");
}

export async function listProjects(): Promise<ApiEnvelope<Project[]>> {
  return request<ApiEnvelope<Project[]>>("/projects");
}

export async function createProject(
  name: string,
): Promise<ApiEnvelope<Project>> {
  return request<ApiEnvelope<Project>>("/projects", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
}

export async function getProject(
  projectId: string,
): Promise<ApiEnvelope<Project>> {
  return request<ApiEnvelope<Project>>(`/projects/${projectId}`);
}

export async function deleteProject(
  projectId: string,
): Promise<ApiEnvelope<{ deleted: boolean }>> {
  return request<ApiEnvelope<{ deleted: boolean }>>(`/projects/${projectId}`, {
    method: "DELETE",
  });
}

export async function listUploads(
  projectId: string,
): Promise<ApiEnvelope<Upload[]>> {
  return request<ApiEnvelope<Upload[]>>(`/projects/${projectId}/uploads`);
}

export async function getUpload(
  projectId: string,
  uploadId: string,
): Promise<ApiEnvelope<Upload>> {
  return request<ApiEnvelope<Upload>>(
    `/projects/${projectId}/uploads/${uploadId}`,
  );
}

export async function uploadFiles(
  projectId: string,
  files: File[],
): Promise<ApiEnvelope<Upload[]>> {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));
  return multipartRequest<ApiEnvelope<Upload[]>>(
    `/projects/${projectId}/uploads`,
    formData,
  );
}

export async function deleteUpload(
  projectId: string,
  uploadId: string,
): Promise<ApiEnvelope<{ deleted: boolean }>> {
  return request<ApiEnvelope<{ deleted: boolean }>>(
    `/projects/${projectId}/uploads/${uploadId}`,
    { method: "DELETE" },
  );
}

export async function loadDataset(
  projectId: string,
  payload: DatasetLoadRequest,
): Promise<ApiEnvelope<DatasetPayload>> {
  return request<ApiEnvelope<DatasetPayload>>(
    `/projects/${projectId}/datasets/load`,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export async function importRemoteSource(
  projectId: string,
  payload: RemoteSourceImportRequest,
): Promise<ApiEnvelope<DatasetPayload>> {
  return request<ApiEnvelope<DatasetPayload>>(
    `/projects/${projectId}/sources/import`,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export async function searchRemoteSource(
  projectId: string,
  payload: RemoteSourceSearchRequest,
): Promise<ApiEnvelope<RemoteSearchPayload>> {
  return request<ApiEnvelope<RemoteSearchPayload>>(
    `/projects/${projectId}/sources/search`,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export async function listRemoteSearches(
  projectId: string,
): Promise<ApiEnvelope<RemoteSearchListItem[]>> {
  return request<ApiEnvelope<RemoteSearchListItem[]>>(
    `/projects/${projectId}/sources/searches`,
  );
}

export async function getRemoteSearch(
  projectId: string,
  searchId: string,
): Promise<ApiEnvelope<RemoteSearchPayload>> {
  return request<ApiEnvelope<RemoteSearchPayload>>(
    `/projects/${projectId}/sources/searches/${searchId}`,
  );
}

export async function updateRemoteCandidates(
  projectId: string,
  searchId: string,
  payload: CandidateDecisionRequest,
): Promise<ApiEnvelope<RemoteSearchPayload>> {
  return request<ApiEnvelope<RemoteSearchPayload>>(
    `/projects/${projectId}/sources/searches/${searchId}/candidates`,
    { method: "PATCH", body: JSON.stringify(payload) },
  );
}

export async function promoteRemoteCandidates(
  projectId: string,
  searchId: string,
  payload: CandidatePromotionRequest,
): Promise<ApiEnvelope<DatasetPayload>> {
  return request<ApiEnvelope<DatasetPayload>>(
    `/projects/${projectId}/sources/searches/${searchId}/promote`,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export async function listDatasets(
  projectId: string,
): Promise<ApiEnvelope<DatasetListItem[]>> {
  return request<ApiEnvelope<DatasetListItem[]>>(
    `/projects/${projectId}/datasets`,
  );
}

export async function getDataset(
  projectId: string,
  datasetId: string,
): Promise<ApiEnvelope<DatasetPayload>> {
  return request<ApiEnvelope<DatasetPayload>>(
    `/projects/${projectId}/datasets/${datasetId}`,
  );
}

export async function getDatasetSummary(
  projectId: string,
  datasetId: string,
): Promise<ApiEnvelope<DatasetSummary>> {
  return request<ApiEnvelope<DatasetSummary>>(
    `/projects/${projectId}/datasets/${datasetId}/summary`,
  );
}

export async function getDatasetRecords(
  projectId: string,
  datasetId: string,
): Promise<ApiEnvelope<BibliographicRecord[]>> {
  return request<ApiEnvelope<BibliographicRecord[]>>(
    `/projects/${projectId}/datasets/${datasetId}/records`,
  );
}

export async function getValidation(
  projectId: string,
  datasetId: string,
): Promise<ApiEnvelope<ValidationPayload>> {
  return request<ApiEnvelope<ValidationPayload>>(
    `/projects/${projectId}/datasets/${datasetId}/validation`,
  );
}

export async function getFilterOptions(
  projectId: string,
  datasetId: string,
): Promise<ApiEnvelope<FilterOptions>> {
  return request<ApiEnvelope<FilterOptions>>(
    `/projects/${projectId}/datasets/${datasetId}/filters/options`,
  );
}

export async function previewFilters(
  projectId: string,
  datasetId: string,
  filters: FilterSpec,
): Promise<ApiEnvelope<FilterPreview>> {
  return request<ApiEnvelope<FilterPreview>>(
    `/projects/${projectId}/datasets/${datasetId}/filters/preview`,
    { method: "POST", body: JSON.stringify({ filters }) },
  );
}

export async function runOverview(
  projectId: string,
  datasetId: string,
  payload: AnalysisRequest,
): Promise<ApiEnvelope<AnalysisOverview>> {
  return request<ApiEnvelope<AnalysisOverview>>(
    `/projects/${projectId}/datasets/${datasetId}/analysis/overview`,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export async function buildMatrix(
  projectId: string,
  datasetId: string,
  payload: MatrixRequest,
): Promise<ApiEnvelope<MatrixResult>> {
  return request<ApiEnvelope<MatrixResult>>(
    `/projects/${projectId}/datasets/${datasetId}/matrices`,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export async function buildNetwork(
  projectId: string,
  datasetId: string,
  payload: MatrixRequest,
): Promise<ApiEnvelope<NetworkResult>> {
  return request<ApiEnvelope<NetworkResult>>(
    `/projects/${projectId}/datasets/${datasetId}/networks`,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export async function getPrismaFlow(
  projectId: string,
  datasetId?: string | null,
): Promise<ApiEnvelope<PrismaFlowPayload>> {
  const query = datasetId ? `?dataset_id=${encodeURIComponent(datasetId)}` : "";
  return request<ApiEnvelope<PrismaFlowPayload>>(
    `/projects/${projectId}/prisma${query}`,
  );
}

export async function buildPrismaFlow(
  projectId: string,
  payload: PrismaFlowRequest,
): Promise<ApiEnvelope<PrismaFlowPayload>> {
  return request<ApiEnvelope<PrismaFlowPayload>>(
    `/projects/${projectId}/prisma`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export async function listExports(
  projectId: string,
): Promise<ApiEnvelope<ExportArtifact[]>> {
  return request<ApiEnvelope<ExportArtifact[]>>(
    `/projects/${projectId}/exports`,
  );
}

export async function createExport(
  projectId: string,
  payload: ExportRequest,
): Promise<ApiEnvelope<ExportArtifact>> {
  return request<ApiEnvelope<ExportArtifact>>(
    `/projects/${projectId}/exports`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export function downloadExportUrl(projectId: string, filename: string): string {
  return `${API_BASE_URL}/projects/${projectId}/exports/${encodeURIComponent(
    filename,
  )}/download`;
}
