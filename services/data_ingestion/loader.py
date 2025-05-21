# services/data_ingestion/loader.py

from pathlib import Path
import json
from pydantic import BaseModel, ValidationError
from typing import List, Any, Optional

# Pydantic models for schema validation
class Chunk(BaseModel):
    id: str
    text: str
    metadata: dict

class Document(BaseModel):
    page_id: str
    url: Optional[str]
    metadata: dict
    sections: List[Any]
    chunks: List[Chunk]

class Loader:
    """
    Validate each structured JSON against the Document schema.
    """

    def __init__(self, processed_dir: Path):
        self.processed_dir = processed_dir

    def validate_all(self):
        """
        For each *_structured.json:
        1. Load JSON.
        2. Attempt Document(**data).
        3. Raise if any validation errors.
        """
        for file in self.processed_dir.glob("*_structured.json"):
            data = json.loads(file.read_text(encoding='utf-8'))
            try:
                Document(**data)
            except ValidationError as e:
                print(f"Validation error in {file.name}:\n{e}")
                raise
        print("✅ All documents validated successfully.")
