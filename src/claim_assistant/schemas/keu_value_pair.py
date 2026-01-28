from pydantic import BaseModel, Field

from claim_assistant.schemas.bounding_region import BoundingRegion


class KeyValuePair(BaseModel):
    key: str | None = Field(...)
    value: str | None = Field(...)
    confidence: float | None = Field(..., ge=0.0, le=1.0)
    bounding_regions: list[BoundingRegion] = Field(default_factory=list)
