import { apiGet } from "./client";
import type { DashboardStats } from "../types";

export async function fetchDashboardStats(dateFrom?: string, dateTo?: string): Promise<DashboardStats> {
  return apiGet<DashboardStats>("/dashboard/stats", { date_from: dateFrom, date_to: dateTo });
}
