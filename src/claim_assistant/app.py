import os.path
from pathlib import Path

import streamlit as st

from claim_assistant import PROJECT_DIR
from claim_assistant.views import (
    FormModelEditorView,
    FormModelSelectionView,
    HomeView,
    ProcessFormView,
    ResultsView,
    View,
)


class ClaimAssistantApp:
    def __init__(self):
        st.set_page_config(page_title="Claim Assistant", page_icon="🤖", layout="wide")
        self.forms_dir = Path(os.path.join(PROJECT_DIR, "data", "forms"))
        self.available_forms = self._discover_forms()
        self.current_view: View = st.session_state.get("current_view", View.HOME)

        self.views = {
            View.HOME: HomeView(self),
            View.PROCESS_FORM: ProcessFormView(self),
            View.RESULTS: ResultsView(self),
            View.FORM_MODEL_SELECTION: FormModelSelectionView(self),
            View.FORM_MODEL_EDITOR: FormModelEditorView(self),
        }

    def _discover_forms(self) -> list[str]:
        """Scan `data/forms` and return names of processable forms."""
        form_types = []
        for subdir in self.forms_dir.iterdir():
            if subdir.is_dir() and (subdir / "form_model.json").exists():
                form_types.append(subdir.name)
        return sorted(form_types)

    def set_view(self, view: View):
        """Switch view and trigger rerun."""
        st.session_state["current_view"] = view
        st.rerun()

    def run(self):
        """Render the current view."""
        view = self.views[self.current_view]
        view.render()


if __name__ == "__main__":
    app = ClaimAssistantApp()
    app.run()
