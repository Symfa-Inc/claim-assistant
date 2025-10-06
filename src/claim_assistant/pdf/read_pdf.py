# from pypdf import PdfReader


# def get_form_fields_pypdf(pdf_path: str):
#     """Simple extraction of form fields using pypdf."""
#     reader = PdfReader(pdf_path)
#     fields = {}

#     # Try to get fields from AcroForm
#     if reader.trailer["/Root"].get("/AcroForm"):
#         acroform = reader.trailer["/Root"]["/AcroForm"]
#         if acroform.get("/Fields"):
#             for field in acroform["/Fields"]:
#                 field_obj = field.get_object()
#                 name = field_obj.get("/T", "")
#                 value = field_obj.get("/V", "")
#                 fields[name] = value

#     return fields

# Save form_fields to JSON file
# import json

# output_json_path = "/home/maken/symfa/claim-assistant/data/forms/cid/extracted_form_fields.json"
# with open(output_json_path, "w") as json_file:
#     json.dump(form_fields, json_file, indent=2)


# from datetime import date, time
# from uuid import uuid4

# import requests

# from claim_assistant.extraction.fnol_forms import DWCForm


# def extract_form_fields(pdf_path: str) -> dict[str, str | int | float | bool | date | time]:
#     """Extract form fields from a PDF using an external extraction service."""

#     # Get bytes
#     with open(pdf_path, "rb") as f:
#         bytes = f.read()

#     user_id = str(uuid4())
#     headers = {"x-key": user_id}

#     url = "https://extract-server-f34kggfazq-uc.a.run.app"

#     data = {
#         "user_id": user_id,
#         "description": "Insurance claim form data extraction from worker injury claims.",
#         "schema": DWCForm.model_json_schema(),
#         "instruction": (
#             "Extract worker injury claim information from FNOL forms. "
#             "Focus on personal details, injury specifics, employment information, and medical data."
#         ),
#     }

#     response = requests.post(f"{url}/extractors", json=data, headers=headers)
#     extractor = response.json()

#     result = requests.post(
#         f"{url}/extract",
#         data={"extractor_id": extractor["uuid"], "model_name": "gpt-3.5-turbo"},
#         files={"file": bytes},
#         headers=headers,
#     )

#     return result.json()["data"][2]


import os
from pathlib import Path

from openai import OpenAI

from claim_assistant.pdf.summary_form import SummaryForm


def extract_form_fields(
    pdf_path: str | Path,
) -> dict[str, str]:
    """
    Extract FNOL data from a PDF using OpenAI with structured (Pydantic) output.
    Returns a dict matching form_pydanitc_model.
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    if not client.api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    # Upload the PDF once and reference it via input_file
    with open(pdf_path, "rb") as f:
        uploaded = client.files.create(
            file=f,
            purpose="assistants",
        )  # or purpose="assistants"

    instruction = (
        "You are an expert at extracting workers' compensation FNOL data. "
        f"Extract values to fit the {SummaryForm.__name__} schema. Use ISO formats: dates=YYYY-MM-DD, "
        "times=HH:MM PM or AM. Use true/false for booleans. If a field is missing/unclear, use null. "
        "Do not invent data."
    )

    # Use OpenAI Responses API with structured outputs (Pydantic parsing)
    # try:
    resp = client.responses.parse(
        model="gpt-5-nano-2025-08-07",
        input=[
            {
                "role": "system",
                "content": "You return only data that conforms to the schema.",
            },
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": instruction},
                    {"type": "input_file", "file_id": uploaded.id},
                ],
            },
        ],
        # Parse directly into the Pydantic model
        text_format=SummaryForm,
        # temperature=0.0,
    )

    parsed = resp.output_parsed
    return parsed.model_dump(mode="python")  # dict with native types


if __name__ == "__main__":
    pdf_path = Path(
        "/home/maken/symfa/claim-assistant/data/forms/dwc/form_filled_flat.pdf",
    )
    form_fields = extract_form_fields(pdf_path)
    print(form_fields)
