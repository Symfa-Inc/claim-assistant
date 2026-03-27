import json
import os
import time
from typing import Any

from openai import OpenAI, OpenAIError

from claim_assistant import PROJECT_DIR
from claim_assistant.data.settings import OpenAISettings
from claim_assistant.schemas.form import Form  # your validation class

# -------------------------------
# Configuration
# -------------------------------
PROMPT = """You are an expert data engineer digitizing PDF claim forms.

You will receive the extracted text of one PDF form.
Your task is to produce a complete JSON array describing **all form fields**, in the exact order they appear.

Each JSON object must follow this schema strictly:

{
  "order": <positive integer, order of appearance in the PDF>,
  "text": "<exact label or question text from the form>",
  "description": "<optional hint or clarification>",
  "alias": "<one of: 'policy_id', 'first_name', 'last_name', 'date_of_incident', or null>",
  "data_type": "<one of: 'string', 'number', 'date', 'time', 'boolean', 'text', 'enum'>",
  "meta": { "<optional>": ... }
}

---

### Rules

1. **Include every field** that can accept user input (text box, checkbox, date, number, etc.).
   Skip only headings, instructions, or decorative text.

2. **Output only valid JSON** — the result must be directly loadable with `json.loads()`.

3. **Ordering**
   - Assign `order` values incrementally (1, 2, 3, …) following their appearance order in the PDF.

4. **Alias assignment**
   - Use exactly one of these aliases if the field clearly matches:
     • `"policy_id"` — for “Policy Number”, “Policy ID”, etc.
     • `"first_name"` — for “First Name”, “Given Name”, etc.
     • `"last_name"` — for “Last Name”, “Surname”, etc.
     • `"date_of_incident"` — for “Date of Incident”, “Accident Date”, etc.
   - These four fields are **required**.
     - If a field with the same meaning exists but has a slightly different label, assign the correct alias.
     - If a field combines multiple values (e.g., “Full Name”), you may split it into separate entries (first and last name).
   - For **all other fields**, set `"alias": null`.
   - Do **not invent new aliases** beyond these four.

5. **data_type selection**
   - `"string"` → short text inputs (names, IDs, addresses, phone numbers).
   - `"text"` → long descriptive answers (e.g., “Describe the accident”).
   - `"number"` → numeric inputs (amounts, IDs that are purely numeric).
   - `"date"` → any date-type field.
   - `"time"` → any time-of-day field.
   - `"boolean"` → yes/no or checkbox fields.
   - `"enum"` → fields with predefined options; include them under `"meta": {"labels": [...]}`.

6. **meta field rules**
   - For `"enum"` → `{"labels": ["Option1", "Option2", ...]}`
   - For `"date"` → `{"format": "YYYY-MM-DD"}`
   - For `"time"` → `{"format": "HH:mm:ss"}`
   - For all others → `{}`

7. **description**
   - Optional. Include if it adds clarity about purpose or context.

8. **Output format**
   - Return **only** a valid JSON array.
   - Do not include Markdown, prose, explanations, or comments.

---

### ✅ Example Output

[
  {
    "order": 1,
    "text": "Policy Number",
    "description": "Unique identifier of the policy.",
    "alias": "policy_id",
    "data_type": "string",
    "meta": {}
  },
  {
    "order": 2,
    "text": "First Name",
    "description": "Given name of the insured individual.",
    "alias": "first_name",
    "data_type": "string",
    "meta": {}
  },
  {
    "order": 3,
    "text": "Last Name",
    "description": "Family name of the insured individual.",
    "alias": "last_name",
    "data_type": "string",
    "meta": {}
  },
  {
    "order": 4,
    "text": "Date of Incident",
    "description": "Date when the accident occurred.",
    "alias": "date_of_incident",
    "data_type": "date",
    "meta": {"format": "YYYY-MM-DD"}
  },
  {
    "order": 5,
    "text": "Description of Accident",
    "description": "Detailed description of the event.",
    "alias": null,
    "data_type": "text",
    "meta": {}
  },
  {
    "order": 6,
    "text": "Type of Injury",
    "description": "Select one of the injury categories.",
    "alias": null,
    "data_type": "enum",
    "meta": {"labels": ["Slip", "Fall", "Collision", "Other"]}
  }
]
"""

settings = OpenAISettings()
client = OpenAI(api_key=settings.openai_api_key)

BASE_DIR = os.path.join(PROJECT_DIR, "data", "forms")
MODEL_NAME = "gpt-5-mini-2025-08-07"  # adjust as needed

INPUT_PDF = "form_raw.pdf"
OUTPUT_JSON = "form_model.json"
FAILED_NAME = "form_model_failed.json"

# Structured Outputs schema (strict) — matches your generator prompt
JSON_SCHEMA = {
    "name": "form_fields",
    "schema": {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "order": {"type": "integer", "minimum": 1},
                "text": {"type": "string"},
                "description": {"type": ["string", "null"]},
                "alias": {
                    "type": ["string", "null"],
                    "enum": [
                        "policy_id",
                        "first_name",
                        "last_name",
                        "date_of_incident",
                        None,
                    ],
                },
                "data_type": {
                    "type": "string",
                    "enum": [
                        "string",
                        "number",
                        "date",
                        "time",
                        "boolean",
                        "text",
                        "enum",
                    ],
                },
                "meta": {"type": "object"},
            },
            "required": ["order", "text", "alias", "data_type", "meta"],
            "additionalProperties": False,
        },
    },
}
# -------------------------------
# Helpers
# -------------------------------


