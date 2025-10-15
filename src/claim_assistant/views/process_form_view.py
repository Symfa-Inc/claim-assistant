import os
from datetime import datetime
from pathlib import Path

import streamlit as st

from claim_assistant import PROJECT_DIR
from claim_assistant.main import main as process_claim
from claim_assistant.views.base_view import BaseView, View


class ProcessFormView(BaseView):
    def render(self):
        st.title("📄 Process Claim Form")
        st.markdown("Select a form type and upload a filled PDF to process.")

        forms = self.app.available_forms
        if not forms:
            st.warning("⚠️ No processable forms found in `data/forms/`.")
            return

        # --- Simple radio-like button row ---
        # Ensure session state key exists
        if "selected_form_type" not in st.session_state:
            st.session_state.selected_form_type = None

        st.write("### Available Forms")
        cols = st.columns(len(forms))
        selected_form = st.session_state.get("selected_form_type")

        for i, form_name in enumerate(forms):
            with cols[i]:
                is_selected = st.session_state.selected_form_type == form_name
                btn_label = f"✅ {form_name}" if is_selected else form_name
                if st.button(
                    btn_label,
                    key=f"select_{form_name}",
                    use_container_width=True,
                ):
                    st.session_state.selected_form_type = form_name

        # --- File upload ---
        st.divider()
        st.subheader(f"📄 Upload filled {selected_form} form")
        uploaded_file = st.file_uploader(
            "Choose PDF file",
            type="pdf",
            key="upload_pdf",
        )

        if uploaded_file and st.button("✨ Process Form", type="primary"):
            with st.spinner("Processing form..."):
                try:
                    # --- Create run directory ---
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    run_dir = os.path.join(PROJECT_DIR, "data", "runs", timestamp)
                    os.makedirs(run_dir, exist_ok=True)

                    # --- Save uploaded file ---
                    input_pdf_path = Path(run_dir) / f"{selected_form}_input.pdf"
                    with open(input_pdf_path, "wb") as f:
                        f.write(uploaded_file.read())

                    # --- Resolve form and policy paths ---
                    form_json_path = (
                        Path(PROJECT_DIR)
                        / "data"
                        / "forms"
                        / selected_form
                        / "form_model.json"
                    )
                    # TODO: switch back to new policies when ready
                    # policy_db_path = Path(PROJECT_DIR) / "data" / "policies" / "policies.json"
                    policy_db_path = (
                        Path(PROJECT_DIR) / "data" / "policies" / "policies_old.json"
                    )

                    process_claim(
                        run_dir=run_dir,
                        input_pdf_path=input_pdf_path,
                        form_json_path=form_json_path,
                        policy_db_path=policy_db_path,
                    )

                    st.session_state.run_dir = run_dir
                    st.session_state.selected_form_type = selected_form
                    self.app.set_view(View.RESULTS)

                except Exception as e:
                    st.error(f"❌ Processing failed: {e}")
                    import traceback

                    st.text(traceback.format_exc())
