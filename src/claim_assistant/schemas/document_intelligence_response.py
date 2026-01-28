from azure.ai.formrecognizer import AnalyzeResult
from pydantic import BaseModel, Field

from claim_assistant.schemas.bounding_region import BoundingRegion


class KeyValuePair(BaseModel):
    key: str | None = Field(...)
    value: str | None = Field(...)
    confidence: float | None = Field(..., ge=0.0, le=1.0)
    bounding_regions: list[BoundingRegion] = Field(default_factory=list)


class DocumentIntelligenceResponse(BaseModel):
    """
    Structured representation of key/value pairs similar to DI output
    derived from AnalyzeResult.

    It is a list of KeyValuePair:
      - key.content: field label (e.g., form field text)
      - value.content: extracted/filled value rendered as string
      - bounding_region: taken from VALUE evidences (best evidence)
    """

    kv_pairs: list[KeyValuePair] = Field(default_factory=list)

    @classmethod
    def from_analyze_result(
        cls,
        analysis: AnalyzeResult,
    ) -> "DocumentIntelligenceResponse":
        """
        Build a structured DI-like response from AnalyzeResult.

        Expects:
          analysis.form -> list[FormField]-like objects with:
            - field.key.content
            - field.value.content
            - field.value.evidences (list)
        """
        kv_pairs = getattr(analysis, "key_value_pairs", None) or []
        pairs: list[KeyValuePair] = []

        for kv in kv_pairs:
            key_el = getattr(kv, "key", None)
            val_el = getattr(kv, "value", None)

            key_text = getattr(key_el, "content", None) if key_el else None
            val_text = getattr(val_el, "content", None) if val_el else None
            conf = getattr(kv, "confidence", None)
            if conf is None and val_el is not None:
                conf = getattr(val_el, "confidence", None)

            regions = []
            if val_el is not None:
                for br in getattr(val_el, "bounding_regions", None) or []:
                    try:
                        regions.append(BoundingRegion.from_di(br))
                    except Exception:
                        # prefer resilience over crashing DI extraction
                        # if you want strictness, remove this try/except
                        continue

            pairs.append(
                KeyValuePair(
                    key=key_text,
                    value=val_text,
                    confidence=float(conf) if conf is not None else None,
                    bounding_regions=regions,
                ),
            )

        return cls(kv_pairs=pairs)
