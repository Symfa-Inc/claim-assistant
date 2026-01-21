import logging
import os
import time
from datetime import datetime
from pathlib import Path

from openai import OpenAI

from claim_assistant import PROJECT_DIR
from claim_assistant.processors import (
    ClaimValidationProcessor,
    DIKeyValueExtractionProcessor,
    DIKVFormFillingProcessor,
    PDFMappingProcessor,
    PolicyDatabaseProcessor,
)
from claim_assistant.schemas import CoverageAnalysisResponse
from claim_assistant.schemas.form import Form
from claim_assistant.schemas.mock_policy_record import MockPolicyRecord
from claim_assistant.settings import AzureDocumentIntelligenceSettings, OpenAISettings

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
        1. Extract DI key/value pairs from the input PDF (with evidence).
        2. Fill the form using one-shot LLM mapping from DI KV pairs.
        3. Load the mock policy database and find the matching record.
        4. Validate the claim against policy coverage (LLM) and attach context.
        5. Generate a structured PDF summary report.
    """
    start_time = time.time()

    # --- output directory ---
    output_pdf_path = os.path.join(run_dir, "claim_summary.pdf")
    log_path = os.path.join(run_dir, "run.log")

    # --- Setup logging and output directory ---
    logger = logging.getLogger("claim_pipeline")
    logger.setLevel(logging.INFO)
    if logger.hasHandlers():
        logger.handlers.clear()

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"),
    )

    file_handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"),
    )

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    logging.getLogger("httpx").setLevel(logging.WARNING)

    # --- Initialize settings / clients ---
    openai_settings = OpenAISettings()
    client = OpenAI(api_key=openai_settings.openai_api_key)

    di_settings = AzureDocumentIntelligenceSettings()

    # --- Initialize processors ---
    di_kv_processor = DIKeyValueExtractionProcessor(
        api_key=di_settings.documentintelligence_api_key,
        endpoint=di_settings.documentintelligence_endpoint,
        logger=logger,
    )
    form_processor = DIKVFormFillingProcessor(model_client=client, logger=logger)
    db_processor = PolicyDatabaseProcessor(policy_db_path, logger)
    validation_processor = ClaimValidationProcessor(client, logger)
    report_processor = PDFMappingProcessor(logger)

    # --- Workflow ---
    logger.info("Step 1: Extracting DI key/value pairs from PDF...")
    di_payload = di_kv_processor.process(input_pdf_path)

    logger.info("Step 2: Filling form fields from DI KV pairs via LLM...")
    form: Form = form_processor.process(
        form_json_path=form_json_path,
        di_payload=di_payload,
    )

    logger.info("Step 3: Fetching policy from database...")
    policy: MockPolicyRecord | None = db_processor.process(form)

    logger.info("Step 4: Validating claim against policy record...")
    analysis: CoverageAnalysisResponse = validation_processor.process(form, policy)

    logger.info("Step 5: Generating structured summary report...")
    report_processor.process(analysis=analysis, output_path=output_pdf_path)

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
        "forms",
        "FL",
        "form_hw_POL987654321.pdf",
    )
    form_json_path = os.path.join(
        PROJECT_DIR,
        "data",
        "forms",
        "FL",
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
