import json
from pathlib import Path
from typing import Counter

import streamlit as st
from streamlit_sortables import sort_items

from claim_assistant import PROJECT_DIR
from claim_assistant.models.form import Form
from claim_assistant.models.form_field import FormField
from claim_assistant.views.base_view import BaseView, View


class FormModelEditorView(BaseView):
    """Interactive editor for viewing and modifying form definitions."""

    from collections import Counter

    ALLOWED_ALIASES = {"policy_id", "first_name", "last_name", "date_of_incident"}

    def validate_form_fields(self, fields: list[dict]) -> list[str]:
        errors: list[str] = []

        # normalize aliases
        aliases_raw = [(f.get("alias") or "") for f in fields]
        aliases_norm = [a.strip().lower() for a in aliases_raw]  # keep empty as ""

        # counts over non-empty aliases
        non_empty_aliases = [a for a in aliases_norm if a]
        counts = Counter(non_empty_aliases)

        # 1) unknown aliases (anything not in the allowed set)
        unknown = sorted(
            {a for a in non_empty_aliases if a not in self.ALLOWED_ALIASES},
        )
        if unknown:
            errors.append(
                f"Unknown alias(es) present: {unknown}. Allowed: {sorted(self.ALLOWED_ALIASES)}.",
            )

        # 2) required aliases: each must appear exactly once
        missing = [a for a in self.ALLOWED_ALIASES if counts.get(a, 0) == 0]
        multi = [a for a in self.ALLOWED_ALIASES if counts.get(a, 0) > 1]
        if missing:
            errors.append(f"Missing required alias(es): {missing}.")
        if multi:
            errors.append(f"Alias(es) assigned more than once: {multi}.")

        # 3) any duplicates across all aliases (even non-required) — should be none
        dupes_all = sorted([a for a, c in counts.items() if c > 1])
        if dupes_all:
            errors.append(
                f"Duplicate alias(es) detected: {dupes_all}. Each alias must be unique.",
            )

        # 4) (optional) ensure order values are a clean 1..N sequence
        orders = [f.get("order") for f in fields]
        if any(o is None for o in orders):
            errors.append("Some fields are missing 'order'.")
        else:
            n = len(fields)
            if sorted(orders) != list(range(1, n + 1)):
                errors.append(
                    "Field 'order' values must be a 1..N sequence with no gaps/duplicates.",
                )

        # 5) (optional) enforce meta rules quickly (enum must have labels, date/time may have format)
        for f in fields:
            dt = f.get("data_type")
            meta = f.get("meta") or {}
            if dt == "enum" and not meta.get("labels"):
                errors.append(
                    f"Field '{f.get('text', '(unnamed)')}' is enum but has no labels in meta.",
                )
            if (
                dt in {"date", "time"}
                and ("format" in meta)
                and not isinstance(meta["format"], str)
            ):
                errors.append(
                    f"Field '{f.get('text', '(unnamed)')}' has non-string meta.format.",
                )

        return errors

    def render(self):
        st.title("🧠 Form Model Editor")

        model_name = st.session_state.get("selected_model")
        if not model_name:
            st.error("❌ No model selected.")
            if st.button("↩️ Back to Models"):
                self.app.set_view(View.FORM_MODEL_SELECTION)
            return

        # --- Resolve path and load form ---
        form_path = (
            Path(PROJECT_DIR) / "data" / "forms" / model_name / "form_model.json"
        )
        if not form_path.exists():
            st.error(f"Form file not found: {form_path}")
            return

        # --- Load JSON once into session ---
        if "form_fields" not in st.session_state:
            form = Form.from_json(form_path)
            st.session_state.form_fields = [f.model_dump() for f in form.fields]

        st.markdown(f"### Editing: `{model_name}`")
        st.caption(f"File: {form_path}")

        fields = st.session_state.form_fields

        # --- Editable cards (live sync) ---
        st.markdown("#### Fields")
        for i, field_data in enumerate(fields):
            with st.container(border=True):
                field = FormField(**field_data)

                st.subheader(f"🧩 Field {i + 1}: {field.text or '(unnamed)'}")

                col1, col2 = st.columns([2, 1])
                with col1:
                    field.text = st.text_input(
                        "Field Text",
                        value=field.text,
                        key=f"text_{i}",
                    )
                    field.description = st.text_input(
                        "Description",
                        value=field.description or "",
                        key=f"desc_{i}",
                    )
                    field.alias = st.selectbox(
                        "Alias",
                        [
                            None,
                            "policy_id",
                            "first_name",
                            "last_name",
                            "date_of_incident",
                        ],
                        index=(
                            [
                                None,
                                "policy_id",
                                "first_name",
                                "last_name",
                                "date_of_incident",
                            ].index(field.alias)
                            if field.alias
                            in [
                                "policy_id",
                                "first_name",
                                "last_name",
                                "date_of_incident",
                            ]
                            else 0
                        ),
                        key=f"alias_{i}",
                    )

                with col2:
                    field.data_type = st.selectbox(
                        "Data Type",
                        ["string", "number", "date", "time", "boolean", "text", "enum"],
                        index=[
                            "string",
                            "number",
                            "date",
                            "time",
                            "boolean",
                            "text",
                            "enum",
                        ].index(field.data_type),
                        key=f"type_{i}",
                    )

                    # Meta editor
                    meta = field.meta or {}
                    if field.data_type in {"date", "time"}:
                        fmt_default = (
                            "YYYY-MM-DD" if field.data_type == "date" else "HH:mm:ss"
                        )
                        meta["format"] = st.text_input(
                            "Format",
                            value=meta.get("format", fmt_default),
                            key=f"meta_fmt_{i}",
                        )
                    elif field.data_type == "enum":
                        labels_str = ", ".join(meta.get("labels", []))
                        labels_str = st.text_input(
                            "Enum Labels (comma-separated)",
                            value=labels_str,
                            key=f"meta_labels_{i}",
                        )
                        meta["labels"] = [
                            lbl.strip() for lbl in labels_str.split(",") if lbl.strip()
                        ]
                    else:
                        meta = {}

                    field.meta = meta

                # Write back changes live
                field.order = i + 1
                st.session_state.form_fields[i] = field.model_dump()

        # --- Reorder Fields (Draggable UI) ---
        field_labels = [
            f"{i + 1}. {f.get('text', '(no text)')} ({f.get('alias', 'no_alias')})"
            for i, f in enumerate(st.session_state.form_fields)
        ]
        label_to_field = {
            lbl: f for lbl, f in zip(field_labels, st.session_state.form_fields)
        }

        new_order = sort_items(
            items=field_labels,
            multi_containers=False,
            direction="vertical",
            key="sortable_fields",
        )

        # Apply new order if valid
        if new_order and set(new_order) == set(field_labels):
            reordered = [
                label_to_field[lbl] for lbl in new_order if lbl in label_to_field
            ]
            for idx, f in enumerate(reordered, start=1):
                f["order"] = idx
            st.session_state.form_fields = reordered

        # --- Save & Navigation ---
        st.divider()
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("💾 Save Form Model", use_container_width=True):
                fields = st.session_state.form_fields
                errs = self.validate_form_fields(fields)
                if errs:
                    for e in errs:
                        st.error(e)
                    st.info("❌ Not saved. Please fix the issues above.")
                    st.stop()

                with open(form_path, "w", encoding="utf-8") as f:
                    json.dump(fields, f, indent=2, ensure_ascii=False)
                st.success("✅ Form model saved successfully.")

        with col2:
            if st.button("↩️ Back to Models", use_container_width=True):
                self.app.set_view(View.FORM_MODEL_SELECTION)

        with col3:
            if st.button("🏠 Back to Home", use_container_width=True):
                self.app.set_view(View.HOME)
