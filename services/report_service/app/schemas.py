from pydantic import BaseModel
from uuid import UUID


class ReportRequest(BaseModel):
    property_id: UUID


class ReportResponse(BaseModel):
    task_id: str


class ReportStatus(BaseModel):
    task_id: str
    state: str
    download_path: str | None = None
