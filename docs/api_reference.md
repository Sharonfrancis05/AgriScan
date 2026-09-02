# API Reference

Base path: `/api`. Interactive OpenAPI docs are also available at
`/docs` (Swagger UI) and `/redoc` once the backend is running.

## `POST /api/scans`

Submit a leaf image and run the full pipeline synchronously.

- **Request**: `multipart/form-data` with an `image` field (JPEG/PNG/WEBP,
  ≤15MB).
- **Response** `200`: `ScanResultResponse`
  ```json
  {
    "scan_uuid": "…",
    "crop_name": "Tomato",
    "disease_code": "Tomato___Late_blight",
    "disease_display_name": "Late blight",
    "confidence": 0.87,
    "infected_area_pct": 34.5,
    "severity": "Severe",
    "original_image_url": "/static/uploads/…/original.jpg",
    "overlay_image_url": "/static/uploads/…/overlay.jpg",
    "report_id": "AGV-20260803-0F3A2C",
    "model_status": "fine_tuned",
    "recommendations": { "treatment": "…", "prevention": "…", "urgency_note": null },
    "created_at": "2026-08-03T10:00:00"
  }
  ```
- **Errors**: `415` unsupported content type, `413` over the size limit,
  `400` empty file.

## `GET /api/scans`

Paginated, filterable scan history.

- **Query params**: `crop`, `severity`, `date_from`, `date_to` (all
  optional), `page` (default 1), `page_size` (default 20, max 100).
- **Response** `200`: `PaginatedScans` — `{ items: ScanSummary[], total, page, page_size }`.

## `GET /api/scans/{scan_uuid}`

Full detail for one scan (same shape as the `POST /api/scans` response).
`404` if not found.

## `GET /api/reports/{report_id}/download`

Streams the generated PDF (`application/pdf`). `404` if not found.

## `GET /api/dashboard/stats`

- **Query params**: `date_from`, `date_to` (optional).
- **Response** `200`: `DashboardStatsResponse`
  ```json
  {
    "total_scans": 42,
    "severity_breakdown": [{ "label": "Healthy", "count": 10 }, …],
    "crop_breakdown": [{ "label": "Tomato", "count": 20 }, …],
    "trend_over_time": [{ "date": "2026-08-01", "count": 5 }, …],
    "most_common_diseases": [{ "label": "Late blight", "count": 8 }, …]
  }
  ```

## `GET /api/health`

Liveness/readiness probe: `{ "status": "ok", "model_loaded": true, "model_status": "…" }`.
