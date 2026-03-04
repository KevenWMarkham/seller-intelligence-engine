import { useQuery } from "@tanstack/react-query";
import { getTasks } from "../api/client";

export function useTasks(sellerId, filters = {}) {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["tasks", sellerId, filters],
    queryFn: () => getTasks(sellerId, filters),
    enabled: !!sellerId,
    refetchInterval: 60_000, // Refresh every 60 seconds
  });

  return {
    tasks: data?.tasks ?? [],
    count: data?.count ?? 0,
    isLoading,
    error,
    refetch,
  };
}
