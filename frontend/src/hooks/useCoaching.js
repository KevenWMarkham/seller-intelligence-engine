import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getCoachingHistory, startRoleplay, updateTaskStatus } from "../api/client";

export function useCoachingHistory(sellerId) {
  return useQuery({
    queryKey: ["coaching", sellerId],
    queryFn: () => getCoachingHistory(sellerId),
    enabled: !!sellerId,
  });
}

export function useStartRoleplay() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ sellerId, taskId }) => startRoleplay(sellerId, taskId),
    onSuccess: (_, { sellerId }) => {
      queryClient.invalidateQueries({ queryKey: ["coaching", sellerId] });
    },
  });
}

export function useUpdateTaskStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ taskId, status, notes }) => updateTaskStatus(taskId, status, notes),
    onSuccess: (_, { taskId }) => {
      queryClient.invalidateQueries({ queryKey: ["task", String(taskId)] });
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
    },
  });
}
