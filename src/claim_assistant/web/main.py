import json
import traceback
from multiprocessing import get_context
from pathlib import Path
from typing import Annotated

import anyio
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from claim_assistant.web.deps import (
    get_logger,
    get_processing_service,
    get_project_dir,
    get_registry,
)
from claim_assistant.web.services.processing import ProcessRequest


def _run_processing(
    form_type: str,
    upload_pdf_path: str,
    send_conn,
) -> None:
    try:
        svc = get_processing_service()
        req = ProcessRequest(form_type=form_type, upload_pdf_path=Path(upload_pdf_path))
        result = svc.process(req)
        send_conn.send({"ok": True, "result": result.model_dump()})
    except Exception as exc:
        send_conn.send(
            {
                "ok": False,
                "error": str(exc),
                "traceback": traceback.format_exc(),
            },
        )
    finally:
        try:
            send_conn.close()
        except Exception:
            pass


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
    request: Request,
    file: Annotated[UploadFile, File()],
    form_id: Annotated[str, Form()],
    svc=Depends(get_processing_service),
    logger=Depends(get_logger),
):
    """
    Accepts a PDF upload + form_type.
    Returns CoverageAnalysisResponse (JSON).
    """
    if form_id == "generic":
        form_type = "generic"
    else:
        sample = get_registry().get_sample(form_id)
        if sample is None:
            raise HTTPException(status_code=404, detail="Sample not found")
        form_type = sample.form_code

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

        req = ProcessRequest(form_type=form_type, upload_pdf_path=tmp_path)
        logger.info(
            "Process request: %s",
            json.dumps(svc.to_debug_dict(req), ensure_ascii=False),
        )

        ctx = get_context("spawn")
        recv_conn, send_conn = ctx.Pipe(duplex=False)
        process = ctx.Process(
            target=_run_processing,
            args=(form_type, str(tmp_path), send_conn),
        )
        process.start()
        send_conn.close()

        while True:
            if await request.is_disconnected():
                if process.is_alive():
                    process.terminate()
                process.join(timeout=1)
                raise HTTPException(status_code=499, detail="Client closed request")

            if recv_conn.poll(0):
                message = recv_conn.recv()
                if message.get("ok"):
                    return message.get("result")
                logger.error("Processing failed: %s", message.get("error"))
                logger.debug("Processing traceback: %s", message.get("traceback"))
                raise HTTPException(
                    status_code=500,
                    detail="Internal processing error",
                )

            await anyio.sleep(0.1)

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve)) from ve
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Processing failed")
        raise HTTPException(
            status_code=500,
            detail="Internal processing error",
        ) from e
    finally:
        try:
            if "process" in locals() and process.is_alive():
                process.terminate()
                process.join(timeout=1)
        except Exception:
            pass
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except Exception:
            pass
