import json
import logging
import os
import time
from pathlib import Path

from claim_assistant import PROJECT_DIR
from claim_assistant.pdf.analyse_case import validate_claim
from claim_assistant.pdf.read_pdf import extract_form_fields
from claim_assistant.pdf.write_pdf import write_summary_pdf

logger = logging.getLogger(__name__)


def main(
    input_pdf_path: str | Path,
    policies: list[dict],
    ouptut_pdf_path: str | Path = "./claim_summary.pdf",
):
    start_time = time.time()
    logger.info("Starting claim processing workflow")

    logger.info("Extracting form fields from PDF: %s", input_pdf_path)
    claim_dict = extract_form_fields(input_pdf_path)

    logger.info("Validating claim against %d policies", len(policies))
    claim_dict = validate_claim(claim_dict, policies)

    logger.info("Writing summary PDF to: %s", ouptut_pdf_path)
    write_summary_pdf(claim_dict, ouptut_pdf_path)

    end_time = time.time()
    total_time = end_time - start_time
    logger.info("Claim processing completed in %.1f seconds", total_time)


if __name__ == "__main__":
    # Configure logging for standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)

    policies_json = """
    [
      {
        "policy_number": "SIC123456789",
        "policy_holder_name": "John Smith",
        "start_date": "2023-05-15",
        "end_date": "2024-05-15",
        "policy_coverage": "Workplace injury compensation including medical expenses, rehabilitation services, and wage replacement."
      },
      {
        "policy_number": "POL123456789",
        "policy_holder_name": "John Doe",
        "start_date": "2022-03-20",
        "end_date": "2024-03-20",
        "policy_coverage": "Occupational accident insurance covering hospital bills, temporary disability payments, and emergency treatment costs."
      }
    ]
    """
    policies = json.loads(policies_json)
    path = os.path.join(PROJECT_DIR, "data", "forms", "dwc", "form_filled_flat.pdf")
    main(path, policies)
