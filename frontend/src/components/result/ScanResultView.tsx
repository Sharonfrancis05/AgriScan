import { reportDownloadUrl } from "../../api/client";
import type { ScanResult } from "../../types";
import { OverlayImageViewer } from "./OverlayImageViewer";
import { RecommendationPanel } from "./RecommendationPanel";
import { SeverityBadge } from "./SeverityBadge";

export function ScanResultView({ result }: { result: ScanResult }) {
  const scannedAt = new Date(result.created_at).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-white">
            {result.crop_name} — {result.disease_display_name}
          </h1>
          <p className="text-sm text-slate-400">
            Report {result.report_id} · Scanned {scannedAt}
          </p>
        </div>
        <SeverityBadge severity={result.severity} />
      </div>

      {result.prediction_warning && (
        <div className="rounded-md border border-severity-severe/40 bg-severity-severe/10 px-4 py-3 text-sm text-severity-severe">
          <strong>Reliability warning:</strong> {result.prediction_warning}
        </div>
      )}

      {result.model_status === "pretrained_backbone_untrained_head" && (
        <div className="rounded-md border border-severity-mild/40 bg-severity-mild/10 px-4 py-3 text-sm text-severity-mild">
          This result was produced by an ImageNet-pretrained backbone with an <strong>untrained</strong>{" "}
          classification head — no fine-tuned checkpoint has been trained yet. Treat this prediction as a
          pipeline smoke-test, not a real diagnosis, until <code>models_store/classifier_best.pt</code>{" "}
          exists.
        </div>
      )}

      <OverlayImageViewer originalUrl={result.original_image_url} overlayUrl={result.overlay_image_url} />

      <div className="grid grid-cols-2 gap-3 rounded-lg border border-surface-border bg-surface-raised p-4 sm:grid-cols-4">
        <div>
          <p className="text-xs text-slate-500">Confidence</p>
          <p className="tabular-nums text-lg font-semibold text-white">
            {(result.confidence * 100).toFixed(1)}%
          </p>
        </div>
        <div>
          <p className="text-xs text-slate-500">Affected Area</p>
          <p className="tabular-nums text-lg font-semibold text-white">
            {result.infected_area_pct.toFixed(1)}%
          </p>
        </div>
        <div>
          <p className="text-xs text-slate-500">Plant Species</p>
          <p className="text-lg font-semibold text-white">{result.crop_name}</p>
        </div>
        <div>
          <p className="text-xs text-slate-500">Severity</p>
          <p className="text-lg font-semibold text-white">{result.severity}</p>
        </div>
      </div>

      <RecommendationPanel recommendations={result.recommendations} />

      <a
        href={reportDownloadUrl(result.report_id)}
        className="inline-block rounded-md bg-brand px-4 py-2.5 text-sm font-semibold text-white hover:bg-brand-dark"
      >
        Download PDF Report
      </a>
    </div>
  );
}