def upload_pdf(pdf_path: str) -> str:
    """Upload a PDF and return the file ID."""
    for attempt in range(3):
        try:
            with open(pdf_path, "rb") as f:
                file_obj = client.files.create(file=f, purpose="user_data")
            return file_obj.id
        except Exception as e:
            print(f"  ⚠️ Upload attempt {attempt + 1} failed: {e}")
            time.sleep(2)
    raise RuntimeError(f"Failed to upload file after 3 attempts: {pdf_path}")


def _extract_text_from_response(resp) -> str:
    """
    Robustly extract text from Responses API result without relying on helper attributes.
    See example response structure with `output[*].content[*].type='output_text'`.  [oai_citation:1‡OpenAI Cookbook](https://cookbook.openai.com/examples/responses_api/reasoning_items?utm_source=chatgpt.com)
    """
    try:
        data = resp.model_dump()
    except Exception:
        try:
            # fallback if resp is already a dict-like
            data = json.loads(resp.json())
        except Exception:
            # last resort: try treating as plain dict
            data = dict(resp)

    out = data.get("output") or []
    for item in out:
        if item.get("type") == "message":
            for c in item.get("content", []):
                # 'output_text' is canonical; some SDKs may expose plain 'text'
                if c.get("type") in ("output_text", "text"):
                    return c.get("text", "")
    # If nothing found, try Responses 'text' aggregate (some SDKs expose it)
    t = data.get("text")
    if isinstance(t, dict) and "value" in t:
        return t["value"]
    raise ValueError("Could not extract text output from response payload.")


# -------------------------------
# LLM call
# -------------------------------
def convert_pdf_to_json(pdf_path: str) -> list[dict[str, Any]]:
    """
    Upload PDF, call Responses API with PROMPT + file, return parsed JSON list.
    Uses content parts: {'type': 'text'} and {'type': 'file', 'file_id': ...}.
    Docs: file ID inputs & Responses API are recommended for PDFs and multimodal.  [oai_citation:2‡OpenAI Platform](https://platform.openai.com/docs/guides/images-vision?utm_source=chatgpt.com)
    """
    print(f"  → Uploading {os.path.basename(pdf_path)}...")
    file_id = upload_pdf(pdf_path)
    print(f"  ✓ Uploaded (file_id={file_id}). Requesting model...")

    try:
        resp = client.responses.create(
            model=MODEL_NAME,
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": PROMPT
                            + "\n\nExtract all fields from the attached PDF.",
                        },
                        {
                            "type": "input_file",
                            "file_id": file_id,
                        },
                    ],
                },
            ],
            # You can set max_output_tokens if needed, e.g. 8192
        )
    except OpenAIError as e:
        # Attempt cleanup of uploaded file
        try:
            client.files.delete(file_id)
        except Exception:
            pass
        raise RuntimeError(f"OpenAI API call failed: {e}")

    # Best-effort cleanup (avoid storage pile-up)
    try:
        client.files.delete(file_id)
    except Exception:
        pass

    raw_text = _extract_text_from_response(resp)
    if not raw_text:
        raise ValueError("Empty response text from model.")

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as e:
        # Dump the raw text into an error so caller can persist it under *_failed.json
        raise ValueError(
            f"Model returned non-JSON output: {e}\nRAW:\n{raw_text[:1000]}",
        )

    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON array, got {type(data)}")

    print(f"  ✓ Parsed {len(data)} fields.")
    return data


# -------------------------------
# Main process
# -------------------------------
def process_forms(base_dir: str = BASE_DIR):
    failed: list[str] = []
    for form_name in sorted(os.listdir(base_dir)):
        form_dir = os.path.join(base_dir, form_name)
        if not os.path.isdir(form_dir):
            continue

        pdf_path = os.path.join(form_dir, INPUT_PDF)
        out_json = os.path.join(form_dir, OUTPUT_JSON)
        fail_json = os.path.join(form_dir, FAILED_NAME)

        # Only process if raw PDF exists and model JSON not present
        if not os.path.isfile(pdf_path):
            continue
        if os.path.isfile(out_json):
            continue

        print(f"\n📄 Processing form: {form_name}")
        try:
            items = convert_pdf_to_json(pdf_path)
        except Exception as e:
            print(f"❌ Conversion failed for {form_name}: {e}")
            # Persist a diagnostic JSON (no schema) to aid debugging
            with open(fail_json, "w", encoding="utf-8") as f:
                json.dump(
                    {"error": str(e), "stage": "conversion"},
                    f,
                    indent=2,
                    ensure_ascii=False,
                )
            failed.append(form_name)
            continue

        # Validate with your Form runtime initializer
        try:
            _ = Form(items)  # will raise on missing declared aliases, bad fields, etc.
            print("  ✅ Validation passed.")
        except Exception as e:
            print(f"  ❌ Validation failed for {form_name}: {e}")
            with open(fail_json, "w", encoding="utf-8") as f:
                json.dump(
                    {"error": str(e), "stage": "validation", "items": items},
                    f,
                    indent=2,
                    ensure_ascii=False,
                )
            print(f"  ⚠️  Saved failed JSON → {fail_json}")
            failed.append(form_name)
            continue

        # Save only if valid
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2, ensure_ascii=False)
        print(f"  💾 Saved validated JSON → {out_json}")

    if failed:
        print("\n❗Processing completed with errors.\nFailed forms:")
        for name in failed:
            print(f" - {name}")
    else:
        print("\n✅ All forms processed successfully!")


# -------------------------------
# Entry point
# -------------------------------
if __name__ == "__main__":
    process_forms()
