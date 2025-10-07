import json
import logging
import os
import tempfile
import time

import streamlit as st

from claim_assistant.main import main as process_claim

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default policies data
DEFAULT_POLICIES = [
    {
        "policy_number": "SIC123456789",
        "policy_holder_name": "John Smith",
        "start_date": "2023-05-15",
        "end_date": "2024-05-15",
        "policy_coverage": "Workplace injury compensation including medical expenses, rehabilitation services, and wage replacement.",
    },
    {
        "policy_number": "POL123456789",
        "policy_holder_name": "John Doe",
        "start_date": "2022-03-20",
        "end_date": "2024-03-20",
        "policy_coverage": "Occupational accident insurance covering hospital bills, temporary disability payments, and emergency treatment costs.",
    },
]


def display_pdf(pdf_bytes: bytes, download_name: str):
    """Display PDF with consistent styling."""
    # Download button
    st.download_button(
        label=f"📥 Download {download_name}",
        data=pdf_bytes,
        file_name=f"{download_name.lower().replace(' ', '_')}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

    # Display PDF using iframe
    import base64

    base64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
    pdf_display = f"""
    <div style="width: 100%; height: 600px; border: 2px solid #e1e5e9; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-top: 10px;">
        <iframe
            src="data:application/pdf;base64,{base64_pdf}"
            width="100%"
            height="100%"
            type="application/pdf"
            style="border: none;">
        </iframe>
    </div>
    """
    st.markdown(pdf_display, unsafe_allow_html=True)


def create_placeholder():
    """Create placeholder with consistent styling."""
    placeholder = """
    <div style="width: 100%; height: 676px; border: 2px dashed #e1e5e9; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #8e9297; font-size: 18px; background-color: #f8f9fa; margin-top: 58px;">
        PDF will appear here
    </div>
    """
    st.markdown(placeholder, unsafe_allow_html=True)


def main():
    st.set_page_config(
        page_title="Claim Assistant - PDF Processor",
        page_icon="📄",
        layout="wide",
    )

    st.title("🏥 Claim Assistant - PDF Form Processor")
    st.markdown(
        "Upload a PDF form, process it with AI, and get a comprehensive summary report.",
    )

    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            help="Required for PDF processing",
            value=os.getenv("OPENAI_API_KEY", ""),
        )

        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key

        st.markdown("---")

        st.subheader("📋 Insurance Policies")
        use_default_policies = st.checkbox("Use default policies", value=True)

        if use_default_policies:
            policies = DEFAULT_POLICIES
            st.success(f"Using {len(policies)} default policies")
        else:
            policies_json = st.text_area(
                "Custom Policies (JSON)",
                value=json.dumps(DEFAULT_POLICIES, indent=2),
                height=200,
                help="Enter policies as JSON array",
            )
            try:
                policies = json.loads(policies_json)
                st.success(f"Loaded {len(policies)} custom policies")
            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON: {e}")
                policies = DEFAULT_POLICIES

    # File uploader
    uploaded_file = st.file_uploader(
        "📤 Choose a PDF file to process",
        type="pdf",
        help="Upload the claim form PDF to process",
    )

    # Control buttons in a single row
    if uploaded_file is not None:
        # Store file in session state
        if (
            "uploaded_pdf_bytes" not in st.session_state
            or st.session_state.get("uploaded_filename") != uploaded_file.name
        ):
            st.session_state.uploaded_pdf_bytes = uploaded_file.read()
            st.session_state.uploaded_filename = uploaded_file.name

        col_process, col_reset, col_time = st.columns([2, 2, 2])

        with col_process:
            if st.button(
                "🚀 Start Processing",
                type="primary",
                use_container_width=True,
            ):
                if not api_key:
                    st.error("⚠️ Please provide an OpenAI API key in the sidebar")
                    return

                start_time = time.time()

                with st.spinner("🔄 Processing PDF..."):
                    try:
                        # Save to temporary files
                        with tempfile.NamedTemporaryFile(
                            delete=False,
                            suffix=".pdf",
                        ) as tmp_input:
                            tmp_input.write(st.session_state.uploaded_pdf_bytes)
                            tmp_input_path = tmp_input.name

                        with tempfile.NamedTemporaryFile(
                            delete=False,
                            suffix=".pdf",
                        ) as tmp_output:
                            tmp_output_path = tmp_output.name

                        # Process the claim
                        process_claim(
                            input_pdf_path=tmp_input_path,
                            policies=policies,
                            ouptut_pdf_path=tmp_output_path,
                        )

                        # Calculate processing time
                        processing_time = time.time() - start_time

                        # Read generated summary
                        with open(tmp_output_path, "rb") as f:
                            summary_pdf_bytes = f.read()

                        # Store results
                        st.session_state.processing_complete = True
                        st.session_state.summary_pdf = summary_pdf_bytes
                        st.session_state.processing_time = processing_time

                        # Clean up
                        os.unlink(tmp_input_path)
                        os.unlink(tmp_output_path)

                        st.success(
                            f"✅ Processing completed in {processing_time:.1f} seconds!",
                        )
                        st.rerun()

                    except Exception as e:
                        st.error(f"❌ Processing failed: {str(e)}")
                        logger.error(f"Processing error: {e}", exc_info=True)

        with col_reset:
            if (
                hasattr(st.session_state, "processing_complete")
                and st.session_state.processing_complete
            ):
                if st.button("🔄 Reset", use_container_width=True):
                    for key in [
                        "processing_complete",
                        "summary_pdf",
                        "uploaded_pdf_bytes",
                        "uploaded_filename",
                        "processing_time",
                    ]:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()

        with col_time:
            if (
                hasattr(st.session_state, "processing_complete")
                and st.session_state.processing_complete
            ):
                st.metric(
                    "⚡ Processing Time",
                    f"{st.session_state.get('processing_time', 0):.1f}s",
                )

    st.markdown("---")

    # Perfect PDF alignment - simple and clean
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📄 Original Form")
        if uploaded_file is not None and hasattr(
            st.session_state,
            "uploaded_pdf_bytes",
        ):
            display_pdf(st.session_state.uploaded_pdf_bytes, "Original Form")
        else:
            create_placeholder()

    with col2:
        st.subheader("📊 Summary Report")
        if (
            hasattr(st.session_state, "processing_complete")
            and st.session_state.processing_complete
            and hasattr(st.session_state, "summary_pdf")
        ):
            display_pdf(st.session_state.summary_pdf, "Summary Report")
        else:
            create_placeholder()

    # Footer
    st.markdown("---")
    st.markdown("**Claim Assistant** - Automated claim processing powered by AI")


if __name__ == "__main__":
    main()
