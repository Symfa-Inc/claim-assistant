from pathlib import Path

# from claim_assistant.storage.db import check_db
from claim_assistant.pdf.read_pdf import extract_form_fields
from claim_assistant.pdf.write_pdf import write_summary_pdf


def main(
    input_pdf_path: str | Path,
    ouptut_pdf_path: str | Path = "data/forms/dwc/claim_summary.pdf",
):
    claim_dict = extract_form_fields(input_pdf_path)
    # claim_dict = check_db(claim_dict)
    print(claim_dict)
    write_summary_pdf(claim_dict, ouptut_pdf_path)


if __name__ == "__main__":
    path = "/home/maken/symfa/claim-assistant/data/forms/dwc/form_filled_flat.pdf"
    main(path)
