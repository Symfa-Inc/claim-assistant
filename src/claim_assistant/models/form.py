from pathlib import Path
from typing import Any, get_type_hints

from pydantic import BaseModel, Field

from claim_assistant.models.form_field import FormField


class Form(BaseModel):
    """
    Represents a structured insurance form composed of ordered FormFields.
    Dynamically maps required aliases (policy_id, first_name, etc.)
    and provides safe per-instance field management.
    """

    # --- Used for database logic ---
    policy_id: FormField | None = Field(default=None)
    first_name: FormField | None = Field(default=None)
    last_name: FormField | None = Field(default=None)
    date_of_incident: FormField | None = Field(default=None)

    # --- Used for report generation logic ---
    # (You can add more declared fields here later.)

    # --- All fields ---
    fields: list[FormField] = Field(
        ...,
        description="List of all fields defined in the form model (ordered).",
    )

    def __init__(self, data: list[dict[str, Any]]) -> None:
        """
        Initialize from a list of field definitions, preserving reference links.
        """
        if not isinstance(data, list):
            raise TypeError("Form expects a list of field definitions (dicts).")

        # 1. Convert to FormField instances and sort
        fields = [FormField(**entry) for entry in data]
        fields.sort(key=lambda f: f.order)

        # 2. Map aliases
        alias_map = {f.alias: f for f in fields if f.alias}

        # 3. Call BaseModel init first with all fields
        super().__init__(fields=fields)

        # 4. Dynamically assign attributes (shared references)
        declared_attrs = {
            name
            for name, typ in get_type_hints(self.__class__).items()
            if typ in {FormField, FormField | None}
        }

        for attr_name in declared_attrs:
            if attr_name in alias_map:
                object.__setattr__(self, attr_name, alias_map[attr_name])

        # 5. Check that all declared fields exist
        missing = [a for a in declared_attrs if getattr(self, a, None) is None]
        if missing:
            raise ValueError(
                f"Missing required fields for declared attributes: {missing}",
            )

    @classmethod
    def from_json(cls, path: str | Path) -> "Form":
        """
        Factory method that loads form definition from a JSON file
        and returns a Form instance.

        Args:
            path: Path to a JSON file containing a list of field definitions.

        Returns:
            Form: a fully initialized Form object.
        """
        import json

        path = Path(path)
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"Form JSON file not found: {path}")

        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in form file: {path}\n{e}")

        if not isinstance(data, list):
            raise TypeError(
                f"Form JSON must be a list of field definitions, got {type(data)}",
            )

        return cls(data)


if __name__ == "__main__":
    form_data = [
        {
            "order": 2,
            "text": "First name",
            "alias": "first_name",
            "data_type": "string",
        },
        {"order": 1, "text": "Policy ID", "alias": "policy_id", "data_type": "string"},
        {"order": 3, "text": "Last name", "alias": "last_name", "data_type": "string"},
        {
            "order": 4,
            "text": "Date of incident",
            "alias": "date_of_incident",
            "data_type": "date",
        },
    ]

    form = Form(form_data)

    print("Fields (ordered):", [f.alias for f in form.fields])
    print("Shared object check:", form.policy_id is form.fields[0])

    # Modify one place, both reflect
    form.policy_id.answer = "POL123"
    print(form.fields[0].answer)
    print(form.policy_id.answer)
