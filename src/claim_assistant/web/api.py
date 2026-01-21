from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, File
from fastapi import Form as FormField
from fastapi import HTTPException, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from claim_assistant.schemas.coverage_analysis_response import CoverageAnalysisResponse
from claim_assistant.web.deps import (
    get_logger,
    get_processing_service,
    get_project_dir,
    get_registry,
)
from claim_assistant.web.services.processing import ProcessRequest


def create_app() -> FastAPI:
    app = FastAPI(title="Claim Assistant API")

    project_dir = get_project_dir()
    static_dir = project_dir / "src" / "claim_assistant" / "web" / "static"

    # Serve built SPA (React dist copied here)
    if static_dir.exists():
        app.mount(
            "/",
            StaticFiles(directory=str(static_dir), html=True),
            name="spa",
        )

    # ----------------------------
    # API routes
    # ----------------------------
    @app.get("/api/registry", response_class=JSONResponse)
    def registry_snapshot(
        registry=Depends(get_registry),
    ) -> dict[str, Any]:
        """
        Data needed by the SPA homepage:
          - available form types (form_model.json present)
          - available sample PDFs (optional convenience)
        """
        snap = registry.snapshot()
        return snap.to_dict()

    @app.post("/api/process", response_model=CoverageAnalysisResponse)
    async def process_claim(
        form_type: str = FormField(...),
        file: UploadFile = File(...),
        svc=Depends(get_processing_service),
        logger=Depends(get_logger),
    ) -> CoverageAnalysisResponse:
        """
        Accepts a PDF upload + form_type.
        Returns CoverageAnalysisResponse (JSON).
        """
        if file.content_type not in (None, "", "application/pdf"):
            raise HTTPException(
                status_code=415,
                detail="Only application/pdf is supported.",
            )

        # Store upload to a temp path (under project_dir/.tmp_uploads)
        uploads_dir = Path(project_dir) / ".tmp_uploads"
        uploads_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = uploads_dir / file.filename

        try:
            content = await file.read()
            tmp_path.write_bytes(content)

            req = ProcessRequest(form_type=form_type, upload_pdf_path=tmp_path)
            logger.info(
                "Process request: %s",
                json.dumps(svc.to_debug_dict(req), ensure_ascii=False),
            )

            return svc.process(req)

        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve)) from ve
        except Exception as e:
            logger.exception("Processing failed")
            raise HTTPException(
                status_code=500,
                detail="Internal processing error",
            ) from e
        finally:
            # keep file for debugging if you want; otherwise delete
            try:
                if tmp_path.exists():
                    tmp_path.unlink()
            except Exception:
                pass

    # Fallback: when static is missing, expose a minimal homepage.
    @app.get("/")
    def root_fallback(logger=Depends(get_logger)) -> JSONResponse:
        if static_dir.exists():
            # StaticFiles(html=True) already handles "/"
            return JSONResponse({"ok": True})
        logger.warning("SPA static directory not found: %s", static_dir)
        return JSONResponse(
            {
                "message": "SPA not built/copied yet.",
                "hint": "Copy React build output into src/claim_assistant/web/static/",
                "registry": "/api/registry",
                "process": "/api/process",
            },
        )

    return app
