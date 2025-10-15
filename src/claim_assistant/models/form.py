from pathlib import Path
from typing import Any, get_type_hints

from pydantic import BaseModel

from claim_assistant.models.form_field import FormField


class Form(BaseModel):
    """Generic Form containing both logic attributes and an ordered list of FormFields."""

    # --- Used for database logic ---
    policy_id: FormField
    first_name: FormField
    last_name: FormField
    date_of_incident: FormField

    # --- Used for report generation logic ---
    # (You can add more declared fields here later.)

    # --- All fields ---
    fields: list[FormField]

    def __init__(self, data: list[dict[str, Any]]) -> None:
        """
        Initialize form from list of dicts.

        Steps:
        1. Convert all elements into FormField instances.
        2. Sort fields by their 'order' attribute.
        3. Store them in self.fields.
        4. For fields whose alias matches a declared attribute name, assign them.
        5. Validate that all declared attributes are present.
        """
        super().__init__()

        if not isinstance(data, list):
            raise TypeError("Form expects a list of field definitions (dicts).")

        # 1. Convert each entry into a FormField
        fields: list[FormField] = []
        for entry in data:
            try:
                field = FormField(**entry)
            except Exception as e:
                raise ValueError(f"Invalid field definition: {entry}\n{e}")
            fields.append(field)

        # 2. Sort by 'order'
        fields.sort(key=lambda f: f.order)

        # 3. Save to form
        self.fields = fields

        # 4. Assign attributes by alias
        declared_attrs = {
            name
            for name, typ in get_type_hints(self.__class__).items()
            if typ is FormField
        }

        alias_map = {f.alias: f for f in fields}

        for attr_name in declared_attrs:
            field_obj = alias_map.get(attr_name)
            if field_obj is not None:
                setattr(self, attr_name, field_obj)

        # 5. Check that all declared attributes are present
        missing = [attr for attr in declared_attrs if not hasattr(self, attr)]
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
