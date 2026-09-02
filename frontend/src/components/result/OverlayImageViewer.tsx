import { useState } from "react";
import { resolveStaticUrl } from "../../api/client";

export function OverlayImageViewer({
  originalUrl,
  overlayUrl,
}: {
  originalUrl: string;
  overlayUrl: string;
}) {
  const [showOverlay, setShowOverlay] = useState(true);

  return (
    <div className="space-y-2">
      <div className="overflow-hidden rounded-lg border border-surface-border bg-black/20">
        <img
          src={resolveStaticUrl(showOverlay ? overlayUrl : originalUrl)}
          alt={showOverlay ? "Disease-highlighted leaf" : "Original leaf photo"}
          className="mx-auto max-h-96 w-full object-contain"
        />
      </div>
      <div className="flex justify-center gap-2">
        <button
          type="button"
          onClick={() => setShowOverlay(false)}
          className={`rounded-md px-3 py-1 text-xs font-medium ${
            !showOverlay ? "bg-brand text-white" : "bg-surface-border text-slate-300"
          }`}
        >
          Original
        </button>
        <button
          type="button"
          onClick={() => setShowOverlay(true)}
          className={`rounded-md px-3 py-1 text-xs font-medium ${
            showOverlay ? "bg-brand text-white" : "bg-surface-border text-slate-300"
          }`}
        >
          Highlighted
        </button>
      </div>
    </div>
  );
}
