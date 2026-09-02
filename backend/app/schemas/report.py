import datetime

from pydantic import BaseModel, ConfigDict


class ReportSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    report_id: str
    scan_id: int
    generated_at: datetime.datetime
