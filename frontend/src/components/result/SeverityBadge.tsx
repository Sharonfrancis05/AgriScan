import type { Severity } from "../../types";

// Solid fill + white text (not colored text on a translucent background):
// each fill is individually WCAG-AA contrast-checked for white text, and the
// severity name is always rendered as a visible label — identity never rests
// on hue alone. See docs/ml_pipeline.md for the underlying % thresholds.
const SEVERITY_STYLES: Record<Severity, string> = {
  Healthy: "bg-severity-healthy",
  Mild: "bg-severity-mild",
  Moderate: "bg-severity-moderate",
  Severe: "bg-severity-severe",
  Critical: "bg-severity-critical",
};

export function SeverityBadge({ severity }: { severity: Severity }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide text-white ${SEVERITY_STYLES[severity]}`}
    >
      {severity}
    </span>
  );
}
