from pydantic import BaseModel
from uuid import UUID

class PropertyIdRequest(BaseModel):
    property_id: UUID


class ARVResult(BaseModel):
    property_id: UUID
    min: float
    max: float


class NarrativeResult(BaseModel):
    property_id: UUID
    narrative: str


class JobResponse(BaseModel):
    task_id: str


class JobStatus(BaseModel):
    task_id: str
    state: str
    result: dict | None = None
    result_error: str | None = None


class BatchRequest(BaseModel):
    property_ids: list[UUID]


class RetrainResponse(BaseModel):
    task_id: str
