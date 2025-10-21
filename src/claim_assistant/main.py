import logging
import os
import time
from datetime import datetime
from pathlib import Path

from openai import OpenAI

from claim_assistant import PROJECT_DIR
from claim_assistant.models.form import Form
from claim_assistant.processors import (
    ClaimValidationProcessor,
    FormFillingProcessor,
    PDFMappingProcessor,
    PolicyDatabaseProcessor,
)
from claim_assistant.schemas.coverage_analysis import CoverageAnalysis
from claim_assistant.schemas.mock_policy_record import MockPolicyRecord
from claim_assistant.settings import OpenAISettings

logger = logging.getLogger(__name__)


def main(
    run_dir: str,
    input_pdf_path: str | Path,
    form_json_path: str | Path,
    policy_db_path: str | Path,
) -> None:
    """
    Main entry point for the claim processing workflow.

    Steps:
        1. Fill the form using LLM extraction from the input PDF.
        2. Load the mock policy database and find the matching record.
        3. Validate the claim against policy coverage.
        4. Generate a structured PDF summary report.
    """
    start_time = time.time()

    # --- output directory ---
    output_pdf_path = os.path.join(run_dir, "claim_summary.pdf")
    log_path = os.path.join(run_dir, "run.log")
    file_handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    file_handler.setLevel(logging.INFO)

    # --- Setup logging and output directory ---
    logger = logging.getLogger("claim_pipeline")
    logger.setLevel(logging.INFO)
    # Clear any pre-existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"),
    )

    # File handler
    file_handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"),
    )

    # Attach both handlers once
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    logging.getLogger("httpx").setLevel(logging.WARNING)

    # --- Initialize processors ---
    settings = OpenAISettings()
    client = OpenAI(api_key=settings.openai_api_key)
    form_processor = FormFillingProcessor(client, logger)
    db_processor = PolicyDatabaseProcessor(policy_db_path, logger)
    validation_processor = ClaimValidationProcessor(client, logger)
    report_processor = PDFMappingProcessor(logger)

    # --- Workflow ---
    logger.info("Step 1: Extracting and filling form fields from PDF...")
    form: Form = form_processor.process(input_pdf_path, form_json_path)

    logger.info("Step 2: Fetching policy from database...")
    policy: MockPolicyRecord | None = db_processor.process(form)
    if not policy:
        logger.error(
            "No matching policy found for Policy ID: %s",
            form.policy_id.answer,
        )
        return

    logger.info("Step 3: Validating claim against policy record...")
    analysis: CoverageAnalysis = validation_processor.process(form, policy)

    logger.info("Step 4: Generating structured summary report...")
    report_processor.process(form, policy, analysis, output_pdf_path)

    elapsed = time.time() - start_time
    logger.info(f"Claim processing completed in {elapsed:.1f} seconds")
    logger.info(f"Artifacts saved in: {run_dir}")
    logger.info(f"Report: {output_pdf_path}")
    logger.info(f"Log: {log_path}")


if __name__ == "__main__":
    # Paths for input and form template
    policy_db_path = os.path.join(PROJECT_DIR, "data", "policies", "policies.json")
    input_pdf_path = os.path.join(
        PROJECT_DIR,
        "data",
        "demo",
        "dwc",
        "filled_digital.pdf",
    )
    form_json_path = os.path.join(
        PROJECT_DIR,
        "data",
        "forms",
        "demo_DWC",
        "form_model.json",
    )

    run_dir = os.path.join(
        PROJECT_DIR,
        "data",
        "runs",
        datetime.now().strftime("%Y%m%d_%H%M%S"),
    )
    os.makedirs(run_dir, exist_ok=True)

    # --- Run full processing pipeline ---
    main(run_dir, input_pdf_path, form_json_path, policy_db_path)
