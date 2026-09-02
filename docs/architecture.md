# Architecture

AgriVision is a monorepo with two independently deployable services plus a
shared MySQL database:

```
AgriVision/
├── backend/    FastAPI + PyTorch + OpenCV + ReportLab (REST API, ML inference, PDF generation)
├── frontend/   React + TypeScript + Tailwind + Vite (SPA)
└── docs/       this folder
```

## Request flow (a single scan)

1. **Frontend** (`ScanPage.tsx`) captures a photo via `getUserMedia` or accepts
   a drag-and-drop upload, then `POST`s it as `multipart/form-data` to
   `/api/scans`.
2. **`app/routers/scans.py`** validates content-type/size and calls
   `scan_service.create_scan`.
3. **`app/services/scan_service.py`** calls the single ML orchestration seam,
   `InferenceService.run_inference` (`app/services/inference_service.py`),
   which internally:
   - preprocesses the image (`app/ml/preprocessing.py`, OpenCV)
   - classifies crop + disease (`app/ml/classifier.py`, EfficientNet-B0)
   - segments the infected region and computes % infected area
     (`app/ml/segmentation/`, classical CV by default)
   - classifies severity (`app/ml/severity.py`)
   - builds the disease-highlighted overlay image (`app/pdf/overlay_image.py`)
4. `scan_service` persists a `Scan` row, looks up treatment/prevention text
   (`app/services/recommendation_service.py`), and calls
   `app/services/report_service.py` to render the PDF
   (`app/pdf/report_template.py`, ReportLab) and persist a `Report` row.
5. The API returns a `ScanResultResponse` with image URLs, the report ID, and
   recommendations; the frontend renders `ScanResultView` and links to
   `GET /api/reports/{report_id}/download` for the PDF.

## Why one `inference_service` seam

Every ML concern (preprocessing, classification, segmentation, severity,
overlay) is reachable only through `InferenceService.run_inference`. Routers
and `scan_service` never import `app/ml/*` directly. This is what makes the
segmentation backend swappable (`SEGMENTATION_BACKEND=classical_cv|unet` in
`.env`, see `docs/segmentation_upgrade.md`) and the classifier checkpoint
swappable (drop a new `.pt` file in `models_store/`) without touching the API
layer, database layer, or frontend at all.

## Training vs. runtime

`backend/ml_training/` is deliberately separate from `backend/app/`: it is
not imported by the running API and its extra dependencies
(`ml_training/requirements-training.txt`) are not part of the Docker image.
It exists to produce the checkpoints that `app/ml/classifier.py` and
`app/ml/segmentation/unet_backend.py` load from `models_store/`. See
`docs/setup_dev.md` for how to run it against your uploaded dataset.
