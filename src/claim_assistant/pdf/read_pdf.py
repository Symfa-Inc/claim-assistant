# from fillpdf import fillpdfs

# input_path = "/home/maken/symfa/claim-assistant/data/forms/dwc/form_filled.pdf"
# data = fillpdfs.get_form_fields(input_path)
# print(data)

from pypdf import PdfReader


def get_form_fields_pypdf(pdf_path: str):
    """Simple extraction of form fields using pypdf."""
    reader = PdfReader(pdf_path)
    fields = {}

    # Try to get fields from AcroForm
    if reader.trailer["/Root"].get("/AcroForm"):
        acroform = reader.trailer["/Root"]["/AcroForm"]
        if acroform.get("/Fields"):
            for field in acroform["/Fields"]:
                field_obj = field.get_object()
                name = field_obj.get("/T", "")
                value = field_obj.get("/V", "")
                fields[name] = value

    return fields


# Usage:
pdf_path = "/home/maken/symfa/claim-assistant/data/forms/dwc/form_filled.pdf"
form_fields = get_form_fields_pypdf(pdf_path)
print(form_fields)

# Save form_fields to JSON file
import json

output_json_path = "/home/maken/symfa/claim-assistant/data/forms/dwc/extracted_form_fields.json"
with open(output_json_path, "w") as json_file:
    json.dump(form_fields, json_file, indent=2)

# from pypdf import PdfReader

# def extract_filled_fields(pdf_path: str) -> dict:
#     """Extract filled form fields from a PDF."""
#     reader = PdfReader(pdf_path)
#     filled_fields = {}

#     # Iterate through all pages
#     for page_num, page in enumerate(reader.pages):
#         # Check if page has annotations (form fields)
#         if "/Annots" in page:
#             annotations = page["/Annots"]

#             for annotation in annotations:
#                 # Get the annotation object
#                 annot_obj = annotation.get_object()

#                 # Check if it's a form field (widget annotation)
#                 if annot_obj.get("/Subtype") == "/Widget":
#                     # Get field name
#                     field_name = annot_obj.get("/T")
#                     if field_name:
#                         field_name = field_name

#                     # Get field value
#                     field_value = annot_obj.get("/V")
#                     if field_value:
#                         filled_fields[field_name] = field_value

#                     # Alternative: get default appearance value
#                     if not field_value and "/AP" in annot_obj:
#                         ap = annot_obj["/AP"]
#                         if "/N" in ap:
#                             filled_fields[field_name] = "Has appearance stream"

#     # Also check if there's a global form (AcroForm)
#     if "/AcroForm" in reader.trailer["/Root"]:
#         acro_form = reader.trailer["/Root"]["/AcroForm"]
#         if "/Fields" in acro_form:
#             fields = acro_form["/Fields"]
#             for field in fields:
#                 field_obj = field.get_object()
#                 field_name = field_obj.get("/T")
#                 field_value = field_obj.get("/V")

#                 if field_name and field_value:
#                     filled_fields[field_name] = field_value

#     return filled_fields

# def extract_all_form_data(pdf_path: str) -> dict:
#     """Extract all form-related data from PDF."""
#     reader = PdfReader(pdf_path)
#     form_data = {
#         "filled_fields": {},
#         "field_names": [],
#         "text_content": ""
#     }

#     # Extract text content
#     text_parts = []
#     for page in reader.pages:
#         text_parts.append(page.extract_text())
#     form_data["text_content"] = "\n".join(text_parts)

#     # Extract form fields
#     try:
#         # Method 1: Check AcroForm
#         if "/AcroForm" in reader.trailer["/Root"]:
#             acro_form = reader.trailer["/Root"]["/AcroForm"]
#             if "/Fields" in acro_form:
#                 for field in acro_form["/Fields"]:
#                     field_obj = field.get_object()
#                     field_name = field_obj.get("/T", "Unknown")
#                     field_value = field_obj.get("/V", "")

#                     form_data["field_names"].append(field_name)
#                     if field_value:
#                         form_data["filled_fields"][field_name] = field_value

#         # Method 2: Check page annotations
#         for page in reader.pages:
#             if "/Annots" in page:
#                 for annot in page["/Annots"]:
#                     annot_obj = annot.get_object()
#                     if annot_obj.get("/Subtype") == "/Widget":
#                         field_name = annot_obj.get("/T", "Unknown")
#                         field_value = annot_obj.get("/V", "")

#                         if field_name not in form_data["field_names"]:
#                             form_data["field_names"].append(field_name)

#                         if field_value and field_name not in form_data["filled_fields"]:
#                             form_data["filled_fields"][field_name] = field_value

#     except Exception as e:
#         print(f"Error extracting form fields: {e}")

#     return form_data

# # Update your existing code:
# if __name__ == "__main__":
#     pdf_path = "/home/maken/symfa/claim-assistant/data/forms/dwc/form_filled.pdf"

#     # Method 1: Extract filled fields only
#     filled_fields = extract_filled_fields(pdf_path)
#     print("Filled Fields:")
#     for field_name, field_value in filled_fields.items():
#         print(f"  {field_name}: {field_value}")

#     print("\n" + "="*50 + "\n")

#     # Method 2: Extract all form data
#     all_form_data = extract_all_form_data(pdf_path)
#     print("All Form Data:")
#     print(f"Field Names: {all_form_data['field_names']}")
#     print(f"Filled Fields: {all_form_data['filled_fields']}")
#     print(f"Text Content Preview: {all_form_data['text_content'][:200]}...")
