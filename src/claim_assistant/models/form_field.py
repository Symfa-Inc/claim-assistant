from typing import Any, Literal

from pydantic import BaseModel, Field, create_model, field_validator
from pydantic_core.core_schema import ValidationInfo


class BoundingRegion(BaseModel):
    page: int = Field(..., ge=1)
    polygon: list[float] = Field(
        ...,
        description="Flat list [x1,y1,x2,y2,...] in DI coordinates.",
    )


class FieldEvidence(BaseModel):
    source: Literal["di_kv", "di_ocr", "manual", "llm"] = "di_kv"
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    bounding_regions: list[BoundingRegion] = Field(default_factory=list)


class FormFieldAnswer(BaseModel):
    value: Any = Field(None)
    evidence: list[FieldEvidence] = Field(default_factory=list)


class FormField(BaseModel):
    """Represents a single field in a claim form.

    Each field defines how a specific piece of information should be extracted
    and represented in structured output. It can serve both as an extraction
    template for the LLM and as a data definition for validation or mapping.
    """

    order: int = Field(
        None,
        description="Numeric order of the field in the form. ",
    )

    text: str = Field(
        ...,
        description="Human-readable field text or prompt as it appears in the form.",
    )
    description: str | None = Field(
        None,
        description=(
            "Auxiliary explanation or hint expanding the question. "
            "May include examples, definitions, or context to assist user."
        ),
    )
    alias: str | None = Field(
        description=(
            "Alias used for mapping fields into attributes required for business logic.\n"
            "Allowed aliases:\n"
            "• 'policy_id'\n"
            "• 'first_name'\n"
            "• 'last_name'\n"
            "• 'date_of_incident'"
        ),
    )
    data_type: Literal[
        "string",
        "number",
        "date",
        "time",
        "boolean",
        "text",
        "enum",
    ] = Field(
        ...,
        description=(
            "Defines how the LLM should represent the field in structured output "
            "and what validation applies."
            "Allowed options are specified in meta"
        ),
    )
    meta: dict[str, Any] | None = Field(
        default_factory=dict,
        description=(
            "Data-type–specific metadata controlling format and validation. "
            "Examples:\n"
            "• For enum: {'labels': ['Collision', 'Fire', 'Flood']}\n"
            "• For date: {'format': 'YYYY-MM-DD'}\n"
            "• For time: {'format': 'HH:mm:ss' or 'h:mm A'}"
        ),
    )
    answer: FormFieldAnswer = Field(
        default_factory=FormFieldAnswer,
        description="Value extracted or entered by user.",
    )

    @field_validator("order")
    @classmethod
    def validate_order(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Order must be a positive integer.")
        return v

    @field_validator("data_type")
    @classmethod
    def validate_data_type(cls, v: str) -> str:
        allowed = {"string", "number", "date", "time", "boolean", "text", "enum"}
        if v not in allowed:
            raise ValueError(
                f"Invalid data_type '{v}'. Must be one of {sorted(allowed)}.",
            )
        return v

    @field_validator("meta")
    @classmethod
    def validate_meta(
        cls,
        meta: dict[str, Any],
        info: ValidationInfo,
    ) -> dict[str, Any]:
        """Ensure meta contains only allowed keys and required ones if applicable."""
        if not meta:
            return meta

        allowed_keys = {"format", "labels"}
        invalid = set(meta.keys()) - allowed_keys
        if invalid:
            raise ValueError(
                f"Invalid meta key(s): {invalid}. Allowed keys: {allowed_keys}.",
            )

        dtype = info.data.get("data_type")  # <-- Correct Pydantic v2 access
        if dtype == "enum" and "labels" not in meta:
            raise ValueError(
                "Enum fields must define meta['labels'] with allowed options.",
            )
        if (
            dtype in {"date", "time"}
            and "format" in meta
            and not isinstance(meta["format"], str)
        ):
            raise ValueError("meta['format'] must be a string for date/time fields.")
        return meta

    def build_response_schema(self) -> type[BaseModel]:
        """
        Build a per-field structured-output schema that can carry:
          - the extracted value (typed by data_type)
          - optional evidence[] (confidence + bounding regions)
        """
        dtype = self.data_type
        meta = self.meta or {}

        type_map = {
            "string": str,
            "text": str,
            "number": float,
            "boolean": bool,
            "date": str,  # keep as str; validate/parse later if needed
            "time": str,  # keep as str; validate/parse later if needed
            "enum": str,
        }
        value_type = type_map.get(dtype, Any)

        desc = f"Field: {self.text}"
        if dtype == "enum" and meta.get("labels"):
            desc += f" (One of: {', '.join(meta['labels'])})"
        elif dtype in {"date", "time"} and meta.get("format"):
            desc += f" (Expected format: {meta['format']})"

        # Schema: {"value": ..., "evidence": [...]}
        DynamicAnswerModel = create_model(
            f"{(self.alias or 'FormField').title().replace(' ', '')}Response",
            value=(value_type, Field(default=None, description=desc)),
            evidence=(list[FieldEvidence], Field(default_factory=list)),
            __base__=BaseModel,
        )
        return DynamicAnswerModel


if __name__ == "__main__":
    import json

    field = FormField(
        order=1,
        text="Type of incident",
        data_type="enum",
        alias="incident_type",
        meta={"labels": ["Collision", "Fire", "Flood"]},
    )

    print(field.model_dump_json(indent=2))

    test_fields = [
        FormField(
            order=1,
            text="Date of incident",
            data_type="date",
            alias="date_of_incident",
            meta={"format": "YYYY-MM-DD"},
        ),
        FormField(
            order=2,
            text="Time of incident",
            data_type="time",
            alias=None,
            meta={"format": "h:mm A"},
        ),
        FormField(
            order=3,
            text="Type of incident",
            data_type="enum",
            alias="incident_type",
            meta={"labels": ["Collision", "Fire", "Flood"]},
        ),
        FormField(
            order=4,
            text="Description of incident",
            data_type="text",
            alias=None,
        ),
        FormField(
            order=5,
            text="Claim amount",
            data_type="number",
            alias=None,
        ),
    ]

    print("🔍 Testing FormField.build_response_schema()\n")
    for field in test_fields:
        print(f"Field: {field.text} (type={field.data_type})")
        schema = field.build_response_schema()
        print(json.dumps(schema, indent=2))
        print("-" * 60)
