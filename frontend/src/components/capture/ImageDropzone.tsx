import { useRef, useState, type DragEvent } from "react";

const MAX_SIZE_BYTES = 15 * 1024 * 1024;
const ACCEPTED_TYPES = ["image/jpeg", "image/png", "image/webp"];

export function ImageDropzone({ onSelect }: { onSelect: (file: File) => void }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const validateAndSelect = (file: File) => {
    if (!ACCEPTED_TYPES.includes(file.type)) {
      setError("Only JPEG, PNG, or WEBP images are supported.");
      return;
    }
    if (file.size > MAX_SIZE_BYTES) {
      setError("Image exceeds the 15MB upload limit.");
      return;
    }
    setError(null);
    onSelect(file);
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);
    const file = event.dataTransfer.files?.[0];
    if (file) validateAndSelect(file);
  };

  return (
    <div className="space-y-2">
      <div
        onDragOver={(event) => {
          event.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`flex h-40 cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed text-sm transition-colors ${
          isDragging
            ? "border-brand bg-brand/10 text-brand-light"
            : "border-surface-border text-slate-400 hover:border-brand/50"
        }`}
      >
        <p>Drag &amp; drop a leaf image here</p>
        <p className="text-xs text-slate-500">or click to browse (JPEG/PNG/WEBP, max 15MB)</p>
      </div>
      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        className="hidden"
        onChange={(event) => {
          const file = event.target.files?.[0];
          if (file) validateAndSelect(file);
          event.target.value = "";
        }}
      />
      {error && <p className="text-sm text-severity-severe">{error}</p>}
    </div>
  );
}
