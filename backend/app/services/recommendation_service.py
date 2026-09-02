from sqlalchemy.orm import Session

from app.models.disease_reference import DiseaseReference
from app.schemas.scan import RecommendationBlock

_URGENCY_NOTE = (
    "Severity is {severity}: isolate or remove severely affected plant material promptly "
    "and consider a follow-up scan after treatment to confirm improvement."
)


def get_recommendations(db: Session, disease_code: str, severity: str) -> RecommendationBlock:
    reference = db.query(DiseaseReference).filter_by(disease_code=disease_code).first()

    if reference is None:
        return RecommendationBlock(
            treatment="No reference data available for this disease code yet.",
            prevention="No reference data available for this disease code yet.",
        )

    urgency_note = None
    if severity in ("Severe", "Critical"):
        urgency_note = _URGENCY_NOTE.format(severity=severity)

    return RecommendationBlock(
        treatment=reference.treatment_text or "",
        prevention=reference.prevention_text or "",
        urgency_note=urgency_note,
    )
