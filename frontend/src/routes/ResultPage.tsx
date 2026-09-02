import { useParams } from "react-router-dom";
import { ScanResultView } from "../components/result/ScanResultView";
import { useScanDetail } from "../hooks/useScanHistory";

export function ResultPage() {
  const { scanUuid } = useParams<{ scanUuid: string }>();
  const { data, isLoading, isError } = useScanDetail(scanUuid);

  if (isLoading) {
    return <p className="text-sm text-slate-400">Loading result…</p>;
  }
  if (isError || !data) {
    return <p className="text-sm text-severity-severe">Could not load this scan result.</p>;
  }

  return <ScanResultView result={data} />;
}
