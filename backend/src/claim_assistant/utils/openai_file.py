import logging
from contextlib import contextmanager
from pathlib import Path

from openai import OpenAI


@contextmanager
def openai_file(client: OpenAI, pdf_path: Path, logger: logging.Logger):
    """
    Context manager that uploads a file to OpenAI and ensures cleanup
    even if processing fails.

    Yields:
        str: The uploaded file's ID for downstream use.
    """
    file_id = None
    try:
        logger.info(f"Uploading {pdf_path.name} to OpenAI...")
        with open(pdf_path, "rb") as f:
            uploaded = client.files.create(file=f, purpose="user_data")
        file_id = uploaded.id
        logger.info(f"File uploaded successfully (id={file_id}).")
        yield file_id
    except Exception as e:
        logger.error(f"Upload or processing error: {e}")
        raise
    finally:
        if file_id:
            try:
                client.files.delete(file_id)
                logger.info(f"Cleaned up uploaded file {file_id} from OpenAI storage.")
            except Exception as cleanup_error:
                logger.warning(f"Failed to delete file {file_id}: {cleanup_error}")
