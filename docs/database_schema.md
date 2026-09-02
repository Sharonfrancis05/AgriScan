# Database Schema (MySQL)

Managed via Alembic (`backend/alembic/versions/0001_init_schema.py`). Three
tables:

## `diseases_reference`

The recommendation knowledge base — seeded (idempotently, on every backend
startup) from `backend/app/db/fixtures/diseases_reference_seed.json`.

| Column | Type | Notes |
|---|---|---|
| `id` | INT PK | |
| `crop` | VARCHAR(50) | e.g. `Tomato` |
| `disease_code` | VARCHAR(100), unique | e.g. `Tomato___Late_blight` — the classifier's label format, and the join key to `scans` |
| `disease_display_name` | VARCHAR(150) | e.g. `Late Blight` |
| `description` | TEXT | nullable |
| `treatment_text` | TEXT | nullable |
| `prevention_text` | TEXT | nullable |
| `is_healthy_label` | BOOLEAN | true for the `*___healthy` entries |

## `scans`

One row per submitted image + inference result.

| Column | Type | Notes |
|---|---|---|
| `id` | INT PK | |
| `scan_uuid` | CHAR(36), unique | public-facing ID used in URLs |
| `user_id` | INT, nullable | unused today — present so a future auth system can attribute scans without a migration |
| `original_image_path` / `overlay_image_path` | VARCHAR(500) | paths under the `storage/uploads/` volume |
| `crop_name` | VARCHAR(50), indexed | |
| `disease_code` | VARCHAR(100), FK → `diseases_reference.disease_code` | |
| `disease_display_name` | VARCHAR(150) | denormalized for fast list rendering |
| `confidence` | FLOAT | 0–1 |
| `infected_area_pct` | FLOAT | 0–100 |
| `severity` | ENUM(Healthy, Mild, Moderate, Severe, Critical), indexed | |
| `model_version` / `segmentation_backend` / `model_status` | VARCHAR(50), nullable | transparency fields — see `docs/ml_pipeline.md` |
| `created_at` | DATETIME, indexed | |

## `reports`

Modeled separately from `scans` (not just a `pdf_path` column on `scans`) so
a report could be regenerated later without losing scan history.

| Column | Type | Notes |
|---|---|---|
| `id` | INT PK | |
| `report_id` | VARCHAR(30), unique | e.g. `AGV-20260803-0F3A2C` |
| `scan_id` | INT, FK → `scans.id` | |
| `pdf_path` | VARCHAR(500) | path under the `storage/reports/` volume |
| `generated_at` | DATETIME | |
