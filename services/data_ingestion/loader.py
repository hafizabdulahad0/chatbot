import json
from pathlib import Path
from typing import Any, Dict, List
from pydantic import BaseModel, ValidationError

class Section(BaseModel):
    header: str
    content: Any        # ← allow string, int, list, dict, etc.

class ChunkMetadata(BaseModel):
    page_id: str
    section: str
    chunk_index: int

class Chunk(BaseModel):
    id: str
    text: str
    metadata: ChunkMetadata

class Document(BaseModel):
    page_id: str
    page_title: str | None = None
    sections: List[Section]
    chunks: List[Chunk]

class Loader:
    def __init__(self, processed_dir: Path):
        self.processed_dir = processed_dir

    def validate_all(self):
        for file in self.processed_dir.glob("*_structured.json"):
            data = json.loads(file.read_text(encoding="utf-8"))

            # still allow dict-shaped sections
            secs = data.get("sections")
            if isinstance(secs, dict):
                data["sections"] = [
                    {"header": hdr, "content": content}
                    for hdr, content in secs.items()
                ]

            try:
                Document(**data)
            except ValidationError as e:
                print(f"Validation error in {file.name}:\n{e}")
                raise
        print("✅ All documents validated successfully.")
