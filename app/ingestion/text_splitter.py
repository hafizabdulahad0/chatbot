import re
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class TextSplitter:
    """
    Runtime text chunker for long strings.
    """

    def __init__(self, chunk_size: int=500, overlap: int=100):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if overlap < 0:
            raise ValueError("overlap must be non-negative")
        if overlap >= chunk_size:
            raise ValueError("overlap must be less than chunk_size")
            
        self.chunk_size = chunk_size
        self.overlap = overlap

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text before splitting."""
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?-]', '', text)
        return text.strip()

    def split(self, text: str) -> list[dict]:
        """
        Split input text into overlapping chunks of words.
        """
        if not text:
            logger.warning("Empty text provided to splitter")
            return []

        # Clean and normalize text
        text = self._clean_text(text)
        if not text:
            logger.warning("Text is empty after cleaning")
            return []

        tokens = text.split()
        chunks = []
        start, idx = 0, 0
        while start < len(tokens):
            end = start + self.chunk_size
            chunk_tokens = tokens[start:end]
            chunks.append({
                "chunk_text": " ".join(chunk_tokens),
                "start_index": start,
                "end_index": min(end, len(tokens)),
                "chunk_index": idx
            })
            start += self.chunk_size - self.overlap
            idx += 1

        logger.info(f"Split text into {len(chunks)} chunks")
        return chunks 