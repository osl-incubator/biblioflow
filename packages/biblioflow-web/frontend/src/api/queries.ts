import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  buildMatrix,
  buildNetwork,
  buildPrismaFlow,
  createExport,
  createProject,
  createScreeningRun,
  deleteProject,
  deleteUpload,
  getDataset,
  getDatasetRecords,
  getDatasetSummary,
  getFilterOptions,
  getHealth,
  getPrismaFlow,
  getProject,
  getRemoteSearch,
  getScreeningRun,
  getUpload,
  getValidation,
  importRemoteSource,
  listDatasets,
  listExports,
  listProjects,
  listRemoteSearches,
  listScreeningCandidates,
  listScreeningRuns,
  listUploads,
  loadDataset,
  promoteRemoteCandidates,
  promoteScreeningCandidates,
  previewFilters,
  runOverview,
  searchRemoteSource,
  updateScreeningCandidates,
  updateScreeningCandidatesBulk,
  updateRemoteCandidates,
  uploadFiles,
} from "./client";
import type {
  AnalysisRequest,
  BulkScreeningCandidateDecisionRequest,
  CandidateDecisionRequest,
  CandidatePromotionRequest,
  DatasetLoadRequest,
  ExportRequest,
  FilterSpec,
  MatrixRequest,
  PrismaFlowRequest,
  RemoteSourceImportRequest,
  RemoteSourceSearchRequest,
  ScreeningCandidateDecisionRequest,
  ScreeningCandidatePromotionRequest,
  ScreeningRunCreateRequest,
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

export function useRemoteSearches(projectId?: string | null) {
  return useQuery({
    queryKey: ["projects", projectId, "remote-searches"],
    queryFn: () => listRemoteSearches(projectId as string),
    enabled: Boolean(projectId),
  });
}

export function useRemoteSearch(
  projectId?: string | null,
  searchId?: string | null,
) {
  return useQuery({
    queryKey: ["projects", projectId, "remote-searches", searchId],
    queryFn: () => getRemoteSearch(projectId as string, searchId as string),
    enabled: Boolean(projectId && searchId),
  });
}

export function useScreeningRuns(projectId?: string | null) {
  return useQuery({
    queryKey: ["projects", projectId, "screening-runs"],
    queryFn: () => listScreeningRuns(projectId as string),
    enabled: Boolean(projectId),
  });
}

export function useScreeningRun(
  projectId?: string | null,
  screeningRunId?: string | null,
) {
  return useQuery({
    queryKey: ["projects", projectId, "screening-runs", screeningRunId],
    queryFn: () =>
      getScreeningRun(projectId as string, screeningRunId as string),
    enabled: Boolean(projectId && screeningRunId),
  });
}

export function useScreeningCandidates(projectId?: string | null) {
  return useQuery({
    queryKey: ["projects", projectId, "screening-candidates"],
    queryFn: () => listScreeningCandidates(projectId as string),
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

export function usePrismaFlow(
  projectId?: string | null,
  datasetId?: string | null,
) {
  return useQuery({
    queryKey: ["projects", projectId, "datasets", datasetId, "prisma"],
    queryFn: () => getPrismaFlow(projectId as string, datasetId),
    enabled: Boolean(projectId && datasetId),
  });
}

export function useBuildPrismaFlow(projectId?: string | null) {
  return useMutation({
    mutationFn: (payload: PrismaFlowRequest) =>
      buildPrismaFlow(projectId as string, payload),
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

export function useImportRemoteSource(projectId?: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: RemoteSourceImportRequest) =>
      importRemoteSource(projectId as string, payload),
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

export function useSearchRemoteSource(projectId?: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: RemoteSourceSearchRequest) =>
      searchRemoteSource(projectId as string, payload),
    onSuccess: (response) => {
      const searchId = response.data.search_id;
      queryClient.invalidateQueries({ queryKey: ["projects", projectId] });
      queryClient.invalidateQueries({
        queryKey: ["projects", projectId, "remote-searches"],
      });
      queryClient.setQueryData(
        ["projects", projectId, "remote-searches", searchId],
        response,
      );
    },
  });
}

export function useCreateScreeningRun(projectId?: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ScreeningRunCreateRequest) =>
      createScreeningRun(projectId as string, payload),
    onSuccess: (response) => {
      const screeningRunId = response.data.screening_run_id;
      queryClient.invalidateQueries({ queryKey: ["projects", projectId] });
      queryClient.invalidateQueries({
        queryKey: ["projects", projectId, "screening-runs"],
      });
      queryClient.invalidateQueries({
        queryKey: ["projects", projectId, "screening-candidates"],
      });
      queryClient.setQueryData(
        ["projects", projectId, "screening-runs", screeningRunId],
        response,
      );
    },
  });
}

export function useUpdateScreeningCandidates(
  projectId?: string | null,
  screeningRunId?: string | null,
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ScreeningCandidateDecisionRequest) =>
      updateScreeningCandidates(
        projectId as string,
        screeningRunId as string,
        payload,
      ),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ["projects", projectId] });
      queryClient.invalidateQueries({
        queryKey: ["projects", projectId, "screening-runs"],
      });
      queryClient.invalidateQueries({
        queryKey: ["projects", projectId, "screening-candidates"],
      });
      queryClient.setQueryData(
        ["projects", projectId, "screening-runs", screeningRunId],
        response,
      );
    },
  });
}

