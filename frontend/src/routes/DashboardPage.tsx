import { CropDistributionChart } from "../components/dashboard/CropDistributionChart";
import { SeverityTrendChart } from "../components/dashboard/SeverityTrendChart";
import { StatsCards } from "../components/dashboard/StatsCards";
import { useDashboardStats } from "../hooks/useDashboardStats";

export function DashboardPage() {
  const { data, isLoading, isError } = useDashboardStats();

  if (isLoading) {
    return <p className="text-sm text-slate-400">Loading dashboard…</p>;
  }
  if (isError || !data) {
    return <p className="text-sm text-severity-severe">Could not load dashboard stats.</p>;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-white">Dashboard</h1>

      <StatsCards
        totalScans={data.total_scans}
        severityBreakdown={data.severity_breakdown}
        mostCommonDiseases={data.most_common_diseases}
      />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="rounded-lg border border-surface-border bg-surface-raised p-4">
          <p className="mb-2 text-sm text-slate-400">Scan Volume Over Time</p>
          <SeverityTrendChart data={data.trend_over_time} />
        </div>
        <div className="rounded-lg border border-surface-border bg-surface-raised p-4">
          <p className="mb-2 text-sm text-slate-400">Scans by Crop</p>
          <CropDistributionChart data={data.crop_breakdown} />
        </div>
      </div>
    </div>
  );
}
