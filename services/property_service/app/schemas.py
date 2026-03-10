from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class PropertyBase(BaseModel):
    address: str

class PropertyCreate(PropertyBase):
    pass


class PropertyUpdate(PropertyBase):
    """Fields allowed when modifying a property."""
    pass


class ImportRequest(BaseModel):
    """Payload for triggering a CSV import task."""
    filepath: str | None = None  # absolute or container path; defaults to sample file


class SearchHit(BaseModel):
    id: str
    address: str


class SearchResults(BaseModel):
    hits: list[SearchHit]
    query: str
    processingTimeMs: int
    limit: int
    offset: int
    estimatedTotalHits: int


class ARVResult(BaseModel):
    property_id: UUID
    min: float
    max: float

class PropertyOut(PropertyBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
