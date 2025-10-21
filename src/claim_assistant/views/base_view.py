from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from claim_assistant.app import ClaimAssistantApp


class View(Enum):
    HOME = auto()
    PROCESS_FORM = auto()
    RESULTS = auto()
    FORM_MODEL_SELECTION = auto()
    FORM_MODEL_EDITOR = auto()


class BaseView:
    """Base class for all app views."""

    def __init__(self, app: "ClaimAssistantApp"):
        self.app = app

    def render(self):
        raise NotImplementedError("Each view must implement its render() method.")
