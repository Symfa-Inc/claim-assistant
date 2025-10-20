import logging
import os
from pathlib import Path
from typing import Literal

from openai import OpenAI

from claim_assistant import PROJECT_DIR
from claim_assistant.models.form import Form
from claim_assistant.models.form_field import FormField
from claim_assistant.utils import openai_file, validate_pdf


class FormFillingProcessor:
    """
    Responsible for populating a Form instance with data extracted
    from a file, PDF, or raw text input.

    This class separates orchestration logic (I/O, model calls, extraction)
    from the Form data model itself, following SOLID principles.
    """

    def __init__(
        self,
        model_client: OpenAI,
        logger: logging.Logger,
        model_name: Literal[
            "gpt-5-2025-08-07",
            "gpt-5-mini-2025-08-07",
            "gpt-5-nano-2025-08-07",
        ] = "gpt-5-2025-08-07",
    ) -> None:
        """
        Args:
            model_client: OpenAI (or compatible) client used for inference.
            logger: logging.Logger Python logger instance for structured logging.
            model_name: Model identifier to use for structured extraction.
                        Must be one of:
                        - gpt-5-2025-08-07
                        - gpt-5-mini-2025-08-07
                        - gpt-5-nano-2025-08-07
        """
        if model_name not in {
            "gpt-5-2025-08-07",
            "gpt-5-mini-2025-08-07",
            "gpt-5-nano-2025-08-07",
        }:
            raise ValueError(
                f"Invalid model '{model_name}'. Must be one of: GPT-5 models.",
            )
        self.client = model_client
        self.model_name = model_name
        self.logger = logger

    def _load_form(self, form_json_path: str | Path) -> Form:
        """
        Load the form structure from a JSON definition file.
        """
        return Form.from_json(form_json_path)

    def _process_field(self, field: FormField, file_id: str) -> None:
        """
        Process a single FormField using structured output parsing.

        Args:
            field: FormField object to fill.
            file_id: ID of the uploaded PDF file for model reference.
        """
        self.logger.info(f"Extracting field №{field.order}: {field.text}")

        # The response schema can be defined dynamically from the field
        # For now we keep a stub using structured output (client.responses.parse)
        try:
            parsed_response = self.client.responses.parse(
                model=self.model_name,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": (
                                    f"You are reading a filled insurance claim form PDF. "
                                    f"Find the answer for this field:\n\n"
                                    f"Question: {field.text}\n"
                                    f"Description: {field.description or 'N/A'}\n\n"
                                    "Return only the extracted value, validated "
                                    "according to the field type and expected format."
                                ),
                            },
                            {"type": "input_file", "file_id": file_id},
                        ],
                    },
                ],
                text_format=field.build_response_schema(),
            )

            result = parsed_response.output_parsed
            field.answer = result.answer
            self.logger.info(f"Extracted: {field.answer}")

        except Exception as e:
            self.logger.error(f"Failed to extract field '{field.text}': {e}")
            field.answer = None

    def _process_fields(self, form: Form, file_id: str) -> None:
        """
        Process all FormFields in a single structured-output LLM request.

        Args:
            form: Form object containing multiple FormField definitions.
            file_id: ID of the uploaded PDF file for model reference.
        """
        self.logger.info(
            f"Extracting {len(form.fields)} fields from PDF in a single request...",
        )
        try:
            # Build combined structured schema
            response_schema = form.build_response_schema()

            # Prepare compact textual summary
            questions_text = "\n".join(
                f"{f.order}. {f.text} ({f.data_type})" for f in form.fields
            )

            # Call OpenAI structured response API
            parsed_response = self.client.responses.parse(
                model=self.model_name,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": (
                                    "You are reading a filled insurance claim form PDF.\n"
                                    "Extract all answers for the following fields.\n\n"
                                    f"Questions:\n{questions_text}\n\n"
                                    "Return a structured JSON with one key per field, "
                                    "matching the names and order of the provided list."
                                ),
                            },
                            {"type": "input_file", "file_id": file_id},
                        ],
                    },
                ],
                text_format=response_schema,
            )

            result_dict = parsed_response.output_parsed.model_dump()

            for field in form.fields:
                key = f"{field.order}_{(field.alias or field.text.replace(' ', '_')).lower()}"
                value = result_dict.get(key)

                # flatten nested dicts that come from structured parsing
                if isinstance(value, dict) and "answer" in value:
                    value = value["answer"]

                field.answer = value
                self.logger.info(
                    f"Extracted field {field.order}: {field.text} → {value}",
                )

        except Exception as e:
            self.logger.error(f"Failed to extract multiple fields: {e}")
            for f in form.fields:
                f.answer = None

    @staticmethod
    def _postprocess_policy_id(policy_id: str | None) -> str | None:
        """
        Post-process the extracted policy ID to ensure correct formatting.
        """
        if policy_id is None:
            return None

        processed_id = (
            policy_id.replace(" ", "").replace("-", "").replace("/", "").upper()
        )
        return processed_id

    def process(
        self,
        input_source: str | Path,
        form_json_path: str | Path,
    ) -> Form:
        """
        Process a PDF claim form and populate a Form instance.
        """
        self.logger.info("Loading form definition...")
        form = self._load_form(form_json_path)

        self.logger.info("Validating and uploading PDF...")
        pdf_path = validate_pdf(input_source)

        with openai_file(self.client, pdf_path, self.logger) as file_id:
            self.logger.info("Starting field extraction...")
            self._process_fields(form, file_id)
            # for field in form.fields:
            #     self._process_field(field, file_id)

        form.policy_id.answer = FormFillingProcessor._postprocess_policy_id(
            form.policy_id.answer,
        )

        self.logger.info("Form processing completed.")
        return form


if __name__ == "__main__":
    input_pdf_path = os.path.join(
        PROJECT_DIR,
        "data",
        "deprecated",
        "dwc",
        "form_filled_flat.pdf",
    )
    form_json_path = os.path.join(
        PROJECT_DIR,
        "data",
        "forms",
        "TMP_DWC",
        "form_model.json",
    )

    logger = logging.getLogger("FormFillingProcessor")
    logger.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)

    processor = FormFillingProcessor(
        model_client=OpenAI(api_key="api_key"),
        logger=logger,
        model_name="gpt-5-nano-2025-08-07",
    )

    processor.process(input_pdf_path, form_json_path)
