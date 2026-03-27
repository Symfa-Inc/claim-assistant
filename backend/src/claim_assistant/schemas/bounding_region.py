from typing import Annotated

from azure.ai.formrecognizer import BoundingRegion as DIBoundingRegion
from pydantic import BaseModel, Field


class BoundingRegion(BaseModel):
    """
    Bounding region of an extracted element on a specific page,
    as returned by Azure Document Intelligence.

    Coordinate system:
    - Origin (0, 0) is the TOP-LEFT corner of the page.
    - Coordinates are absolute and page-relative (NOT normalized).
    - Polygon vertices are listed clockwise starting from the top-left corner
      of the element’s bounding quadrilateral.

    Units:
    - For PDF inputs: coordinates are measured in INCHES.
    - For image inputs (PNG/JPEG/TIFF): coordinates are measured in PIXELS.

    Notes:
    - Values are floats because PDF coordinate space is continuous.
    - Consumers must NOT assume pixel units unless the source document is an image.
    - No DPI normalization is applied.
    """

    page: int = Field(..., ge=1)
    polygon: Annotated[list[float], Field(min_length=8, max_length=8)] = Field(
        ...,
        description="8-number quadrilateral: x1,y1,x2,y2,x3,y3,x4,y4 in DI coordinates.",
    )

    @classmethod
    def from_di(cls, other: DIBoundingRegion) -> "BoundingRegion":
        (x1, y1), (x2, y2), (x3, y3), (x4, y4) = other.polygon
        return BoundingRegion(
            page=other.page_number,
            polygon=[x1, y1, x2, y2, x3, y3, x4, y4],
        )
