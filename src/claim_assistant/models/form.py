from pathlib import Path
from typing import Any, get_type_hints

from pydantic import BaseModel, Field, create_model

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

    # ----------------------------------------------------------------
    # Unified structured-response schema builder
    # ----------------------------------------------------------------
    def build_response_schema(self) -> type[BaseModel]:
        """
        Dynamically construct a single response schema model
        that includes all form fields in one structure.
        """

        fields_dict = {}
        for i, f in enumerate(self.fields, start=1):
            name = f"{i}_{f.alias or f.text.replace(' ', '_').lower()}"
            fields_dict[name] = f.build_response_schema()

        DynamicFormResponseModel = create_model(
            "FormResponseModel",
            **fields_dict,
            __base__=BaseModel,
        )
        return DynamicFormResponseModel

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

    @classmethod
    def from_filled_json(
        cls,
        form_path: str | Path,
        answers_path: str | Path,
    ) -> "Form":
        """
        Factory method to load a filled form from two JSON files:
        - form_path: JSON defining the form fields (structure)
        - answers_path: JSON with the filled answers

        Raises:
            FileNotFoundError: if either file does not exist.
            TypeError: if JSON structure is invalid.
            ValueError: if answers do not correspond to form model.

        Returns:
            Form: a Form instance with field.answer values populated.
        """
        import json

        form_path = Path(form_path)
        answers_path = Path(answers_path)

        # --- Load form model ---
        if not form_path.exists():
            raise FileNotFoundError(f"Form JSON not found: {form_path}")
        with form_path.open("r", encoding="utf-8") as f:
            form_data = json.load(f)
        if not isinstance(form_data, list):
            raise TypeError("Form JSON must be a list of field definitions.")

        # --- Load answers ---
        if not answers_path.exists():
            raise FileNotFoundError(f"Answers JSON not found: {answers_path}")
        with answers_path.open("r", encoding="utf-8") as f:
            answers_data = json.load(f)
        if not isinstance(answers_data, list):
            raise TypeError("Answers JSON must be a list of answer objects.")

        # --- Basic shape validation ---
        # Ensure answer objects contain at least 'order' and 'answer' keys
        if not all(
            isinstance(a, dict) and "order" in a and "answer" in a for a in answers_data
        ):
            raise ValueError(
                f"Invalid answers file: {answers_path}\n"
                "Each entry must include 'order', 'text', and 'answer' fields.",
            )

        # --- Initialize form from model ---
        form = cls(form_data)

        # --- Build lookup tables ---
        answers_by_order = {a["order"]: a["answer"] for a in answers_data}
        answers_by_text = {a["text"]: a["answer"] for a in answers_data}

        # --- Fill answers and track mismatches ---
        unmatched = []
        for field in form.fields:
            value = answers_by_order.get(field.order)
            if value is None:
                value = answers_by_text.get(field.text)
            if value is None:
                unmatched.append(f"{field.order}: {field.text}")
            field.answer = value

        if unmatched:
            raise ValueError(
                f"Answers file does not match form model.\n"
                f"Missing {len(unmatched)} fields:\n" + "\n".join(unmatched),
            )

        return form


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
