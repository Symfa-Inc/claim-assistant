from datetime import datetime
from pathlib import Path

import streamlit as st

from claim_assistant import PROJECT_DIR
from claim_assistant.main import main as process_claim
from claim_assistant.views.base_view import BaseView, View

STATE_MAP = {
    "FL": "Florida",
    "IA": "Iowa",
    "KS": "Kansas",
    "MN": "Minnesota",
    "NH": "New Hampshire",
    "NY": "New York",
    "OH": "Ohio",
    "WI": "Wisconsin",
}

TYPE_MAP = {
    "hw": "Handwritten",
    "dg": "Digital",
}

MODERN_CSS = """
<style>
    /* Clean minimal design */
    .stApp {
        background: #ffffff;
    }

    .main .block-container {
        padding: 2rem 1rem;
        max-width: 1000px;
    }

    /* Typography */
    h1 {
        color: #0f172a;
        font-weight: 600;
        font-size: 2rem;
        margin-bottom: 0.5rem;
        letter-spacing: -0.025em;
    }

    h3 {
        color: #475569;
        font-weight: 500;
        font-size: 1rem;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }

    /* Minimal card design */
    .example-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.75rem;
        transition: all 0.15s ease;
        cursor: pointer;
    }

    .example-card:hover {
        border-color: #cbd5e1;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }

    .example-card.selected {
        border-color: #0f172a;
        background: #f8fafc;
    }

    .example-card h4 {
        margin: 0 0 0.5rem 0;
        font-size: 0.95rem;
        font-weight: 500;
        color: #0f172a;
    }

    /* State section headers */
    .state-section {
        margin-top: 2rem;
        margin-bottom: 1rem;
    }

    .state-section h4 {
        color: #0f172a;
        font-weight: 600;
        font-size: 1.1rem;
        margin-bottom: 0.75rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e2e8f0;
    }

    /* Minimal badges */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 500;
        margin-right: 0.5rem;
        background: #f1f5f9;
        color: #475569;
    }

    /* Upload area */
    .upload-area {
        border: 2px dashed #cbd5e1;
        border-radius: 8px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
        background: #fafafa;
    }

    /* Buttons styled as cards */
    .stButton > button {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
        padding: 1rem !important;
        text-align: center !important;
        font-weight: 400 !important;
        color: #0f172a !important;
        transition: all 0.15s ease !important;
        margin-bottom: 0.75rem !important;
    }

    .stButton > button:hover {
        background: #fafafa !important;
        border-color: #cbd5e1 !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
    }

    .stButton > button:focus {
        background: #f8fafc !important;
        border-color: #0f172a !important;
        box-shadow: none !important;
    }

    .stButton > button[kind="primary"] {
        background: #0f172a !important;
        color: #ffffff !important;
        border-color: #0f172a !important;
        font-weight: 500 !important;
        text-align: center !important;
    }

    .stButton > button[kind="primary"]:hover {
        background: #1e293b !important;
        border-color: #1e293b !important;
    }

    /* Clean alerts */
    .stAlert {
        border-radius: 6px;
        border: 1px solid #e2e8f0;
        background: #f8fafc;
    }

    /* File uploader minimal style */
    [data-testid="stFileUploader"] {
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 1rem;
        background: #fafafa;
    }

    /* Divider */
    hr {
        margin: 2rem 0;
        border-color: #f1f5f9;
    }
</style>
"""


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
        # Inject custom CSS
        st.markdown(MODERN_CSS, unsafe_allow_html=True)

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

        st.title("Process Claim Form")
        st.markdown(
            "Choose an example form or upload your own PDF to begin processing.",
        )

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

        # -------------------------------------------------
        # 3. Show examples section grouped by state
        # -------------------------------------------------
        st.markdown("### Example Forms")

        # Group examples by state
        examples_by_state = {}
        for ex in examples:
            state = ex["state"]
            if state not in examples_by_state:
                examples_by_state[state] = []
            examples_by_state[state].append(ex)

        # Display examples grouped by state
        for state, state_examples in sorted(examples_by_state.items()):
            state_name = STATE_MAP.get(state, state)

            st.markdown(
                f"""
            <div class="state-section">
                <h4>{state_name}</h4>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Display examples in 2 columns
            cols = st.columns(2)
            for idx, ex in enumerate(state_examples):
                key = ex["key"]
                # is_selected = selected == key

                type_name = TYPE_MAP.get(ex["type"], ex["type"])

                # Use alternating columns
                with cols[idx % 2]:
                    if st.button(
                        f"**{ex['case']}**  \n{type_name}",
                        key=f"select_{key}",
                        disabled=disabled,
                        use_container_width=True,
                    ):
                        select(key)
                        st.rerun()

        st.markdown("---")

        # -------------------------------------------------
        # 4. Upload section
        # -------------------------------------------------
        is_upload_selected = selected == upload_key

        st.markdown("### Upload Custom PDF")

        uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

        if uploaded_file and not is_upload_selected:
            select(upload_key)
            st.rerun()

        st.markdown("---")

        # -------------------------------------------------
        # 5. When EXAMPLE selected - show processing button
        # -------------------------------------------------
        if selected and selected != upload_key:
            ex = next(e for e in examples if e["key"] == selected)
            st.info(
                f"Selected: {ex['case']} — {TYPE_MAP.get(ex['type'], ex['type'])} form from {STATE_MAP.get(ex['state'], ex['state'])}",
            )

            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button(
                    "Process Form",
                    type="primary",
                    disabled=disabled,
                    use_container_width=True,
                ):
                    # Store what needs to be processed
                    self._lock_ui()
                    st.session_state.processing_target = {
                        "form": ex["form"],
                        "path": ex["path"],
                    }
                    st.rerun()
            return

        # -------------------------------------------------
        # 6. When UPLOAD selected - show form type selector
        # -------------------------------------------------
        if selected == upload_key and uploaded_file:
            st.info(f"File ready: {uploaded_file.name}")

            # Map 2-letter codes → full names for display
            full_state_labels = [STATE_MAP.get(f, f) for f in forms]

            # Reverse lookup dictionary (label → code)
            state_reverse_map = {STATE_MAP.get(f, f): f for f in forms}

            # Selector shows full names
            selected_full_state = st.selectbox("Select form type", full_state_labels)

            # Convert back to actual 2-letter code for processing
            selected_form = state_reverse_map[selected_full_state]

            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button(
                    "Process Form",
                    type="primary",
                    disabled=disabled,
                    use_container_width=True,
                ):
                    # Store what needs to be processed
                    self._lock_ui()
                    st.session_state.processing_target = {
                        "form": selected_form,
                        "path": uploaded_file,
                    }
                    st.rerun()
