from pathlib import Path
from typing import Union


def _validate_pdf(input_source: Union[str, Path]) -> Path:
    """
    Validate input source and ensure it is a PDF file.

    Returns:
        Path to the validated PDF file.
    Raises:
        ValueError if the file does not exist or is not a PDF.
    """
    pdf_path = Path(input_source)
    if not pdf_path.exists() or pdf_path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a PDF file, got: {pdf_path}")
    return pdf_path
