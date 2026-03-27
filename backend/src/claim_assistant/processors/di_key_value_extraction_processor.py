import logging
from pathlib import Path
from typing import Literal

from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

from claim_assistant.schemas import DocumentIntelligenceResponse


class DIKeyValueExtractionProcessor:
    """
    Extract key/value pairs from a PDF using Azure Form Recognizer (Document Intelligence v3.x)
    prebuilt-document model.

    Note:
      - This processor does NOT map KVs into Form/FormField.
      - It returns raw KV payload (with confidence + bounding regions) for later LLM postprocessing.
    """

    def __init__(
        self,
        *,
        endpoint: str,
        api_key: str,
        logger: logging.Logger,
        model_id: Literal["prebuilt-document"] = "prebuilt-document",
    ) -> None:
        self.logger = logger
        self.model_id = model_id
        self.client = DocumentAnalysisClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(api_key),
        )

    def process(self, input_pdf_path: str | Path) -> DocumentIntelligenceResponse:
        pdf_path = Path(input_pdf_path)
        if not pdf_path.exists() or not pdf_path.is_file():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        self.logger.info(f"DI KV extraction started (model_id={self.model_id})")

        with pdf_path.open("rb") as f:
            poller = self.client.begin_analyze_document(self.model_id, document=f)
        result = poller.result()

        resp = DocumentIntelligenceResponse.from_analyze_result(result)

        self.logger.info("DI extracted %d key/value pairs", len(resp.kv_pairs))
        return resp


if __name__ == "__main__":
    import logging
    import os

    from claim_assistant import PROJECT_DIR
    from claim_assistant.settings import AzureDocumentIntelligenceSettings

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

    logger = logging.getLogger("DIKeyValueExtractionProcessor")
    logger.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)

    settings = AzureDocumentIntelligenceSettings()

    processor = DIKeyValueExtractionProcessor(
        api_key=settings.documentintelligence_api_key,
        endpoint=settings.documentintelligence_endpoint,
        logger=logger,
    )

    payload = processor.process(input_pdf_path)

    pairs = payload.kv_pairs or []

    for i, kv in enumerate(pairs[:5], start=1):  # limit spam
        key = kv.key
        val = kv.value
        conf = kv.confidence
        regions = kv.bounding_regions or []
        n_regions = len(regions)

        first_region = regions[0] if regions else None
        page = first_region.page if first_region else None
        poly = first_region.polygon if first_region else None
        poly_len = len(poly) if isinstance(poly, list) else None

        logger.info(
            f"[KV {i:02d}] {key!r} -> {val!r} (conf={conf}, regions={n_regions}, "
            f"page={page}, poly_len={poly_len})",
        )
