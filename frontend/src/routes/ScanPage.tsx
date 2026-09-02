import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { CameraCapture } from "../components/capture/CameraCapture";
import { ImageDropzone } from "../components/capture/ImageDropzone";
import { useScanSubmit } from "../hooks/useScanSubmit";

type Mode = "camera" | "upload";

export function ScanPage() {
  const [mode, setMode] = useState<Mode>("upload");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const navigate = useNavigate();
  const scanSubmit = useScanSubmit();

  const handleSelect = (file: File) => {
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
  };

  const handleAnalyze = () => {
    if (!selectedFile) return;
    scanSubmit.mutate(selectedFile, {
      onSuccess: (result) => navigate(`/result/${result.scan_uuid}`),
    });
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-white">Scan a Leaf</h1>
        <p className="mt-1 text-sm text-slate-400">
          Capture or upload a photo of a leaf from Apple, Grape, Corn, Tomato, Strawberry, or Peach to
          detect disease, estimate severity, and get treatment recommendations.
        </p>
      </div>

      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => setMode("upload")}
          className={`rounded-md px-4 py-2 text-sm font-medium ${
            mode === "upload" ? "bg-brand text-white" : "bg-surface-raised text-slate-300"
          }`}
        >
          Upload Image
        </button>
        <button
          type="button"
          onClick={() => setMode("camera")}
          className={`rounded-md px-4 py-2 text-sm font-medium ${
            mode === "camera" ? "bg-brand text-white" : "bg-surface-raised text-slate-300"
          }`}
        >
          Use Camera
        </button>
      </div>

      {mode === "upload" ? (
        <ImageDropzone onSelect={handleSelect} />
      ) : (
        <CameraCapture onCapture={handleSelect} />
      )}

      {previewUrl && (
        <div className="space-y-3 rounded-lg border border-surface-border bg-surface-raised p-4">
          <p className="text-sm text-slate-400">Selected image</p>
          <img src={previewUrl} alt="Selected leaf" className="mx-auto max-h-72 rounded object-contain" />
          <button
            type="button"
            onClick={handleAnalyze}
            disabled={scanSubmit.isPending}
            className="w-full rounded-md bg-brand py-2.5 text-sm font-semibold text-white hover:bg-brand-dark disabled:opacity-50"
          >
            {scanSubmit.isPending ? "Analyzing…" : "Analyze Leaf"}
          </button>
          {scanSubmit.isError && (
            <p className="text-sm text-severity-severe">
              {scanSubmit.error instanceof Error ? scanSubmit.error.message : "Something went wrong."}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
