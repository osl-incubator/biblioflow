import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  buildMatrix,
  buildNetwork,
  createExport,
  createProject,
  deleteProject,
  deleteUpload,
  getDataset,
  getDatasetRecords,
  getDatasetSummary,
  getFilterOptions,
  getHealth,
  getProject,
  getUpload,
  getValidation,
  listDatasets,
  listExports,
  listProjects,
  listUploads,
  loadDataset,
  previewFilters,
  runOverview,
  uploadFiles,
} from "./client";
import type {
  AnalysisRequest,
  DatasetLoadRequest,
  ExportRequest,
  FilterSpec,
  MatrixRequest,
} from "./types";

export function useHealth() {
  return useQuery({ queryKey: ["health"], queryFn: getHealth });
}

export function useProjects() {
  return useQuery({ queryKey: ["projects"], queryFn: listProjects });
}

export function useProject(projectId?: string | null) {
  return useQuery({
    queryKey: ["projects", projectId],
    queryFn: () => getProject(projectId as string),
    enabled: Boolean(projectId),
  });
}

export function useUploads(projectId?: string | null) {
  return useQuery({
    queryKey: ["projects", projectId, "uploads"],
    queryFn: () => listUploads(projectId as string),
    enabled: Boolean(projectId),
  });
}

export function useUpload(projectId?: string | null, uploadId?: string | null) {
  return useQuery({
    queryKey: ["projects", projectId, "uploads", uploadId],
    queryFn: () => getUpload(projectId as string, uploadId as string),
    enabled: Boolean(projectId && uploadId),
  });
}

export function useDatasets(projectId?: string | null) {
  return useQuery({
    queryKey: ["projects", projectId, "datasets"],
    queryFn: () => listDatasets(projectId as string),
    enabled: Boolean(projectId),
  });
}

export function useDataset(
  projectId?: string | null,
  datasetId?: string | null,
) {
  return useQuery({
    queryKey: ["projects", projectId, "datasets", datasetId],
    queryFn: () => getDataset(projectId as string, datasetId as string),
    enabled: Boolean(projectId && datasetId),
  });
}

export function useDatasetSummary(
  projectId?: string | null,
  datasetId?: string | null,
) {
  return useQuery({
    queryKey: ["projects", projectId, "datasets", datasetId, "summary"],
    queryFn: () => getDatasetSummary(projectId as string, datasetId as string),
    enabled: Boolean(projectId && datasetId),
  });
}

export function useDatasetRecords(
  projectId?: string | null,
  datasetId?: string | null,
) {
  return useQuery({
    queryKey: ["projects", projectId, "datasets", datasetId, "records"],
    queryFn: () => getDatasetRecords(projectId as string, datasetId as string),
    enabled: Boolean(projectId && datasetId),
  });
}

export function useValidation(
  projectId?: string | null,
  datasetId?: string | null,
) {
  return useQuery({
    queryKey: ["projects", projectId, "datasets", datasetId, "validation"],
    queryFn: () => getValidation(projectId as string, datasetId as string),
    enabled: Boolean(projectId && datasetId),
  });
}

export function useFilterOptions(
  projectId?: string | null,
  datasetId?: string | null,
) {
  return useQuery({
    queryKey: [
      "projects",
      projectId,
      "datasets",
      datasetId,
      "filters",
      "options",
    ],
    queryFn: () => getFilterOptions(projectId as string, datasetId as string),
    enabled: Boolean(projectId && datasetId),
  });
}

export function useFilterPreview(
  projectId?: string | null,
  datasetId?: string | null,
) {
  return useMutation({
    mutationFn: (filters: FilterSpec) =>
      previewFilters(projectId as string, datasetId as string, filters),
  });
}

export function useOverviewAnalysis(
  projectId?: string | null,
  datasetId?: string | null,
  request: AnalysisRequest = { top_n: 20, filters: {} },
) {
  return useQuery({
    queryKey: [
      "projects",
      projectId,
      "datasets",
      datasetId,
      "analysis",
      "overview",
      request,
    ],
    queryFn: () =>
      runOverview(projectId as string, datasetId as string, request),
    enabled: Boolean(projectId && datasetId),
  });
}

export function useMatrix(
  projectId?: string | null,
  datasetId?: string | null,
) {
  return useMutation({
    mutationFn: (request: MatrixRequest) =>
      buildMatrix(projectId as string, datasetId as string, request),
  });
}

export function useNetwork(
  projectId?: string | null,
  datasetId?: string | null,
) {
  return useMutation({
    mutationFn: (request: MatrixRequest) =>
      buildNetwork(projectId as string, datasetId as string, request),
  });
}

export function useExports(projectId?: string | null) {
  return useQuery({
    queryKey: ["projects", projectId, "exports"],
    queryFn: () => listExports(projectId as string),
    enabled: Boolean(projectId),
  });
}

export function useCreateProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createProject,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["projects"] }),
  });
}

export function useUploadFiles(projectId?: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (files: File[]) => uploadFiles(projectId as string, files),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects", projectId] });
      queryClient.invalidateQueries({
        queryKey: ["projects", projectId, "uploads"],
      });
    },
  });
}

export function useLoadDataset(projectId?: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: DatasetLoadRequest) =>
      loadDataset(projectId as string, payload),
    onSuccess: (response) => {
      const datasetId = response.data.dataset_id;
      queryClient.invalidateQueries({ queryKey: ["projects", projectId] });
      queryClient.invalidateQueries({
        queryKey: ["projects", projectId, "datasets"],
      });
      queryClient.invalidateQueries({
        queryKey: ["projects", projectId, "datasets", datasetId],
      });
    },
  });
}

export function useCreateExport(projectId?: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ExportRequest) =>
      createExport(projectId as string, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["projects", projectId, "exports"],
      });
    },
  });
}

export function useDeleteProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteProject,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["projects"] }),
  });
}

export function useDeleteUpload(projectId?: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (uploadId: string) =>
      deleteUpload(projectId as string, uploadId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects", projectId] });
      queryClient.invalidateQueries({
        queryKey: ["projects", projectId, "uploads"],
      });
    },
  });
}
