import { useQuery } from "@tanstack/react-query";
import { fetchScan, fetchScanHistory } from "../api/scans";
import type { ScanHistoryFilters } from "../types";

export function useScanHistory(filters: ScanHistoryFilters) {
  return useQuery({
    queryKey: ["scan-history", filters],
    queryFn: () => fetchScanHistory(filters),
    placeholderData: (previousData) => previousData,
  });
}

export function useScanDetail(scanUuid: string | undefined) {
  return useQuery({
    queryKey: ["scan-detail", scanUuid],
    queryFn: () => fetchScan(scanUuid as string),
    enabled: Boolean(scanUuid),
  });
}
