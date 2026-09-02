import { useQuery } from "@tanstack/react-query";
import { fetchDashboardStats } from "../api/dashboard";

export function useDashboardStats(dateFrom?: string, dateTo?: string) {
  return useQuery({
    queryKey: ["dashboard-stats", dateFrom, dateTo],
    queryFn: () => fetchDashboardStats(dateFrom, dateTo),
  });
}