export function useUpdateAllScreeningCandidates(projectId?: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: BulkScreeningCandidateDecisionRequest) =>
      updateScreeningCandidatesBulk(projectId as string, payload),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ["projects", projectId] });
      queryClient.invalidateQueries({
        queryKey: ["projects", projectId, "screening-runs"],
      });
      queryClient.setQueryData(
        ["projects", projectId, "screening-candidates"],
        response,
      );
    },
  });
}

export function usePromoteScreeningCandidates(
  projectId?: string | null,
  screeningRunId?: string | null,
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ScreeningCandidatePromotionRequest) =>
      promoteScreeningCandidates(
        projectId as string,
        screeningRunId as string,
        payload,
      ),
    onSuccess: (response) => {
      const datasetId = response.data.dataset_id;
      queryClient.invalidateQueries({ queryKey: ["projects", projectId] });
      queryClient.invalidateQueries({
        queryKey: ["projects", projectId, "datasets"],
      });
      queryClient.invalidateQueries({
        queryKey: ["projects", projectId, "screening-runs"],
      });
      queryClient.invalidateQueries({
        queryKey: ["projects", projectId, "screening-candidates"],
      });
      queryClient.invalidateQueries({
        queryKey: ["projects", projectId, "datasets", datasetId],
      });
    },
  });
}

export function useUpdateRemoteCandidates(
  projectId?: string | null,
  searchId?: string | null,
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CandidateDecisionRequest) =>
      updateRemoteCandidates(projectId as string, searchId as string, payload),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ["projects", projectId] });
      queryClient.invalidateQueries({
        queryKey: ["projects", projectId, "remote-searches"],
      });
      queryClient.setQueryData(
        ["projects", projectId, "remote-searches", searchId],
        response,
      );
    },
  });
}

export function usePromoteRemoteCandidates(
  projectId?: string | null,
  searchId?: string | null,
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CandidatePromotionRequest) =>
      promoteRemoteCandidates(projectId as string, searchId as string, payload),
    onSuccess: (response) => {
      const datasetId = response.data.dataset_id;
      queryClient.invalidateQueries({ queryKey: ["projects", projectId] });
      queryClient.invalidateQueries({
        queryKey: ["projects", projectId, "datasets"],
      });
      queryClient.invalidateQueries({
        queryKey: ["projects", projectId, "remote-searches"],
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
