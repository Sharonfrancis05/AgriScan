import { apiGet, apiPostForm } from "./client";
import type { PaginatedScans, ScanHistoryFilters, ScanResult } from "../types";

export async function submitScan(file: File): Promise<ScanResult> {
  const formData = new FormData();
  formData.append("image", file);
  return apiPostForm<ScanResult>("/scans", formData);
}

export async function fetchScan(scanUuid: string): Promise<ScanResult> {
  return apiGet<ScanResult>(`/scans/${scanUuid}`);
}

export async function fetchScanHistory(filters: ScanHistoryFilters): Promise<PaginatedScans> {
  return apiGet<PaginatedScans>("/scans", {
    crop: filters.crop,
    severity: filters.severity,
    date_from: filters.date_from,
    date_to: filters.date_to,
    page: filters.page,
    page_size: filters.page_size,
  });
}
