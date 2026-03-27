import json
import logging
from pathlib import Path

from claim_assistant.schemas import Form, FormFieldAnswer, MockPolicyRecord
from Levenshtein import ratio


class PolicyDatabaseProcessor:
    """
    Processor responsible for interfacing with a mock policy database.

    It loads structured policy data from a JSON file and allows retrieval
    of specific policies based on information extracted from a filled form.
    Supports fuzzy matching via Levenshtein similarity if exact matches fail.
    """

    def __init__(self, json_path: str | Path, logger: logging.Logger) -> None:
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

        self.logger.info(
            f"Loaded {len(self._policies)} policy records from {path.name}.",
        )

    def _find_closest_policy(self, query: str) -> tuple[MockPolicyRecord | None, float]:
        """
        Find the closest matching policy number using Levenshtein similarity.

        Args:
            query: Policy number extracted from the form.

        Returns:
            Tuple of (MockPolicyRecord or None, similarity_score in [0, 1]).
        """
        if not query:
            return None, 0.0

        query = query.strip().upper()
        best_match = None
        best_score = 0.0

        for policy_number, record in self._policies.items():
            score = ratio(query, policy_number.upper())
            if score > best_score:
                best_match = record
                best_score = score

        self.logger.debug(
            f"Fuzzy search for '{query}' -> Best match: "
            f"{getattr(best_match, 'policy_number', None)} (score={best_score:.3f})",
        )

        return best_match, best_score

    def process(self, form: Form) -> MockPolicyRecord | None:
        """
        Retrieve a policy record based on the policy ID contained in the form.
        Falls back to fuzzy Levenshtein matching if no exact match exists.

        Args:
            form: A filled Form object containing a 'policy_id' field.

        Returns:
            Tuple of:
              - MockPolicyRecord | None — the best match (or None if none found)
              - float — confidence score (1.0 for exact match, otherwise Levenshtein similarity)
        """
        policy_ans = getattr(form.policy_id, "answer", None)
        if isinstance(policy_ans, FormFieldAnswer):
            policy_id = policy_ans.value
        else:
            policy_id = policy_ans

        if not policy_id:
            self.logger.warning("Form does not contain a valid policy ID answer.")
            return None

        exact_match = self._policies.get(policy_id)
        if exact_match:
            self.logger.info(f"Exact policy match found for ID '{policy_id}'.")
            return exact_match

        self.logger.info(f"No exact match for ID '{policy_id}', trying fuzzy search...")
        match, score = self._find_closest_policy(policy_id)
        self.logger.info(
            f"Fuzzy match found: '{match.policy_number}' (similarity={score:.2f})",
        )

        return match
