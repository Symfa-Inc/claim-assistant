import streamlit as st

from claim_assistant.views.base_view import BaseView, View


class HomeView(BaseView):
    """Landing view — lets the user choose between modes."""

    def render(self):
        st.title("🤖 Claim Assistant")
        st.markdown(
            """
            Welcome to **Claim Assistant** — your AI-powered workspace for claim processing and form model management.
            """,
        )

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📄 Process Claim Forms")
            st.markdown("Upload a filled form PDF and generate AI-assisted analysis.")
            if st.button("Start Processing", use_container_width=True):
                self.app.set_view(View.PROCESS_FORM)

        with col2:
            st.subheader("🧩 Manage Form Models")
            st.markdown("Create or edit JSON-based form templates for extraction.")
            if st.button("Manage Form Models", use_container_width=True):
                self.app.set_view(View.FORM_MODEL_SELECTION)
