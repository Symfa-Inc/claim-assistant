from datetime import datetime
from pathlib import Path

import streamlit as st

from claim_assistant import PROJECT_DIR
from claim_assistant.main import main as process_claim
from claim_assistant.views.base_view import BaseView, View

STATE_MAP = {
    "IA": "Iowa",
    "KS": "Kansas",
    "MN": "Minnesota",
    "FL": "Florida",
    "NH": "New Hampshire",
    "WI": "Wisconsin",
}

TYPE_MAP = {
    "hw": "Handwritten",
    "dg": "Digital",
}


class ProcessFormView(BaseView):
    def _lock_ui(self):
        st.session_state.processing_in_progress = True

    def _unlock_ui(self):
        st.session_state.processing_in_progress = False

    def _run_processing(self, selected_form, input_file):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = Path(PROJECT_DIR) / "data" / "runs" / timestamp
        run_dir.mkdir(parents=True, exist_ok=True)

        # unify to *_input.pdf
        target_pdf = run_dir / f"{selected_form}_input.pdf"

        if isinstance(input_file, Path):
            target_pdf.write_bytes(input_file.read_bytes())
        else:
            target_pdf.write_bytes(input_file.read())

        form_json_path = (
            Path(PROJECT_DIR) / "data" / "forms" / selected_form / "form_model.json"
        )
        policy_db_path = Path(PROJECT_DIR) / "data" / "policies" / "policies.json"

        process_claim(
            run_dir=run_dir,
            input_pdf_path=target_pdf,
            form_json_path=form_json_path,
            policy_db_path=policy_db_path,
        )

        st.session_state.run_dir = str(run_dir)
        self._unlock_ui()
        self.app.set_view(View.RESULTS)

    def render(self):
        if "processing_in_progress" not in st.session_state:
            st.session_state.processing_in_progress = False

        target = st.session_state.get("processing_target")
        if target:
            try:
                st.info("⏳ Processing form… this may take up to 5 minutes")
                self._run_processing(target["form"], target["path"])
            finally:
                self._unlock_ui()
                st.session_state.processing_target = None
                st.rerun()

        disabled = st.session_state.processing_in_progress

        st.title("📄 Process Claim Form")

        forms = self.app.available_forms
        if not forms:
            st.warning("⚠️ No processable forms found in `data/forms/`.")
            return

        # -------------------------------------------------
        # 1. Load example PDFs
        # -------------------------------------------------
        examples = []
        forms_root = Path(PROJECT_DIR) / "data" / "forms"

        for form_name in forms:
            form_dir = forms_root / form_name
            for pdf in form_dir.glob("form_*.pdf"):
                if "raw" in pdf.name:
                    continue

                parts = pdf.stem.split("_")  # ["form","hw","POL123456789"]
                if len(parts) != 3:
                    continue

                _, ftype, fcase = parts
                key = f"{form_name}:{ftype}:{fcase}"

                examples.append(
                    {
                        "key": key,
                        "case": fcase,
                        "state": form_name,
                        "type": ftype,
                        "path": pdf,
                        "form": form_name,
                    },
                )

        upload_key = "UPLOAD_CUSTOM"

        # -------------------------------------------------
        # 2. Persistent selection in session state
        # -------------------------------------------------
        if "selected_row" not in st.session_state:
            st.session_state.selected_row = None

        def select(key: str):
            st.session_state.selected_row = key

        selected = st.session_state.selected_row

        st.subheader("Choose an example case or upload your own")

        # -------------------------------------------------
        # 3. Draw table header
        # -------------------------------------------------
        header = st.columns([0.12, 0.30, 0.20, 0.20])
        header[0].markdown("**Select**")
        header[1].markdown("**Case**")
        header[2].markdown("**State**")
        header[3].markdown("**Type**")

        # -------------------------------------------------
        # 4. Draw example rows with custom radio buttons
        # -------------------------------------------------
        for i, ex in enumerate(examples):
            key = ex["key"]
            is_selected = selected == key

            cols = st.columns([0.12, 0.30, 0.20, 0.20])

            # --- SELECTOR BUTTON ---
            with cols[0]:
                icon = "🔘" if is_selected else "⚪️"
                label = f"{icon}  Example {i + 1}"
                if st.button(label, key=f"select_{key}", disabled=disabled):
                    select(key)

            # --- TABLE CELLS ---
            cols[1].write(ex["case"])
            cols[2].write(STATE_MAP.get(ex["state"], ex["state"]))
            cols[3].write(TYPE_MAP.get(ex["type"], ex["type"]))

        # -------------------------------------------------
        # 5. Upload row
        # -------------------------------------------------
        is_upload_selected = selected == upload_key
        cols = st.columns([0.12, 0.88])

        with cols[0]:
            icon = "🔘" if is_upload_selected else "⚪️"
            label = f"{icon}  Upload custom PDF"
            if st.button(label, key="select_upload", disabled=disabled):
                select(upload_key)

        st.divider()

        # -------------------------------------------------
        # 6. When EXAMPLE selected
        # -------------------------------------------------
        if selected and selected != upload_key:
            ex = next(e for e in examples if e["key"] == selected)
            st.success(f"Selected example: {ex['case']} ({ex['type']})")

            if st.button("✨ Process Example", type="primary", disabled=disabled):
                # Store what needs to be processed
                self._lock_ui()
                st.session_state.processing_target = {
                    "form": ex["form"],
                    "path": ex["path"],
                }
                st.rerun()
            return

        # -------------------------------------------------
        # 7. When UPLOAD selected
        # -------------------------------------------------
        if selected == upload_key:
            st.subheader("Upload your own PDF")

            st.selectbox("Form type", forms)
            uploaded_file = st.file_uploader("Choose PDF file", type="pdf")
            if (
                st.button("✨ Process Uploaded Form", type="primary", disabled=disabled)
                and uploaded_file
            ):
                # Store what needs to be processed
                self._lock_ui()
                st.session_state.processing_target = {
                    "form": ex["form"],
                    "path": ex["path"],
                }
                st.rerun()
