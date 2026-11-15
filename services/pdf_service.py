# services/pdf_service.py
import io
import logging
from pypdf import PdfReader

logger = logging.getLogger("PDFService")

def extract_text_from_pdf(pdf_input) -> str:
    logger.info("Starting PDF text extraction...")
    if isinstance(pdf_input, bytes):
        pdf_file = io.BytesIO(pdf_input)
    else:
        pdf_file = pdf_input

    reader = PdfReader(pdf_file)
    page_count = len(reader.pages)
    logger.info(f"PDF parsed | Total pages: {page_count}")

    extracted_text = []
    for idx, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        extracted_text.append(text)
        logger.debug(f"Page {idx+1}/{page_count}: Extracted {len(text)} chars")

    combined = "\n".join(extracted_text).strip()
    logger.info(f"Extraction complete | Total extracted length: {len(combined)} characters")
    return combined