import { useState } from "react";
import { HistoryFilters } from "../components/history/HistoryFilters";
import { HistoryTable } from "../components/history/HistoryTable";
import { useScanHistory } from "../hooks/useScanHistory";
import type { ScanHistoryFilters } from "../types";

const DEFAULT_FILTERS: ScanHistoryFilters = { page: 1, page_size: 12 };

export function HistoryPage() {
  const [filters, setFilters] = useState<ScanHistoryFilters>(DEFAULT_FILTERS);
  const { data, isLoading, isError } = useScanHistory(filters);

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-semibold text-white">Scan History</h1>

      <HistoryFilters filters={filters} onChange={setFilters} />

      {isLoading && <p className="text-sm text-slate-400">Loading history…</p>}
      {isError && <p className="text-sm text-severity-severe">Could not load scan history.</p>}

      {data && (
        <>
          <HistoryTable items={data.items} />

          <div className="flex items-center justify-between text-sm text-slate-400">
            <span>
              Page {data.page} of {totalPages} · {data.total} total scans
            </span>
            <div className="flex gap-2">
              <button
                type="button"
                disabled={filters.page <= 1}
                onClick={() => setFilters((prev) => ({ ...prev, page: prev.page - 1 }))}
                className="rounded-md border border-surface-border px-3 py-1 disabled:opacity-40"
              >
                Previous
              </button>
              <button
                type="button"
                disabled={filters.page >= totalPages}
                onClick={() => setFilters((prev) => ({ ...prev, page: prev.page + 1 }))}
                className="rounded-md border border-surface-border px-3 py-1 disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
