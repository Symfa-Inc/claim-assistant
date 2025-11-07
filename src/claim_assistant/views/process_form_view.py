from datetime import datetime
from pathlib import Path

import streamlit as st

from claim_assistant import PROJECT_DIR
from claim_assistant.main import main as process_claim
from claim_assistant.views.base_view import BaseView, View


class ProcessFormView(BaseView):
    def render(self):
        st.title("📄 Process Claim Form")
        st.markdown("Select a form type and upload or choose a filled PDF to process.")

        forms = self.app.available_forms
        if not forms:
            st.warning("⚠️ No processable forms found in `data/forms/`.")
            return

        # --- Select form type ---
        if "selected_form_type" not in st.session_state:
            st.session_state.selected_form_type = None

        st.write("### Available Forms")
        cols = st.columns(len(forms))
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

        selected_form = st.session_state.get("selected_form_type")
        if not selected_form:
            st.info("Please select a form type to continue.")
            return

        st.divider()
        st.subheader(f"📄 Choose or Upload {selected_form} form")

        form_dir = Path(PROJECT_DIR) / "data" / "forms" / selected_form
        existing_pdfs = [f for f in form_dir.glob("*.pdf") if "form_raw" not in f.name]
        existing_names = [f.name for f in existing_pdfs]

        # --- File selector or upload ---
        pdf_choice = st.radio(
            "Select existing PDF or upload a new one:",
            ["Upload new"] + existing_names,
            horizontal=True,
        )

        uploaded_file = None
        input_pdf_path = None

        if pdf_choice == "Upload new":
            uploaded_file = st.file_uploader(
                "Upload PDF file",
                type="pdf",
                key="upload_pdf",
            )
        else:
            input_pdf_path = form_dir / pdf_choice

        if (uploaded_file or input_pdf_path) and st.button(
            "✨ Process Form",
            type="primary",
        ):
            with st.spinner("Processing form..."):
                try:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    run_dir = Path(PROJECT_DIR) / "data" / "runs" / timestamp
                    run_dir.mkdir(parents=True, exist_ok=True)

                    if uploaded_file:
                        input_pdf_path = run_dir / f"{selected_form}_input.pdf"
                        with open(input_pdf_path, "wb") as f:
                            f.write(uploaded_file.read())
                    else:
                        # copy existing PDF into run_dir for traceability
                        target_path = Path(run_dir) / f"{selected_form}_input.pdf"
                        target_path.write_bytes(Path(input_pdf_path).read_bytes())
                        input_pdf_path = target_path

                    form_json_path = form_dir / "form_model.json"
                    policy_db_path = (
                        Path(PROJECT_DIR) / "data" / "policies" / "policies.json"
                    )

                    process_claim(
                        run_dir=run_dir,
                        input_pdf_path=input_pdf_path,
                        form_json_path=form_json_path,
                        policy_db_path=policy_db_path,
                    )

                    st.session_state.run_dir = str(run_dir)
                    st.session_state.selected_form_type = selected_form
                    self.app.set_view(View.RESULTS)

                except Exception as e:
                    st.error(f"❌ Processing failed: {e}")
                    import traceback

                    st.text(traceback.format_exc())

        # Commented out Back to Home
        # if st.button("🏠 Back to Home", use_container_width=True):
        #     self.app.set_view(View.HOME)
