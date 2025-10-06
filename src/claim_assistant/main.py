import json
import os
from pathlib import Path

from claim_assistant import PROJECT_DIR
from claim_assistant.pdf.analyse_case import validate_claim
from claim_assistant.pdf.read_pdf import extract_form_fields
from claim_assistant.pdf.write_pdf import write_summary_pdf


def main(
    input_pdf_path: str | Path,
    policies: list[dict],
    ouptut_pdf_path: str | Path = "./claim_summary.pdf",
):
    print("Extracting form fields...")
    claim_dict = extract_form_fields(input_pdf_path)
    print("Validating claim against policies...")
    claim_dict = validate_claim(claim_dict, policies)
    print("Writing summary PDF...")
    write_summary_pdf(claim_dict, ouptut_pdf_path)


if __name__ == "__main__":
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
