import type { RecommendationBlock } from "../../types";

export function RecommendationPanel({ recommendations }: { recommendations: RecommendationBlock }) {
  return (
    <div className="space-y-4">
      {recommendations.urgency_note && (
        <div className="rounded-md border border-severity-critical/40 bg-severity-critical/10 px-4 py-3 text-sm text-severity-critical">
          <strong>Urgent:</strong> {recommendations.urgency_note}
        </div>
      )}
      <div>
        <h3 className="mb-1 text-sm font-semibold text-slate-200">Treatment</h3>
        <p className="text-sm leading-relaxed text-slate-400">{recommendations.treatment}</p>
      </div>
      <div>
        <h3 className="mb-1 text-sm font-semibold text-slate-200">Prevention</h3>
        <p className="text-sm leading-relaxed text-slate-400">{recommendations.prevention}</p>
      </div>
    </div>
  );
}
