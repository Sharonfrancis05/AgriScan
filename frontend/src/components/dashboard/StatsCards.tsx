import type { BreakdownItem } from "../../types";
import { SeverityBadge } from "../result/SeverityBadge";
import type { Severity } from "../../types";
import { SEVERITY_LEVELS } from "../../types";

function severityCount(breakdown: BreakdownItem[], severity: Severity): number {
  return breakdown.find((item) => item.label === severity)?.count ?? 0;
}

export function StatsCards({
  totalScans,
  severityBreakdown,
  mostCommonDiseases,
}: {
  totalScans: number;
  severityBreakdown: BreakdownItem[];
  mostCommonDiseases: BreakdownItem[];
}) {
  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
      <div className="rounded-lg border border-surface-border bg-surface-raised p-5">
        <p className="text-sm text-slate-400">Total Scans</p>
        <p className="mt-1 text-4xl font-semibold tabular-nums text-white">{totalScans}</p>
      </div>

      <div className="rounded-lg border border-surface-border bg-surface-raised p-5 md:col-span-2">
        <p className="mb-3 text-sm text-slate-400">Severity Breakdown</p>
        <div className="flex flex-wrap gap-3">
          {SEVERITY_LEVELS.map((severity) => (
            <div key={severity} className="flex items-center gap-2">
              <SeverityBadge severity={severity} />
              <span className="tabular-nums text-sm text-slate-300">
                {severityCount(severityBreakdown, severity)}
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-lg border border-surface-border bg-surface-raised p-5 md:col-span-3">
        <p className="mb-3 text-sm text-slate-400">Most Common Diseases</p>
        {mostCommonDiseases.length === 0 ? (
          <p className="text-sm text-slate-500">No diseased scans recorded yet.</p>
        ) : (
          <ol className="space-y-1.5">
            {mostCommonDiseases.map((item, index) => (
              <li key={item.label} className="flex items-center justify-between text-sm">
                <span className="text-slate-300">
                  <span className="mr-2 text-slate-500">{index + 1}.</span>
                  {item.label}
                </span>
                <span className="tabular-nums text-slate-400">{item.count}</span>
              </li>
            ))}
          </ol>
        )}
      </div>
    </div>
  );
}
