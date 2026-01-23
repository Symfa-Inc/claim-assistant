import logging
from pathlib import Path
from typing import Any, Literal

from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential


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

    def process(self, input_pdf_path: str | Path) -> dict[str, Any]:
        pdf_path = Path(input_pdf_path)
        if not pdf_path.exists() or not pdf_path.is_file():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        self.logger.info(f"DI KV extraction started (model_id={self.model_id})")

        with pdf_path.open("rb") as f:
            poller = self.client.begin_analyze_document(self.model_id, document=f)
        result = poller.result()

        kv_pairs_out: list[dict[str, Any]] = []
        kv_pairs = getattr(result, "key_value_pairs", None) or []
        self.logger.info(f"DI returned {len(kv_pairs)} key/value pairs")

        for kv in kv_pairs:
            key = getattr(kv, "key", None)
            value = getattr(kv, "value", None)

            key_text = getattr(key, "content", None) if key else None
            value_text = getattr(value, "content", None) if value else None

            # confidence is sometimes on kv, sometimes on key/value depending on SDK output
            confidence = getattr(kv, "confidence", None)
            if confidence is None and value is not None:
                confidence = getattr(value, "confidence", None)

            # bounding regions live on the element (key/value) typically
            def _regions(el) -> list[dict[str, Any]]:
                out: list[dict[str, Any]] = []
                if not el:
                    return out
                for br in getattr(el, "bounding_regions", None) or []:
                    out.append(
                        {
                            "page": int(getattr(br, "page_number", 0) or 0),
                            "polygon": [
                                float(p.x) if hasattr(p, "x") else float(p[0])
                                for p in (getattr(br, "polygon", None) or [])
                                for p in ([p] if hasattr(p, "x") else [p])
                            ],
                        },
                    )
                return out

            kv_pairs_out.append(
                {
                    "key": {
                        "content": key_text,
                        "bounding_regions": _regions(key),
                    },
                    "value": {
                        "content": value_text,
                        "bounding_regions": _regions(value),
                    },
                    "confidence": float(confidence) if confidence is not None else None,
                },
            )

        payload = {
            "source": "di_kv",
            "model_id": self.model_id,
            "input_file": str(pdf_path),
            "kv_pairs": kv_pairs_out,
        }

        self.logger.info(f"DI extracted {len(kv_pairs_out)} key/value pairs")
        return payload


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

    kv_pairs = payload.get("kv_pairs", [])

    for i, kv in enumerate(kv_pairs[:200], start=1):  # limit spam
        k = (kv.get("key") or {}).get("content")
        v = (kv.get("value") or {}).get("content")
        c = kv.get("confidence") or (kv.get("value") or {}).get("confidence")
        logger.info(f"[KV {i:02d}] {k!r} -> {v!r} (conf={c})")
