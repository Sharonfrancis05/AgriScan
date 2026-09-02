import { SEVERITY_LEVELS, SUPPORTED_CROPS } from "../../types";
import type { ScanHistoryFilters } from "../../types";

export function HistoryFilters({
  filters,
  onChange,
}: {
  filters: ScanHistoryFilters;
  onChange: (next: ScanHistoryFilters) => void;
}) {
  return (
    <div className="flex flex-wrap items-end gap-3 rounded-lg border border-surface-border bg-surface-raised p-4">
      <label className="flex flex-col gap-1 text-xs text-slate-400">
        Crop
        <select
          value={filters.crop ?? ""}
          onChange={(event) => onChange({ ...filters, crop: event.target.value || undefined, page: 1 })}
          className="rounded-md border border-surface-border bg-surface px-2 py-1.5 text-sm text-slate-200"
        >
          <option value="">All crops</option>
          {SUPPORTED_CROPS.map((crop) => (
            <option key={crop} value={crop}>
              {crop}
            </option>
          ))}
        </select>
      </label>

      <label className="flex flex-col gap-1 text-xs text-slate-400">
        Severity
        <select
          value={filters.severity ?? ""}
          onChange={(event) =>
            onChange({
              ...filters,
              severity: (event.target.value || undefined) as ScanHistoryFilters["severity"],
              page: 1,
            })
          }
          className="rounded-md border border-surface-border bg-surface px-2 py-1.5 text-sm text-slate-200"
        >
          <option value="">All severities</option>
          {SEVERITY_LEVELS.map((severity) => (
            <option key={severity} value={severity}>
              {severity}
            </option>
          ))}
        </select>
      </label>

      <label className="flex flex-col gap-1 text-xs text-slate-400">
        From
        <input
          type="date"
          value={filters.date_from ?? ""}
          onChange={(event) => onChange({ ...filters, date_from: event.target.value || undefined, page: 1 })}
          className="rounded-md border border-surface-border bg-surface px-2 py-1.5 text-sm text-slate-200"
        />
      </label>

      <label className="flex flex-col gap-1 text-xs text-slate-400">
        To
        <input
          type="date"
          value={filters.date_to ?? ""}
          onChange={(event) => onChange({ ...filters, date_to: event.target.value || undefined, page: 1 })}
          className="rounded-md border border-surface-border bg-surface px-2 py-1.5 text-sm text-slate-200"
        />
      </label>

      <button
        type="button"
        onClick={() => onChange({ page: 1, page_size: filters.page_size })}
        className="rounded-md border border-surface-border px-3 py-1.5 text-sm text-slate-300 hover:bg-surface-border"
      >
        Clear filters
      </button>
    </div>
  );
}
