import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { createProject, getHealth, listProjects } from "./client";

export function useHealth() {
  return useQuery({ queryKey: ["health"], queryFn: getHealth });
}

export function useProjects() {
  return useQuery({ queryKey: ["projects"], queryFn: listProjects });
}

export function useCreateProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createProject,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["projects"] }),
  });
}
