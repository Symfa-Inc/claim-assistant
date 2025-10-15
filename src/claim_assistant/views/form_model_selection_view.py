import json
from pathlib import Path

import streamlit as st

from claim_assistant import PROJECT_DIR
from claim_assistant.views.base_view import BaseView, View


class FormModelSelectionView(BaseView):
    """Allows uploading or selecting an existing form model."""

    def render(self):
        st.title("🧩 Manage Form Models")
        st.markdown("Select, edit, or create new form definitions.")

        forms = self.app.available_forms
        if not forms:
            st.warning("⚠️ No existing form models found in `data/forms/`.")
            return

        # --- Radio-style form selector ---
        if "selected_model" not in st.session_state:
            st.session_state.selected_model = None

        st.write("### Existing Form Models")
        cols = st.columns(len(forms))
        selected_model = st.session_state.get("selected_model")

        for i, form_name in enumerate(forms):
            with cols[i]:
                is_selected = selected_model == form_name
                btn_label = f"✅ {form_name}" if is_selected else form_name
                if st.button(
                    btn_label,
                    key=f"select_model_{form_name}",
                    use_container_width=True,
                ):
                    st.session_state.selected_model = form_name

        selected_model = st.session_state.get("selected_model")

        # --- Actions for selected model ---
        st.divider()
        if selected_model:
            st.success(f"Selected model: **{selected_model}**")
            if st.button(
                "🧠 Edit Selected Model",
                type="primary",
                use_container_width=True,
            ):
                form_json_path = (
                    Path(PROJECT_DIR)
                    / "data"
                    / "forms"
                    / selected_model
                    / "form_model.json"
                )
                st.session_state["form_model_path"] = str(form_json_path)
                st.session_state["selected_model"] = selected_model
                self.app.set_view(View.FORM_MODEL_EDITOR)

        # --- Upload new form ---
        st.divider()
        st.subheader("📤 Upload New Form Definition")
        uploaded_file = st.file_uploader(
            "Upload new blank form (PDF)",
            type="pdf",
            key="upload_new_pdf",
        )

        if uploaded_file is not None:
            form_name = st.text_input(
                "📝 Enter a name for this form",
                key="new_form_name",
            )
            if form_name and st.button(
                "➕ Add New Form Model",
                use_container_width=True,
            ):
                try:
                    from claim_assistant.data.digitalize_forms import (
                        convert_pdf_to_json,
                    )

                    # --- Create directory ---
                    new_form_dir = Path(PROJECT_DIR) / "data" / "forms" / form_name
                    new_form_dir.mkdir(parents=True, exist_ok=True)

                    # --- Save uploaded PDF ---
                    pdf_path = new_form_dir / "form_raw.pdf"
                    with open(pdf_path, "wb") as f:
                        f.write(uploaded_file.read())

                    st.info("📤 Converting PDF to JSON form model...")

                    # --- Convert to JSON ---
                    model_data = convert_pdf_to_json(str(pdf_path))
                    model_path = new_form_dir / "form_model.json"
                    with open(model_path, "w", encoding="utf-8") as f:
                        json.dump(model_data, f, indent=2, ensure_ascii=False)

                    st.success(f"✅ New form model created at `{model_path}`")

                    # Save in session and redirect
                    st.session_state["selected_model"] = form_name
                    st.session_state["form_model_path"] = str(model_path)
                    self.app.set_view(View.FORM_MODEL_EDITOR)

                except Exception as e:
                    import traceback

                    st.error(f"❌ Failed to process new form: {e}")
                    st.text(traceback.format_exc())

        # --- Navigation ---
        st.divider()
        if st.button("🏠 Back to Home", use_container_width=True):
            self.app.set_view(View.HOME)
