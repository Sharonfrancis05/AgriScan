# Development Setup

## Quick start (Docker Compose)

```bash
cp .env.example .env                 # edit MYSQL_PASSWORD etc. as you like
cp docker-compose.override.yml.example docker-compose.override.yml   # for hot reload
docker compose up --build
```

- Backend: http://localhost:8000 (Swagger UI at `/docs`)
- Frontend (dev server via the override file): http://localhost:5173
- Frontend (prod nginx build, no override file): http://localhost:80
- MySQL: localhost:3306 (credentials from `.env`)

Alembic migrations and the `diseases_reference` seed both run automatically
on backend startup — no manual DB setup step needed.

## Running the backend without Docker

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows; use `source .venv/bin/activate` on macOS/Linux
pip install --index-url https://download.pytorch.org/whl/cpu torch==2.5.1 torchvision==0.20.1
pip install -r requirements-dev.txt
# point DATABASE_URL at a MySQL instance you have running, e.g. via `docker compose up mysql`
alembic upgrade head
uvicorn app.main:app --reload
```

GPU note: the CPU wheel install above is what keeps the Docker image small
and is fine for inference. If you're training on a CUDA GPU, skip the
`--index-url` line and let `pip install -r requirements.txt` pull the
CUDA-enabled `torch`/`torchvision` build instead (or install the CUDA wheel
matching your driver from https://pytorch.org/get-started/locally/).

## Running the frontend without Docker

```bash
cd frontend
npm install
npm run dev
```

## Running tests

```bash
# backend
cd backend
pip install -r requirements-dev.txt
pytest tests/ -v

# frontend
cd frontend
npm run test
npx tsc -b        # typecheck
npm run build     # production build
```

The backend test suite runs against a throwaway SQLite database and a faked
classifier (see `tests/conftest.py`) — it never needs a real MySQL server or
network access to download ImageNet weights, so it runs the same way in CI
as on your machine.

## Preparing the training dataset

1. Download the Kaggle dataset and extract it (see the note below on large
   zips) into `backend/ml_training/data_raw/`. It doesn't need to match any
   particular folder layout — just make sure crop/disease class folders end
   up directly under `data_raw/` somewhere.
2. From `backend/`:
   ```bash
   pip install -r requirements.txt -r ml_training/requirements-training.txt
   python ml_training/prepare_dataset.py
   ```
   This filters to the 6 supported crops (Apple, Grape, Corn, Tomato,
   Strawberry, Peach), stratified-samples to ~3000-5000 images, writes
   `ml_training/data_prepared/`, and generates
   `backend/app/ml/labels_generated.json` (the authoritative label list the
   running app uses — restart the backend after regenerating it).

**Extracting a large dataset zip quickly on Windows**: per-file antivirus
scanning is usually the bottleneck, not the archive format itself. Prefer
7-Zip over Windows Explorer's built-in extractor, and — since
`prepare_dataset.py` discards everything outside the 6 supported crops
anyway — you can open the zip in 7-Zip without extracting it, browse into
it, and extract only the Apple/Grape/Corn/Tomato/Strawberry/Peach folders to
skip extracting Potato/Pepper/other classes entirely.

## Training the classifier

```bash
cd backend
python ml_training/train_classifier.py --epochs 15 --backbone efficientnet_b0
python ml_training/evaluate.py
```

Best checkpoint (by validation accuracy) is written to
`models_store/classifier_best.pt`. Restart the backend to pick it up — once
present, `model_status` switches from `pretrained_backbone_untrained_head`
to `fine_tuned` everywhere it's surfaced.

## Segmentation upgrade path

See `docs/segmentation_upgrade.md` — the short version is that the default
classical-CV segmentation needs no training data, and `train_segmentation.py`
is staged for later once you've acquired lesion masks by one of the three
documented methods.
