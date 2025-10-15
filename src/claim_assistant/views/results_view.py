from pathlib import Path

import streamlit as st

from claim_assistant.views.base_view import BaseView, View


class ResultsView(BaseView):
    def render(self):
        st.title("📊 Processing Results")

        run_dir = st.session_state.get("run_dir")
        if not run_dir or not Path(run_dir).exists():
            st.error("❌ No recent run found.")
            if st.button("↩️ Back to Start"):
                self.app.set_view(View.PROCESS_FORM)
            return

        run_path = Path(run_dir)
        st.markdown(f"**Run Directory:** `{run_path}`")

        input_pdf = next(run_path.glob("*_input.pdf"), None)
        summary_pdf = run_path / "claim_summary.pdf"

        # --- Read PDFs safely ---
        input_pdf_bytes = None
        summary_pdf_bytes = None
        if input_pdf and input_pdf.exists():
            input_pdf_bytes = input_pdf.read_bytes()
        if summary_pdf.exists():
            summary_pdf_bytes = summary_pdf.read_bytes()

        # --- Display PDFs ---
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📄 Uploaded Form")
            if input_pdf_bytes:
                st.download_button(
                    "Download Form PDF",
                    input_pdf_bytes,
                    file_name=input_pdf.name,
                    key="download_input_pdf",
                )
                st.pdf(input_pdf_bytes, key=f"pdf_view_input_{run_dir}")
            else:
                st.warning("No input PDF found.")

        with col2:
            st.subheader("📈 Summary Report")
            if summary_pdf_bytes:
                st.download_button(
                    "Download Summary PDF",
                    summary_pdf_bytes,
                    file_name=summary_pdf.name,
                    key="download_summary_pdf",
                )
                st.pdf(summary_pdf_bytes, key=f"pdf_view_summary_{run_dir}")
            else:
                st.warning("No summary PDF found.")

        # --- Footer Buttons (separate container) ---
        st.divider()
        footer = st.container()
        with footer:
            col1, col2 = st.columns(2)
            with col1:
                if st.button(
                    "📄 Process Another Form",
                    use_container_width=True,
                    key="btn_process_another",
                ):
                    self.app.set_view(View.PROCESS_FORM)
            with col2:
                if st.button(
                    "🏠 Back to Main Menu",
                    use_container_width=True,
                    key="btn_back_home",
                ):
                    self.app.set_view(View.HOME)
