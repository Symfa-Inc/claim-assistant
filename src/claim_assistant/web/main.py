import json
from typing import Annotated

from fastapi import File, Form, UploadFile, HTTPException
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from claim_assistant.web.deps import (
    get_logger,
    get_processing_service,
    get_project_dir,
    get_registry,
)
from claim_assistant.web.services.processing import ProcessRequest


app = FastAPI(debug=True)

origins = [
    "http://localhost:3000",
    # "https://tech-analytics.d10.aisnovations.com",
    # Add more origins here
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PROJECT_DIR = get_project_dir()


@app.post("/process")
async def process_form(
    file: Annotated[UploadFile, File()],
    form_id: Annotated[str, Form()],
    svc=Depends(get_processing_service),
    logger=Depends(get_logger),
):
    """
    Accepts a PDF upload + form_type.
    Returns CoverageAnalysisResponse (JSON).
    """
    sample = get_registry().get_sample(form_id)
    if sample is None:
        raise HTTPException(status_code=404, detail="Sample not found")


    if file.content_type not in (None, "", "application/pdf"):
        raise HTTPException(
            status_code=415,
            detail="Only application/pdf is supported.",
        )

    # Store upload to a temp path (under project_dir/.tmp_uploads)
    uploads_dir = Path(PROJECT_DIR) / ".tmp_uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    tmp_path = uploads_dir / file.filename

    try:
        content = await file.read()
        tmp_path.write_bytes(content)

        req = ProcessRequest(form_type=sample.form_code, upload_pdf_path=tmp_path)
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