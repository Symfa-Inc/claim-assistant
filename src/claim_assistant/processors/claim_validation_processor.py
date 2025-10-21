import logging
from datetime import datetime
from typing import Literal

from Levenshtein import ratio as levenshtein_ratio
from openai import OpenAI

from claim_assistant.models.form import Form
from claim_assistant.schemas.coverage_analysis import CoverageAnalysis
from claim_assistant.schemas.mock_policy_record import MockPolicyRecord


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
    def _llm_coverage_analysis_pdf(
        self,
        form: Form,
        file_id: str,
    ) -> CoverageAnalysis:
        """
        Perform LLM-based reasoning on whether the incident described
        in a filled claim form is covered by the policy document provided
        as a PDF (uploaded to OpenAI as a file reference).

        Args:
            form: Filled Form object containing all extracted answers.
            file_id: OpenAI file ID referencing the uploaded policy PDF.

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

    def _llm_coverage_analysis_text(
        self,
        form: Form,
        policy: MockPolicyRecord,
    ) -> CoverageAnalysis:
        """
        Perform LLM-based reasoning on whether the incident described
        in a filled claim form is covered by the provided policy text.

        Unlike the PDF-based version, this method uses raw textual
        policy data (e.g., policy_coverage) for analysis.

        Args:
            form: Filled Form object containing all extracted answers.
            policy: MockPolicyRecord with coverage description and metadata
                    (policy_number, holder names, validity period, etc.).

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
                                    "=== CLAIM FORM DETAILS ===\n"
                                    f"{filled_answers}\n\n"
                                    "=== POLICY DETAILS ===\n"
                                    f"Policy Number: {policy.policy_number}\n"
                                    f"Policy Holder: {policy.policy_holder_first_name} {policy.policy_holder_last_name}\n"
                                    f"Coverage Period: {policy.start_date} to {policy.end_date}\n\n"
                                    f"Coverage Description:\n{policy.policy_coverage or 'No coverage text available.'}\n\n"
                                    "=== TASK ===\n"
                                    "- Determine whether the reported incident plausibly falls within policy coverage.\n"
                                    "- Identify possible reasons for denial, if applicable.\n"
                                    "- Return only a JSON object with fields:\n"
                                    "  'executive_summary': string,\n"
                                    "  'conclusion': 'positive' or 'negative'."
                                ),
                            },
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

        # --- Step 0: Ensure OCR didn't fail completely ---
        policy_id = getattr(form.policy_id, "answer", None)
        first_name = getattr(form.first_name, "answer", None)
        last_name = getattr(form.last_name, "answer", None)
        incident_date = getattr(form.date_of_incident, "answer", None)

        # Step 0: Ensure form is not empty
        if not any([policy_id, first_name, last_name, incident_date]):
            self.logger.error("OCR extraction failed — all critical fields are empty.")
            return CoverageAnalysis(
                executive_summary=(
                    "OCR extraction failed. No valid data was extracted from the claim form. "
                    "The form contains empty policy number, name, and incident date fields."
                ),
                conclusion="negative",
                confidence=0.0,
            )

        # Step 1: Match by policy number
        if not policy:
            self.logger.warning("No policy found for the given policy ID.")
            return CoverageAnalysis(
                executive_summary="Policy not found in database.",
                conclusion="negative",
                confidence=1,
            )

        # --- Step 2: Compute weighted Levenshtein similarity ---
        form_first = getattr(form.first_name, "answer", "").strip().lower()
        form_last = getattr(form.last_name, "answer", "").strip().lower()
        form_policy_id = getattr(form.policy_id, "answer", "").strip().lower()

        policy_first = policy.policy_holder_first_name.strip().lower()
        policy_last = policy.policy_holder_last_name.strip().lower()
        policy_id = policy.policy_number.strip().lower()

        sim_policy = (
            levenshtein_ratio(form_policy_id, policy_id) if form_policy_id else 0.0
        )
        sim_first = levenshtein_ratio(form_first, policy_first) if form_first else 0.0
        sim_last = levenshtein_ratio(form_last, policy_last) if form_last else 0.0
        confidence = round(
            0.6 * sim_policy + 0.15 * sim_first + 0.25 * sim_last,
            3,
        )
        ocr_uncertain = False

        if confidence < 1:
            self.logger.warning(
                f"Low OCR name match confidence: {confidence:.2f} "
                f"(form='{form_first} {form_last}', policy='{policy_first} {policy_last}')",
            )
            ocr_uncertain = True

        # --- Step 3: Handle very low confidence ---
        if confidence < 0.5:
            self.logger.warning(
                f"Low OCR match confidence: {confidence:.2f}\n"
                f"→ Extracted (form): policy_id='{form_policy_id}', "
                f"first_name='{form_first}', last_name='{form_last}'\n"
                f"→ Reference (policy): policy_id='{policy_id}', "
                f"first_name='{policy_first}', last_name='{policy_last}'",
            )
            return CoverageAnalysis(
                executive_summary=(
                    f"No sufficiently similar policy record found. "
                    f"Integrated confidence score ({confidence:.2f}) indicates no reliable match."
                ),
                conclusion="negative",
                confidence=confidence,
            )

        # --- Step 4: Date coverage check ---
        date_field = getattr(form.date_of_incident, "answer", None)
        try:
            date_of_injury = self._parse_date(date_field)
        except Exception:
            self.logger.error("Invalid or missing incident date in form.")
            return CoverageAnalysis(
                executive_summary="Invalid date format in claim form.",
                conclusion="negative",
                confidence=confidence,
            )

        if not (policy.start_date <= date_of_injury.date() <= policy.end_date):
            self.logger.info("Incident date lies outside policy coverage period.")
            return CoverageAnalysis(
                executive_summary="Incident date not covered by policy validity period.",
                conclusion="negative",
                confidence=confidence,
            )

        # --- Step 5: LLM-based coverage analysis ---
        self.logger.info("Performing LLM-based policy coverage analysis...")

        policy_path = policy.get_policy_path()
        if not policy_path:
            self.logger.error("Policy document file is missing.")
            return CoverageAnalysis(
                executive_summary="Policy document not available for analysis.",
                conclusion="negative",
                confidence=confidence,
            )

        # pdf_path = validate_pdf(policy_path)
        #
        # with openai_file(self.client, pdf_path, self.logger) as file_id:
        #     analysis = self._llm_coverage_analysis_pdf(form, file_id)

        analysis = self._llm_coverage_analysis_text(form, policy)

        # if low name confidence, mark as uncertain
        if ocr_uncertain:
            analysis.conclusion = "uncertain"
            analysis.executive_summary += (
                f"\n\nLow overall OCR match confidence ({confidence:.2f}). "
                f"Form fields (policy ID, first name, last name) show partial similarity "
                f"to the policy record. Claim likely corresponds to the correct policyholder "
                f"but cannot be verified with high certainty due to extraction inconsistencies."
            )
        analysis.confidence = confidence

        self.logger.info("Claim validation completed successfully.")
        return analysis
