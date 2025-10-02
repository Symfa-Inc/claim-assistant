from pathlib import Path
from typing import Type

from pydantic import BaseModel

# from claim_assistant.storage.db import check_db
from claim_assistant.pdf.fnol_forms import DWCForm, CIDForm
from claim_assistant.pdf.read_pdf import extract_form_fields
# from claim_assistant.pdf.write_pdf import make_summary_pdf


def main(path: Path, form_model: Type[BaseModel]):
    claim = extract_form_fields(path, form_model)
    # claim = check_db(claim)
    # make_summary_pdf(claim)


if __name__ == "__main__":
    path = Path("/home/maken/symfa/claim-assistant/data/forms/cid/form_filled_flat.pdf")
    form_model = CIDForm
    main(path, form_model)
