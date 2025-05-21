# services/data_ingestion/transformer.py

from pathlib import Path
import json

class Transformer:
    """
    Split each section in structured JSON into smaller
    token-based chunks, adding 'chunks' to the JSON.
    """

    def __init__(self, processed_dir: Path, chunk_size: int = 500, overlap: int = 100):
        """
        processed_dir: Path to folder containing *_structured.json files
        chunk_size: max number of tokens per chunk
        overlap: number of tokens to overlap between chunks
        """
        self.processed_dir = processed_dir
        self.chunk_size = chunk_size
        self.overlap = overlap

    def transform_all(self):
        """
        For each *_structured.json:
        1. Read the sections.
        2. For each section, join list→str if needed.
        3. Tokenize by whitespace, then slice into
           chunk_size windows with overlap.
        4. Create a chunk record:
           { id, text, metadata: { page_id, header, chunk_index } }
        5. Append all chunks into doc["chunks"] and overwrite.
        """
        for file in self.processed_dir.glob("*_structured.json"):
            doc = json.loads(file.read_text(encoding='utf-8'))
            chunks = []

            for sec in doc.get("sections", []):
                text = sec["content"]
                if isinstance(text, list):
                    text = " ".join(text)

                tokens = text.split()
                start, idx = 0, 0
                # Slide a window over tokens
                while start < len(tokens):
                    chunk_tokens = tokens[start:start + self.chunk_size]
                    chunk_text = " ".join(chunk_tokens)
                    chunk_id = f"{doc['page_id']}_{sec['header']}_{idx}"

                    chunks.append({
                        "id": chunk_id,
                        "text": chunk_text,
                        "metadata": {
                            "page_id": doc["page_id"],
                            "header": sec["header"],
                            "chunk_index": idx
                        }
                    })
                    # Move window forward by chunk_size - overlap
                    start += self.chunk_size - self.overlap
                    idx += 1

            # Attach chunks and overwrite file
            doc["chunks"] = chunks
            file.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding='utf-8')
