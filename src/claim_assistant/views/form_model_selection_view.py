import streamlit as st

from claim_assistant.views.base_view import BaseView, View


class FormModelSelectionView(BaseView):
    """Allows uploading or selecting an existing form model."""

    def render(self):
        st.title("🧩 Manage Form Models")
        st.markdown(
            "Upload a new form definition or select an existing one for editing.",
        )

        uploaded_file = st.file_uploader("Upload JSON Form Model", type="json")
        existing_models = ["DWC", "Generic"]
        selected_model = st.selectbox("Select existing form model", existing_models)

        if uploaded_file or selected_model:
            if st.button("🧠 Open in Editor", use_container_width=True):
                # Save selected or uploaded model in session for editor view
                st.session_state["selected_model"] = (
                    uploaded_file.name if uploaded_file else selected_model
                )
                self.app.set_view(View.FORM_MODEL_EDITOR)

        if st.button("🏠 Back to Home", use_container_width=True):
            self.app.set_view(View.HOME)
