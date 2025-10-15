import json

import streamlit as st

from claim_assistant.views.base_view import BaseView, View


class FormModelEditorView(BaseView):
    """Interactive editor for viewing and modifying form definitions."""

    def render(self):
        st.title("🧠 Form Model Editor")
        model_name = st.session_state.get("selected_model", "Unnamed Model")

        st.markdown(f"Editing model: **{model_name}**")

        # Load form definition (placeholder)
        form_json = "{}"
        st.text_area(
            "Form Definition (JSON)",
            value=form_json,
            height=400,
            key="form_json_editor",
        )

        col_save, col_back = st.columns(2)
        with col_save:
            if st.button("💾 Save Changes", use_container_width=True):
                try:
                    json.loads(st.session_state["form_json_editor"])
                    st.success("✅ Form model saved successfully.")
                except json.JSONDecodeError as e:
                    st.error(f"❌ Invalid JSON: {e}")

        with col_back:
            if st.button("↩️ Back to Models", use_container_width=True):
                self.app.set_view(View.FORM_MODEL_SELECTION)
