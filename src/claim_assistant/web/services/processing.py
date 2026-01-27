from __future__ import annotations

import logging
import shutil
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from openai import OpenAI

from claim_assistant.processors.claim_validation_processor import (
    ClaimValidationProcessor,
)
from claim_assistant.processors.di_key_value_extraction_processor import (
    DIKeyValueExtractionProcessor,
)
from claim_assistant.processors.di_kv_form_filling_processor import (
    DIKVFormFillingProcessor,
)
from claim_assistant.processors.policy_database_processor import PolicyDatabaseProcessor
from claim_assistant.schemas.coverage_analysis_response import CoverageAnalysisResponse
from claim_assistant.schemas.form import Form
from claim_assistant.schemas.mock_policy_record import MockPolicyRecord
from claim_assistant.settings import (
    AzureDocumentIntelligenceSettings,
    OpenAISettings,
)

# If you already expose PROJECT_DIR somewhere central, prefer importing it.
# This mirrors what you used in main.py.
PROJECT_DIR = Path(__file__).resolve().parents[3]


@dataclass(frozen=True, slots=True)
class ProcessRequest:
    """
    API-layer request object.
    """

    form_type: str
    upload_pdf_path: Path


class ClaimProcessingService:
    """
    Orchestrates the pipeline (DI -> LLM form fill -> DB match -> validation).

    Differences vs CLI main():
      - does NOT generate a PDF report
      - policy DB path is hardcoded
      - creates a run dir and persists the uploaded PDF + run.log
      - returns CoverageAnalysisResponse
    """

    def __init__(self, project_dir: Path | None = None) -> None:
        self.project_dir = (project_dir or PROJECT_DIR).resolve()

        # Hardcoded DB path (per your requirement)
        self.policy_db_path = (
            self.project_dir / "data" / "policies" / "policies.json"
        ).resolve()

    # ---------------------------
    # Public API
    # ---------------------------
    def process(self, req: ProcessRequest) -> CoverageAnalysisResponse:
        start_time = time.time()

        run_dir = self._make_run_dir()
        logger = self._build_run_logger(run_dir)

        logger.info("Run dir: %s", run_dir)

        # Persist uploaded PDF into the run dir (so it is traceable/debuggable)
        input_pdf_path = self._persist_upload(req.upload_pdf_path, run_dir, logger)

        # Resolve form model
        form_json_path = self._resolve_form_json(req.form_type)
        logger.info("Resolved form_json_path: %s", form_json_path)

        # --- Initialize settings / clients ---
        openai_settings = OpenAISettings()
        client = OpenAI(api_key=openai_settings.openai_api_key)

        di_settings = AzureDocumentIntelligenceSettings()

        # --- Initialize processors ---
        di_kv_processor = DIKeyValueExtractionProcessor(
            api_key=di_settings.documentintelligence_api_key,
            endpoint=di_settings.documentintelligence_endpoint,
            logger=logger,
        )
        form_processor = DIKVFormFillingProcessor(model_client=client, logger=logger)
        db_processor = PolicyDatabaseProcessor(self.policy_db_path, logger)
        validation_processor = ClaimValidationProcessor(client, logger)

        # --- Workflow ---
        logger.info("Step 1: Extracting DI key/value pairs from PDF...")
        di_payload = di_kv_processor.process(input_pdf_path)
        logger.info("Step 2: Filling form fields from DI KV pairs via LLM...")
        form: Form = form_processor.process(
            form_json_path=form_json_path,
            di_payload=di_payload,
        )

        logger.info("Step 3: Fetching policy from database...")
        policy: MockPolicyRecord | None = db_processor.process(form)

        logger.info("Step 4: Validating claim against policy record...")
        analysis: CoverageAnalysisResponse = validation_processor.process(form, policy)

        elapsed = time.time() - start_time
        logger.info("Claim processing completed in %.1f seconds", elapsed)

        return analysis

    def to_debug_dict(self, req: ProcessRequest) -> dict:
        return {
            "form_type": req.form_type,
            "upload_pdf_path": str(req.upload_pdf_path),
            "policy_db_path": str(self.policy_db_path),
            "project_dir": str(self.project_dir),
        }

    # ---------------------------
    # Internals
    # ---------------------------
    def _make_run_dir(self) -> Path:
        run_dir = (
            self.project_dir
            / "data"
            / "runs"
            / datetime.now().strftime("%Y%m%d_%H%M%S")
        )
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    @staticmethod
    def _build_run_logger(run_dir: Path) -> logging.Logger:
        """
        Builds a per-run logger (console + run_dir/run.log), isolated from global logger.
        """
        logger = logging.getLogger(f"claim_pipeline.{run_dir.name}")
        logger.setLevel(logging.INFO)

        # Avoid duplicating handlers if the same run name is reused (rare but possible).
        if logger.handlers:
            return logger

        fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(fmt)

        log_path = run_dir / "run.log"
        file_handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(fmt)

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

        logging.getLogger("httpx").setLevel(logging.WARNING)
        return logger

    @staticmethod
    def _persist_upload(
        upload_pdf_path: Path,
        run_dir: Path,
        logger: logging.Logger,
    ) -> Path:
        """
        Copies the uploaded PDF into the run dir and returns the persisted path.
        """
        src = Path(upload_pdf_path)
        if not src.exists() or not src.is_file():
            raise ValueError(f"Uploaded file does not exist: {src}")

        # Keep original filename for traceability.
        dst = run_dir / src.name
        shutil.copyfile(src, dst)

        logger.info("Saved upload: %s", dst)
        return dst

    def _resolve_form_json(self, form_type: str) -> Path:
        """
        Resolve form model path from form_type.

        Convention:
          <project_dir>/data/forms/<form_type>/form_model.json

        If form_type is already a path (absolute or relative) and points to a JSON file,
        it will be used as-is.
        """
        ft = (form_type or "").strip()
        if not ft:
            raise ValueError("form_type is required")

        # Allow passing a direct path (useful for debugging).
        as_path = Path(ft)
        if as_path.suffix.lower() == ".json":
            candidate = (
                as_path if as_path.is_absolute() else (self.project_dir / as_path)
            )
            candidate = candidate.resolve()
            if candidate.exists() and candidate.is_file():
                return candidate

        # Default convention
        candidate = (
            self.project_dir / "data" / "forms" / ft / "form_model.json"
        ).resolve()
        if not candidate.exists() or not candidate.is_file():
            raise ValueError(
                f"Unknown form_type '{ft}': form model not found at {candidate}",
            )
        return candidate
