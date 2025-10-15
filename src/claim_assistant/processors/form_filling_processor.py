import logging
from pathlib import Path
from typing import Literal

from openai import OpenAI

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
        ] = "gpt-5-nano-2025-08-07",
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
                text_format=field.build_answer_schema(),
            )

            result = parsed_response.output_parsed
            field.answer = result.answer
            self.logger.info(f"Extracted: {field.answer}")

        except Exception as e:
            self.logger.error(f"Failed to extract field '{field.text}': {e}")
            field.answer = None

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
            for field in form.fields:
                self._process_field(field, file_id)

        self.logger.info("Form processing completed.")
        return form
