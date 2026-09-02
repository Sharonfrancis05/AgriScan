import { useEffect, useRef, useState } from "react";

export function CameraCapture({ onCapture }: { onCapture: (file: File) => void }) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [isActive, setIsActive] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const startCamera = async () => {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment" },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setIsActive(true);
    } catch {
      setError("Camera access was denied or is unavailable. Use the upload option instead.");
      setIsActive(false);
    }
  };

  const stopCamera = () => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    setIsActive(false);
  };

  useEffect(() => stopCamera, []);

  const captureFrame = () => {
    const video = videoRef.current;
    if (!video) return;

    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob((blob) => {
      if (blob) {
        onCapture(new File([blob], `capture-${Date.now()}.jpg`, { type: "image/jpeg" }));
      }
    }, "image/jpeg", 0.92);
  };

  return (
    <div className="space-y-3">
      <div className="relative overflow-hidden rounded-lg border border-surface-border bg-black/30">
        {isActive ? (
          <video ref={videoRef} autoPlay playsInline muted className="mx-auto max-h-80 w-full object-contain" />
        ) : (
          <div className="flex h-52 items-center justify-center text-sm text-slate-500">
            Camera preview will appear here
          </div>
        )}
      </div>

      {error && <p className="text-sm text-severity-severe">{error}</p>}

      <div className="flex justify-center gap-3">
        {!isActive ? (
          <button
            type="button"
            onClick={startCamera}
            className="rounded-md bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-dark"
          >
            Start Camera
          </button>
        ) : (
          <>
            <button
              type="button"
              onClick={captureFrame}
              className="rounded-md bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-dark"
            >
              Capture Photo
            </button>
            <button
              type="button"
              onClick={stopCamera}
              className="rounded-md border border-surface-border px-4 py-2 text-sm text-slate-300 hover:bg-surface-border"
            >
              Stop
            </button>
          </>
        )}
      </div>
    </div>
  );
}
