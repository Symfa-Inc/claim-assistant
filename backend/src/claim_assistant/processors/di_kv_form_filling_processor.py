import logging
from pathlib import Path
from typing import Literal

from claim_assistant.schemas import Form, FormFieldAnswer
from claim_assistant.schemas.document_intelligence_response import (
    DocumentIntelligenceResponse,
)
from openai import OpenAI
from pydantic import BaseModel


class DIKVFormFillingProcessor:
    """
    Fill a Form from DI key/value extraction results using a single structured-output LLM call.

    - Input: list of DI KV pairs (key text, value text, confidence, bounding regions, etc.)
    - Output: Form where each field.answer.value is extracted and field.answer.evidence is populated
    """

    def __init__(
        self,
        model_client: OpenAI,
        logger: logging.Logger,
        model_name: Literal[
            "gpt-5-2025-08-07",
            "gpt-5-mini-2025-08-07",
            "gpt-5-nano-2025-08-07",
            "gpt-5.2-2025-12-11",
        ] = "gpt-5.2-2025-12-11",
    ) -> None:
        self.client = model_client
        self.logger = logger
        self.model_name = model_name

    def _load_form(self, form_json_path: str | Path) -> Form:
        """
        Load the form structure from a JSON definition file.
        """
        return Form.from_json(form_json_path)

    def _build_prompt(self, form: Form, di: DocumentIntelligenceResponse) -> str:
        # Keep the prompt explicit about evidence behavior: 0/1/many; many-to-many mapping allowed.
        questions = "\n".join(
            f"- [{f.order}] {f.text} ({f.data_type})"
            + (f" alias={f.alias}" if f.alias else "")
            + (
                f" format={f.meta.get('format')}"
                if (f.meta or {}).get("format")
                else ""
            )
            + (
                f" labels={f.meta.get('labels')}"
                if f.data_type == "enum" and (f.meta or {}).get("labels")
                else ""
            )
            for f in form.fields
        )
        kv_json = di.model_dump(mode="json")  # {"kv_pairs":[...]}
        return (
            "You are filling a claim form using Azure Document Intelligence (DI) key/value pairs.\n"
            "Your job is to produce the best possible answer VALUE for each field, using the DI pairs as evidence.\n\n"
            "Rules:\n"
            "1) For each form field, output an object with:\n"
            "   - value: the best answer (normalize formatting if useful, e.g. dates, phone numbers, splitting full name).\n"
            "   - evidence: a list of DI evidence objects that support this value.\n"
            "2) Evidence handling:\n"
            "   - evidence may be [], or contain 1 item, or multiple items.\n"
            "   - the same DI evidence item may be referenced by multiple fields.\n"
            "   - multiple DI items may be combined into one value (then include all of them).\n"
            "3) If you cannot answer a field, set value=null and evidence=[].\n"
            "4) Selection marks:\n"
            "   - if a DI pair indicates ':selected:' treat it as checked/true for the corresponding option.\n\n"
            "Form fields:\n"
            f"{questions}\n\n"
            "DI key/value pairs (JSON):\n"
            f"{kv_json}\n\n"
            "Return ONLY JSON that matches the provided response schema."
        )

    def _apply_parsed_to_form(self, form: Form, parsed: BaseModel) -> None:
        """
        parsed is an instance of the DynamicFormResponseModel.
        Each attribute is a per-field response model: {value, evidence}.
        """
        for i, field in enumerate(form.fields, start=1):
            key = f"{i}_{(field.alias or field.text.replace(' ', '_')).lower()}"
            ans: FormFieldAnswer | None = getattr(parsed, key, None)

            if ans is None:
                field.answer.value = None
                field.answer.evidences = []
                continue

            # ans is FormFieldAnswer (not dict) if you used the schema above
            field.answer.value = ans.value
            field.answer.evidences = ans.evidences

    def process(
        self,
        *,
        form_json_path: str | Path,
        di_payload: DocumentIntelligenceResponse,
    ) -> Form:
        """
        Fill a Form using DI KV extraction payload + one-shot structured-output parsing.

        Args:
            form_json_path: Path to form_model.json.
            di_payload: Output of DIKeyValueExtractionProcessor.process(input_pdf_path),
                        expected to be a DocumentIntelligenceResponse.

        Returns:
            Filled Form (values + evidence lists).
        """
        form = self._load_form(form_json_path)

        if not isinstance(di_payload, DocumentIntelligenceResponse):
            raise TypeError(
                f"di_payload must be DocumentIntelligenceResponse, got {type(di_payload)}",
            )

        if not di_payload.kv_pairs:
            self.logger.warning(
                "DI returned 0 key/value pairs; form will remain empty.",
            )
            for f in form.fields:
                f.answer.value = None
                f.answer.evidences = []
            return form

        response_schema = form.build_response_schema()
        prompt = self._build_prompt(
            form,
            di_payload,
        )  # _build_prompt expects the KV list

        try:
            parsed_response = self.client.responses.parse(
                model=self.model_name,
                input=[
                    {
                        "role": "user",
                        "content": [{"type": "input_text", "text": prompt}],
                    },
                ],
                text_format=response_schema,
            )

            parsed = parsed_response.output_parsed
            if parsed is None:
                raise ValueError("Structured output parsed to None")
            if not isinstance(parsed, BaseModel):
                raise TypeError(f"Unexpected parsed type: {type(parsed)}")

            self._apply_parsed_to_form(form, parsed)
            return form

        except Exception as e:
            self.logger.error(f"Failed to fill form from DI KV pairs: {e}")
            for f in form.fields:
                f.answer.value = None
                f.answer.evidences = []
            return form


