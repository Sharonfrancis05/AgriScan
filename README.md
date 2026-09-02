# AgriVision

AI-based multi-crop leaf disease detection, severity estimation, and
automated PDF report generation. Users capture or upload a leaf photo; the
app identifies the plant species and disease, segments the infected region,
estimates % infected leaf area, classifies severity, gives treatment and
prevention recommendations, and generates a downloadable PDF report — with
full scan history and a dashboard.

**Supported crops**: Apple, Grape, Corn, Tomato, Strawberry, Peach.

## Stack

| Layer | Tech |
|---|---|
| Frontend | React, TypeScript, Tailwind CSS, Vite |
| Backend | FastAPI (Python) |
| Database | MySQL |
| Deep learning | PyTorch, EfficientNet-B0 (classification) |
| Segmentation | Classical OpenCV pipeline today, U-Net staged for later — see [docs/segmentation_upgrade.md](docs/segmentation_upgrade.md) |
| PDF generation | ReportLab |

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

Backend: http://localhost:8000/docs · Frontend: http://localhost:80 (or
http://localhost:5173 in dev mode — see [docs/setup_dev.md](docs/setup_dev.md)).

## Documentation

- [docs/architecture.md](docs/architecture.md) — folder structure, request flow, why the ML pipeline is one seam
- [docs/ml_pipeline.md](docs/ml_pipeline.md) — preprocessing → classification → segmentation → severity → recommendations
- [docs/segmentation_upgrade.md](docs/segmentation_upgrade.md) — the honest limitation (no lesion masks in public datasets) and the staged U-Net upgrade path
- [docs/database_schema.md](docs/database_schema.md) — MySQL schema
- [docs/api_reference.md](docs/api_reference.md) — REST endpoints
- [docs/setup_dev.md](docs/setup_dev.md) — local dev setup, running tests, preparing your dataset, training

## Project status

The application is fully wired end-to-end (frontend, backend, database, PDF
reports, dashboard, history) and runs today without any trained model
weights — the classifier falls back to an ImageNet-pretrained backbone with
an untrained head, and this is disclosed everywhere (`model_status` field,
UI banner, PDF footnote) rather than hidden. To get real predictions, prepare
your dataset and train the classifier per
[docs/setup_dev.md](docs/setup_dev.md).
