import { useParams } from "react-router-dom";

import { useProject } from "../../api/queries";

export function useActiveWorkspace() {
  const { projectId } = useParams<{ projectId: string }>();
  const projectQuery = useProject(projectId);
  const project = projectQuery.data?.data;
  const activeDatasetId =
    project?.active_dataset_id ?? project?.datasets?.at(-1)?.dataset_id ?? null;

  return {
    projectId: projectId ?? null,
    project,
    projectQuery,
    activeDatasetId,
    hasDataset: Boolean(activeDatasetId),
  };
}
