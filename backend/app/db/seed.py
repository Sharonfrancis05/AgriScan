"""Idempotent seed loader for diseases_reference.

Run with: python -m app.db.seed
Also invoked automatically from the Docker entrypoint after migrations, so
a fresh environment always has recommendation text available.
"""
import json
import logging
from pathlib import Path

from app.db.session import SessionLocal
from app.models.disease_reference import DiseaseReference

logger = logging.getLogger(__name__)

_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "diseases_reference_seed.json"


def seed_diseases_reference() -> None:
    entries = json.loads(_FIXTURE_PATH.read_text())

    with SessionLocal() as db:
        existing_codes = {row.disease_code for row in db.query(DiseaseReference.disease_code).all()}
        new_rows = [
            DiseaseReference(**entry) for entry in entries if entry["disease_code"] not in existing_codes
        ]
        if new_rows:
            db.add_all(new_rows)
            db.commit()
            logger.info("Seeded %d new diseases_reference rows", len(new_rows))
        else:
            logger.info("diseases_reference already seeded, nothing to do")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed_diseases_reference()
