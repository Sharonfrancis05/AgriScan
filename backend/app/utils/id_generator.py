import datetime
import uuid


def generate_report_id() -> str:
    """e.g. 'AGV-20260803-0F3A2C' — date-sortable, human-scannable."""
    date_part = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d")
    suffix = uuid.uuid4().hex[:6].upper()
    return f"AGV-{date_part}-{suffix}"
