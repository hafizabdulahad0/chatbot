from pathlib import Path
import PyPDF2
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class PDFLoader:
    """
    Runtime helper to read PDFs if needed on-the-fly.
    """

    def __init__(self, pdf_dir: Path):
        self.pdf_dir = pdf_dir
        if not pdf_dir.exists():
            raise ValueError(f"PDF directory does not exist: {pdf_dir}")

    def load_all(self) -> List[Dict[str, Any]]:
        """
        Extract text from each PDF page and return a list of
        { page_id, text, metadata } dicts.
        """
        docs = []
        for pdf_file in self.pdf_dir.glob("*.pdf"):
            try:
                logger.info(f"Processing PDF: {pdf_file}")
                reader = PyPDF2.PdfReader(str(pdf_file))
                text = ""
                for page_num, page in enumerate(reader.pages, 1):
                    try:
                        page_text = page.extract_text() or ""
                        text += page_text + "\n"
                    except Exception as e:
                        logger.warning(f"Error extracting text from page {page_num} in {pdf_file}: {e}")
                
                if not text.strip():
                    logger.warning(f"No text extracted from {pdf_file}")
                    continue
                    
                docs.append({
                    "page_id": pdf_file.stem,
                    "text": text.strip(),
                    "metadata": {
                        "source": str(pdf_file),
                        "total_pages": len(reader.pages)
                    }
                })
                logger.info(f"Successfully processed {pdf_file}")
            except Exception as e:
                logger.error(f"Error processing {pdf_file}: {e}")
                continue
                
        if not docs:
            logger.warning(f"No PDFs were successfully processed in {self.pdf_dir}")
            
        return docs 