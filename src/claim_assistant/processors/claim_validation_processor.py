import logging
from datetime import datetime
from typing import Literal

from openai import OpenAI

from claim_assistant.models.form import Form
from claim_assistant.schemas.coverage_analysis import CoverageAnalysis
from claim_assistant.schemas.mock_policy_record import MockPolicyRecord
from claim_assistant.utils import openai_file, validate_pdf


class ClaimValidationProcessor:
    """
    Processor responsible for matching a filled claim form with
    policy data and generating an analytical coverage summary.
    """

    def __init__(
        self,
        model_client: OpenAI,
        logger: logging.Logger,
        model_name: Literal[
            "gpt-5-2025-08-07",
            "gpt-5-mini-2025-08-07",
            "gpt-5-nano-2025-08-07",
        ] = "gpt-5-nano-2025-08-07",
    ) -> None:
        if model_name not in {
            "gpt-5-2025-08-07",
            "gpt-5-mini-2025-08-07",
            "gpt-5-nano-2025-08-07",
        }:
            raise ValueError("Invalid model name: must be one of the GPT-5 family.")
        self.client = model_client
        self.model_name = model_name
        self.logger = logger

    # -------------------------------
    # Utility
    # -------------------------------
    @staticmethod
    def _parse_date(date_str: str) -> datetime | None:
        """Parse date safely in ISO format."""
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except Exception:
            return None

    # -------------------------------
    # Core LLM analysis
    # -------------------------------
    def _llm_coverage_analysis(
        self,
        form: Form,
        file_id: str,
    ) -> CoverageAnalysis:
        """
        Perform LLM-based reasoning on whether the described injury
        in a filled claim form is likely covered by a given policy.

        Args:
            form: Filled Form object containing all extracted answers.
            policy: MockPolicyRecord instance representing the matched policy
                    (with fields like policy_coverage, policy_number, etc.).

        Returns:
            A CoverageAnalysis instance containing:
              - executive_summary: str — concise reasoning summary.
              - conclusion: Literal["positive", "negative"] — coverage assessment result.
        """
        self.logger.info("Performing LLM coverage reasoning...")

        # Combine filled answers into a readable summary block
        filled_answers = "\n".join(
            f"{field.text}: {field.answer}" for field in form.fields if field.answer
        )

        try:
            parsed = self.client.responses.parse(
                model=self.model_name,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": (
                                    "You are an insurance adjuster assistant.\n"
                                    "Analyze whether the injury described in the claim form "
                                    "is likely covered under the provided policy terms.\n\n"
                                    f"Claim form details:\n{filled_answers}\n\n"
                                    "Task:\n"
                                    "- Determine whether the reported incident plausibly falls within policy coverage.\n"
                                    "- Identify possible reasons for denial, if applicable.\n"
                                    "- Return only a JSON object with fields:\n"
                                    "  'executive_summary': string,\n"
                                    "  'conclusion': 'positive' or 'negative'."
                                ),
                            },
                            {"type": "input_file", "file_id": file_id},
                        ],
                    },
                ],
                text_format=CoverageAnalysis,
            )

            result = parsed.output_parsed
            if not result:
                self.logger.warning(
                    "LLM returned empty structured output; using fallback result.",
                )
                return CoverageAnalysis(
                    executive_summary="Analysis unavailable due to missing model output.",
                    conclusion="negative",
                )

            if isinstance(result, dict):
                return CoverageAnalysis(**result)
            return result

        except Exception as e:
            self.logger.error(f"Coverage reasoning failed: {e}")
            return CoverageAnalysis(
                executive_summary="Error occurred during analysis.",
                conclusion="negative",
            )

    # -------------------------------
    # Main validation logic
    # -------------------------------
    def process(
        self,
        form: Form,
        policy: MockPolicyRecord,
    ) -> CoverageAnalysis:
        """
        Validate a filled insurance claim form against stored policy data
        and produce a structured LLM-based reasoning summary.

        Workflow:
            1. Retrieve the policy record from the mock database using the policy ID.
            2. Verify that the claimant’s first and last names match the policyholder.
            3. Confirm that the incident date falls within the policy’s active coverage period.
            4. If validation passes, perform an LLM-based analysis of whether the claim
               plausibly falls under the policy coverage.

        Args:
            form: A filled Form instance containing extracted field answers.
            policy: Instance of MockPolicyRecord providing information extracted from database.

        Returns:
            - CoverageAnalysis: Structured summary including:
                • executive_summary – textual explanation of the decision.
                • conclusion – "positive" if coverage likely applies, otherwise "negative".
        """
        self.logger.info("Starting claim validation...")

        # Step 1: Match by policy number
        if not policy:
            self.logger.warning("No policy found for the given policy ID.")
            return CoverageAnalysis(
                executive_summary="Policy not found in database.",
                conclusion="negative",
            )

        # --- Step 2: Name verification ---
        form_first = getattr(form.first_name, "answer", "").strip().lower()
        form_last = getattr(form.last_name, "answer", "").strip().lower()
        policy_first = policy.policy_holder_first_name.strip().lower()
        policy_last = policy.policy_holder_last_name.strip().lower()

        if form_first != policy_first or form_last != policy_last:
            self.logger.warning("Claimant name does not match policyholder record.")
            return CoverageAnalysis(
                executive_summary="Policy found, but claimant name differs from policy holder.",
                conclusion="negative",
            )

        # --- Step 3: Date coverage check ---
        date_field = getattr(form.date_of_incident, "answer", None)
        try:
            date_of_injury = self._parse_date(date_field)
        except Exception:
            self.logger.error("Invalid or missing incident date in form.")
            return CoverageAnalysis(
                executive_summary="Invalid date format in claim form.",
                conclusion="negative",
            )

        if not (policy.start_date <= date_of_injury.date() <= policy.end_date):
            self.logger.info("Incident date lies outside policy coverage period.")
            return CoverageAnalysis(
                executive_summary="Incident date not covered by policy validity period.",
                conclusion="negative",
            )

        # --- Step 4: LLM-based coverage analysis ---
        self.logger.info("Performing LLM-based policy coverage analysis...")

        policy_path = policy.get_policy_path()
        if not policy_path:
            self.logger.error("Policy document file is missing.")
            return CoverageAnalysis(
                executive_summary="Policy document not available for analysis.",
                conclusion="negative",
            )

        pdf_path = validate_pdf(policy_path)

        with openai_file(self.client, pdf_path, self.logger) as file_id:
            analysis = self._llm_coverage_analysis(form, file_id)

        self.logger.info("Claim validation completed successfully.")
        return analysis