if __name__ == "__main__":
    import logging
    import os

    from claim_assistant import PROJECT_DIR
    from claim_assistant.data.settings import OpenAISettings
    from claim_assistant.processors.di_key_value_extraction_processor import (
        DIKeyValueExtractionProcessor,
    )
    from claim_assistant.settings import AzureDocumentIntelligenceSettings
    from openai import OpenAI

    # -------------------------------------------------
    # Inputs
    # -------------------------------------------------
    input_pdf_path = os.path.join(
        PROJECT_DIR,
        "data",
        "forms",
        "FL",
        "form_hw_POL987654321.pdf",
    )
    form_json_path = os.path.join(
        PROJECT_DIR,
        "data",
        "forms",
        "FL",
        "form_model.json",
    )

    # -------------------------------------------------
    # Logger
    # -------------------------------------------------
    logger = logging.getLogger("DI_KV_PIPELINE_TEST")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        h = logging.StreamHandler()
        h.setLevel(logging.INFO)
        h.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"),
        )
        logger.addHandler(h)

    # -------------------------------------------------
    # Settings / Clients
    # -------------------------------------------------
    di_settings = AzureDocumentIntelligenceSettings()
    oa_settings = OpenAISettings()

    oa_client = OpenAI(api_key=oa_settings.openai_api_key)

    # -------------------------------------------------
    # 1) DI KV extraction
    # -------------------------------------------------
    kv_processor = DIKeyValueExtractionProcessor(
        api_key=di_settings.documentintelligence_api_key,
        endpoint=di_settings.documentintelligence_endpoint,
        logger=logger,
        # If your processor supports selecting model:
        # model_id="prebuilt-layout",
    )

    payload = kv_processor.process(input_pdf_path)

    kv_pairs = payload.kv_pairs or []
    # for i, kv in enumerate(kv_pairs[:200], start=1):  # limit spam
    #     k = (kv.get("key") or {}).get("content")
    #     v = (kv.get("value") or {}).get("content")
    #     c = kv.get("confidence") or (kv.get("value") or {}).get("confidence")
    #     logger.info(f"[KV {i:02d}] {k!r} -> {v!r} (conf={c})")

    # -------------------------------------------------
    # 2) LLM mapping DI KV -> Form answers (with evidence)
    # -------------------------------------------------
    form_processor = DIKVFormFillingProcessor(
        model_client=oa_client,
        logger=logger,
        model_name="gpt-5.2-2025-12-11",
    )

    form = form_processor.process(
        di_payload=payload,
        form_json_path=form_json_path,
    )

    # quick debug print
    for f in form.fields:
        value = f.answer.value if f.answer else None
        evid = f.answer.evidences if (f.answer and f.answer.evidences) else []

        # choose a scalar for logging (max confidence is usually the most useful)
        conf = max((e.confidence or 0.0) for e in evid) if evid else None
        regions = sum(1 for e in evid if e.bounding_region is not None)

        logger.info(
            f"[{f.order}] {f.text} -> {value!r} (conf={conf}, regions={regions}, evidences={len(evid)})",
        )
