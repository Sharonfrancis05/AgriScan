import { Link } from "react-router-dom";
import { resolveStaticUrl } from "../../api/client";
import { SeverityBadge } from "../result/SeverityBadge";
import type { ScanSummary } from "../../types";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export function HistoryTable({ items }: { items: ScanSummary[] }) {
  if (items.length === 0) {
    return (
      <div className="flex h-40 items-center justify-center rounded-lg border border-surface-border text-sm text-slate-500">
        No scans match these filters yet.
      </div>
    );
  }

  return (
    <>
      {/* Table view: md and up */}
      <div className="hidden overflow-x-auto rounded-lg border border-surface-border md:block">
        <table className="w-full text-left text-sm">
          <thead className="bg-surface-raised text-xs uppercase text-slate-400">
            <tr>
              <th className="px-4 py-3">Image</th>
              <th className="px-4 py-3">Crop</th>
              <th className="px-4 py-3">Disease</th>
              <th className="px-4 py-3">Confidence</th>
              <th className="px-4 py-3">Affected Area</th>
              <th className="px-4 py-3">Severity</th>
              <th className="px-4 py-3">Scanned</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-surface-border">
            {items.map((scan) => (
              <tr key={scan.scan_uuid} className="hover:bg-surface-raised/60">
                <td className="px-4 py-2">
                  <Link to={`/history/${scan.scan_uuid}`}>
                    <img
                      src={resolveStaticUrl(scan.overlay_image_url)}
                      alt=""
                      className="h-12 w-12 rounded object-cover"
                    />
                  </Link>
                </td>
                <td className="px-4 py-2">{scan.crop_name}</td>
                <td className="px-4 py-2">
                  <Link to={`/history/${scan.scan_uuid}`} className="text-brand-light hover:underline">
                    {scan.disease_display_name}
                  </Link>
                </td>
                <td className="px-4 py-2 tabular-nums">{(scan.confidence * 100).toFixed(1)}%</td>
                <td className="px-4 py-2 tabular-nums">{scan.infected_area_pct.toFixed(1)}%</td>
                <td className="px-4 py-2">
                  <div className="flex items-center gap-1.5">
                    <SeverityBadge severity={scan.severity} />
                    {scan.prediction_warning && (
                      <span title={scan.prediction_warning} className="text-severity-severe" aria-label="Reliability warning">
                        ⚠
                      </span>
                    )}
                  </div>
                </td>
                <td className="px-4 py-2 text-slate-400">{formatDate(scan.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Card view: below md */}
      <div className="space-y-3 md:hidden">
        {items.map((scan) => (
          <Link
            key={scan.scan_uuid}
            to={`/history/${scan.scan_uuid}`}
            className="flex gap-3 rounded-lg border border-surface-border bg-surface-raised p-3"
          >
            <img
              src={resolveStaticUrl(scan.overlay_image_url)}
              alt=""
              className="h-16 w-16 flex-shrink-0 rounded object-cover"
            />
            <div className="min-w-0 flex-1 space-y-1">
              <div className="flex items-center justify-between gap-2">
                <span className="truncate text-sm font-medium text-slate-100">
                  {scan.crop_name} — {scan.disease_display_name}
                  {scan.prediction_warning && (
                    <span title={scan.prediction_warning} className="ml-1 text-severity-severe" aria-label="Reliability warning">
                      ⚠
                    </span>
                  )}
                </span>
                <SeverityBadge severity={scan.severity} />
              </div>
              <p className="text-xs text-slate-400">
                {(scan.confidence * 100).toFixed(1)}% confidence · {scan.infected_area_pct.toFixed(1)}% affected
              </p>
              <p className="text-xs text-slate-500">{formatDate(scan.created_at)}</p>
            </div>
          </Link>
        ))}
      </div>
    </>
  );
}
