import json
import logging
from pathlib import Path
from typing import Union

from claim_assistant.models.form import Form
from claim_assistant.schemas.mock_policy_record import MockPolicyRecord


class PolicyDatabaseProcessor:
    """
    Processor responsible for interfacing with a mock policy database.

    It loads structured policy data from a JSON file and allows retrieval
    of specific policies based on information extracted from a filled form.
    """

    def __init__(self, json_path: Union[str, Path], logger: logging.Logger) -> None:
        """
        Args:
            json_path: Path to the JSON file containing policy records.
            logger: Standard logger instance for structured logging.
        """
        self.logger = logger
        path = Path(json_path)
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"Policy database file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError("Policy database JSON must contain a list of records.")

        # Store policies in a dict keyed by policy number
        self._policies: dict[str, MockPolicyRecord] = {
            record["policy_number"]: MockPolicyRecord(**record) for record in data
        }

        self.logger.info(f"Loaded {len(self._policies)} policy records from {path.name}.")

    def process(self, form: Form) -> MockPolicyRecord | None:
        """
        Retrieve a policy record based on the policy ID contained in the form.

        Args:
            form: A filled Form object containing a 'policy_id' field.

        Returns:
            MockPolicyRecord if a matching policy exists, otherwise None.
        """
        policy_id = getattr(form.policy_id, "answer", None)
        if not policy_id:
            self.logger.warning("Form does not contain a valid policy ID answer.")
            return None

        policy = self._policies.get(policy_id)
        if policy:
            self.logger.info(f"Policy found for ID '{policy_id}'.")
        else:
            self.logger.warning(f"No policy found for ID '{policy_id}'.")

        return policy