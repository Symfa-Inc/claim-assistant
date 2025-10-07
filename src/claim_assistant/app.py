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
    """Display PDF with modern, minimalist styling."""
    # Modern download button
    st.download_button(
        label=f"↓ {download_name}",
        data=pdf_bytes,
        file_name=f"{download_name.lower().replace(' ', '_')}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

    # Modern PDF viewer with subtle shadows and clean borders
    import base64

    base64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
    pdf_display = f"""
    <div style="
        width: 100%;
        height: 650px;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        margin-top: 12px;
        background: white;
    ">
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
    """Create modern, minimalist placeholder."""
    placeholder = """
    <div style="
        width: 100%;
        height: 720px;
        border: 2px dashed #d1d5db;
        border-radius: 12px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        color: #6b7280;
        font-size: 16px;
        font-weight: 500;
        background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);
        margin-top: 58px;
        transition: all 0.3s ease;
    ">
        <div style="font-size: 48px; margin-bottom: 16px; opacity: 0.5;">📄</div>
        <div>PDF will appear here</div>
    </div>
    """
    st.markdown(placeholder, unsafe_allow_html=True)


def main():
    st.set_page_config(
        page_title="Claim Assistant",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # Modern CSS styling
    st.markdown(
        """
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f2937;
        margin-bottom: 0.5rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #6b7280;
        font-weight: 400;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.25rem;
        font-weight: 600;
        color: #374151;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e5e7eb;
    }
    .stButton > button {
        border-radius: 8px;
        border: none;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        border: 1px solid #e5e7eb;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Modern header
    st.markdown('<h1 class="main-header">Claim Assistant</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">AI-powered insurance claim processing made simple</p>',
        unsafe_allow_html=True,
    )

    # Modern sidebar configuration
    with st.sidebar:
        st.markdown("### ⚙️ Configuration")

        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            placeholder="sk-...",
            help="🔐 Required for AI processing",
            value=os.getenv("OPENAI_API_KEY", ""),
        )

        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key

        st.markdown("---")

        st.markdown("### 📋 Policies")
        use_default_policies = st.checkbox("Use default policies", value=True)

        if use_default_policies:
            policies = DEFAULT_POLICIES
            st.success(f"✓ {len(policies)} policies loaded")
        else:
            policies_json = st.text_area(
                "Custom Policies (JSON)",
                value=json.dumps(DEFAULT_POLICIES, indent=2),
                height=180,
                help="Enter policies as JSON array",
            )
            try:
                policies = json.loads(policies_json)
                st.success(f"✓ {len(policies)} custom policies loaded")
            except json.JSONDecodeError as e:
                st.error(f"❌ Invalid JSON: {e}")
                policies = DEFAULT_POLICIES

    # Modern file uploader section
    st.markdown("### 📎 Upload Document")
    uploaded_file = st.file_uploader(
        "Choose a PDF file to process",
        type="pdf",
        help="Drag and drop or browse for your claim form PDF",
        label_visibility="collapsed",
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

        # Modern control panel
        col_process, col_reset, col_time = st.columns([3, 2, 2])

        with col_process:
            if st.button(
                "✨ Process Document",
                type="primary",
                use_container_width=True,
            ):
                if not api_key:
                    st.error("🔑 Please provide an OpenAI API key in the sidebar")
                    return

                start_time = time.time()

                with st.spinner("🤖 AI is analyzing your document..."):
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
                            f"🎉 Analysis complete! Processed in {processing_time:.1f}s",
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
                if st.button("↻ New Document", use_container_width=True):
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
                st.markdown(
                    f"""
                <div class="metric-card">
                    <div style="color: #6b7280; font-size: 0.875rem; margin-bottom: 4px;">Processing Time</div>
                    <div style="color: #059669; font-size: 1.5rem; font-weight: 700;">
                        {st.session_state.get("processing_time", 0):.1f}s
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

    # Modern divider
    st.markdown(
        """
    <div style="height: 1px; background: linear-gradient(90deg, transparent, #e5e7eb, transparent); margin: 2rem 0;"></div>
    """,
        unsafe_allow_html=True,
    )

    # Clean document viewer section
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown(
            '<div class="section-header">📄 Original Document</div>',
            unsafe_allow_html=True,
        )
        if uploaded_file is not None and hasattr(
            st.session_state,
            "uploaded_pdf_bytes",
        ):
            display_pdf(st.session_state.uploaded_pdf_bytes, "Original Document")
        else:
            create_placeholder()

    with col2:
        st.markdown(
            '<div class="section-header">📊 AI Analysis Report</div>',
            unsafe_allow_html=True,
        )
        if (
            hasattr(st.session_state, "processing_complete")
            and st.session_state.processing_complete
            and hasattr(st.session_state, "summary_pdf")
        ):
            display_pdf(st.session_state.summary_pdf, "Analysis Report")
        else:
            create_placeholder()

    # Modern footer
    st.markdown(
        """
    <div style="margin-top: 3rem; padding: 2rem 0; border-top: 1px solid #e5e7eb; text-align: center;">
        <div style="color: #6b7280; font-size: 0.875rem;">
            <strong>Claim Assistant</strong> • Powered by AI • Built for efficiency
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
