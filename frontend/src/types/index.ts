export type Severity = "Healthy" | "Mild" | "Moderate" | "Severe" | "Critical";

export const SUPPORTED_CROPS = ["Apple", "Grape", "Corn", "Tomato", "Strawberry", "Peach"] as const;
export type SupportedCrop = (typeof SUPPORTED_CROPS)[number];

export const SEVERITY_LEVELS: Severity[] = ["Healthy", "Mild", "Moderate", "Severe", "Critical"];

export interface RecommendationBlock {
  treatment: string;
  prevention: string;
  urgency_note: string | null;
}

export interface ScanResult {
  scan_uuid: string;
  crop_name: string;
  disease_code: string;
  disease_display_name: string;
  confidence: number;
  infected_area_pct: number;
  severity: Severity;
  original_image_url: string;
  overlay_image_url: string;
  report_id: string;
  model_status: string | null;
  prediction_warning: string | null;
  recommendations: RecommendationBlock;
  created_at: string;
}

export interface ScanSummary {
  scan_uuid: string;
  crop_name: string;
  disease_display_name: string;
  confidence: number;
  infected_area_pct: number;
  severity: Severity;
  overlay_image_url: string;
  prediction_warning: string | null;
  created_at: string;
}

export interface PaginatedScans {
  items: ScanSummary[];
  total: number;
  page: number;
  page_size: number;
}

export interface BreakdownItem {
  label: string;
  count: number;
}

export interface TrendPoint {
  date: string;
  count: number;
}

export interface DashboardStats {
  total_scans: number;
  severity_breakdown: BreakdownItem[];
  crop_breakdown: BreakdownItem[];
  trend_over_time: TrendPoint[];
  most_common_diseases: BreakdownItem[];
}

export interface ScanHistoryFilters {
  crop?: string;
  severity?: Severity;
  date_from?: string;
  date_to?: string;
  page: number;
  page_size: number;
}
