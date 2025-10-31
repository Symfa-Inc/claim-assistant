import json
import logging
import os.path
from pathlib import Path
from typing import Dict, Any, List

from openai import OpenAI

from claim_assistant import PROJECT_DIR
from claim_assistant.data.settings import OpenAISettings
from claim_assistant.models.form import Form


def process_form_from_json(client, model_name: str, form: "Form", answers_raw: str, logger=None) -> "Form":
    """
    Feed prepared JSON answers to the LLM and return the Form with updated answers.

    Args:
        client: OpenAI client or compatible API client.
        model_name: Name of the LLM model to use.
        form: Form object containing multiple FormField definitions.
        answers_raw: JSON dictionary with pre-filled answers.
        logger: Optional logger.

    Returns:
        Form with field.answer values updated by the LLM.
    """
    if logger:
        logger.info(f"Normalizing answers for form with {len(form.fields)} fields...")

    response_schema = form.build_response_schema()

    parsed_response = client.responses.parse(
        model=model_name,
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            "You are given pre-filled answers for a form in JSON format.\n"
                            "Each entry includes 'order', 'text', and 'answer'.\n"
                            "Your task is to normalize the structure ONLY — do not modify, correct, "
                            "or reinterpret any of the actual answer values.\n"
                            "Preserve every answer exactly as provided.\n\n"
                            f"Form content:\n{answers_raw}\n\n"
                            "Return a structured JSON matching the provided schema, with identical 'answer' values "
                            "and consistent field names."
                        ),
                    },
                ],
            },
        ],
        text_format=response_schema,
    )

    result_dict = parsed_response.output_parsed.model_dump()

    # Update the form's fields directly
    for field in form.fields:
        key = f"{field.order}_{(field.alias or field.text.replace(' ', '_')).lower()}"
        value = result_dict.get(key)
        if isinstance(value, dict) and "answer" in value:
            value = value["answer"]
        field.answer = value

    return form


if __name__=="__main__":
    base_dir = Path(PROJECT_DIR) / "data" / "amtrust"
    model_name = "gpt-5-mini-2025-08-07"
    logger = logging.getLogger("answers_fixer")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    openai_client = OpenAI(api_key=OpenAISettings().openai_api_key)


    for form_dir in base_dir.iterdir():
        if not form_dir.is_dir():
            continue

        model_path = form_dir / "form_model.json"
        if not model_path.exists():
            logger.warning(f"Skipping {form_dir.name}: no form_model.json found.")
            continue

        logger.info(f"Processing form type: {form_dir.name}")

        # Load form model
        form = Form.from_json(model_path)

        answer_files = [
            form_dir / f"answers_POL123456789.json",
            form_dir / f"answers_POL987654321.json",
            form_dir / f"answers_SIC123456789.json",
            ]

        # Iterate through answer files
        for answers_file in answer_files:
            # Skip already structured answers
            output_path = answers_file.with_name(
                answers_file.stem.replace("answers_", "answers_structured_") + ".json"
            )
            # Skip if the structured version already exists
            if output_path.exists():
                logger.info(f"Skipping {answers_file.name}: structured file already exists.")
                continue


            with open(answers_file, "r", encoding="utf-8") as f:
                answers_raw = f.read()

            logger.info(f"Sending {answers_file.name} for normalization...")

            # Run normalization
            normalized_form = process_form_from_json(
                client=openai_client,
                model_name=model_name,
                form=form,
                answers_raw=answers_raw,
                logger=logger,
            )

            # Extract fields
            structured_output = [
                {"order": f.order, "text": f.text, "answer": f.answer}
                for f in normalized_form.fields
            ]

            # Save normalized JSON
            output_path = answers_file.with_name(
                answers_file.stem.replace("answers_", "answers_structured_") + ".json"
            )
            with open(output_path, "w") as out:
                json.dump(structured_output, out, indent=2)

            logger.info(f"Saved: {output_path}")