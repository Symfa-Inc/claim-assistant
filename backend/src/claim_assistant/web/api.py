from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from claim_assistant.schemas.coverage_analysis_response import CoverageAnalysisResponse
from claim_assistant.web.deps import (
    get_logger,
    get_processing_service,
    get_project_dir,
    get_registry,
)
from claim_assistant.web.services.processing import ProcessRequest
from fastapi import Depends, FastAPI, File
from fastapi import Form
from fastapi import Form as FormField
from fastapi import HTTPException, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse


def create_app() -> FastAPI:
    app = FastAPI(title="Claim Assistant API")

    project_dir = get_project_dir()
    static_dir = project_dir / "src" / "claim_assistant" / "web" / "static"

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

    @app.post("/api/process-sample", response_model=CoverageAnalysisResponse)
    def process_sample(
        sample_id: str = Form(...),
        svc=Depends(get_processing_service),
        logger=Depends(get_logger),
        registry=Depends(get_registry),
    ) -> CoverageAnalysisResponse:
        sample = registry.get_sample(sample_id)
        if sample is None:
            raise HTTPException(status_code=404, detail="Sample not found")

        req = ProcessRequest(
            form_type=sample.form_code,
            upload_pdf_path=Path(sample.path),
            # is_sample=True,
            # sample_id=sample.id,
        )
        logger.info(
            "Process sample request: %s",
            json.dumps(svc.to_debug_dict(req), ensure_ascii=False),
        )
        try:
            return svc.process(req)
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve)) from ve
        except Exception as e:
            logger.exception("Processing failed")
            raise HTTPException(
                status_code=500,
                detail="Internal processing error",
            ) from e

    # Serve built SPA (React dist copied here)
    if static_dir.exists():
        app.mount(
            "/assets",
            StaticFiles(directory=str(static_dir / "assets")),
            name="assets",
        )

        @app.get("/")
        def spa_index():
            return FileResponse(static_dir / "index.html")
    else:

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
