from pathlib import Path
import json

class Transformer:
    """
    Split each section in structured JSON into smaller
    token-based chunks, adding a `chunks` array to each file.
    """

    def __init__(self, processed_dir: Path, chunk_size: int = 500, overlap: int = 100):
        self.processed_dir = processed_dir
        self.chunk_size   = chunk_size
        self.overlap      = overlap

    def transform_all(self):
        for file in self.processed_dir.glob("*_structured.json"):
            doc = json.loads(file.read_text(encoding="utf-8"))
            page_id = doc.get("page_id", file.stem.replace("_structured", ""))

            # 1) Normalize sections → list of (header, content)
            raw_secs = doc.get("sections", {})
            sec_pairs = []
            if isinstance(raw_secs, dict):
                for header, content in raw_secs.items():
                    sec_pairs.append((header, content))
            elif isinstance(raw_secs, list):
                for sec in raw_secs:
                    sec_pairs.append((sec.get("header"), sec.get("content")))

            # 2) Flatten each section into text
            flat_sections = []
            for header, content in sec_pairs:
                if isinstance(content, str):
                    flat_sections.append((header, content.strip()))

                elif isinstance(content, list) and all(isinstance(i, str) for i in content):
                    flat_sections.append((header, " ".join(content).strip()))

                elif isinstance(content, list) and all(isinstance(i, dict) for i in content):
                    # FAQ style
                    for idx, faq in enumerate(content):
                        q = faq.get("question", "").strip()
                        a = faq.get("answer",   "").strip()
                        text = f"Q: {q}\nA: {a}"
                        flat_sections.append((f"{header}_faq_{idx}", text))

                elif isinstance(content, dict):
                    # nested dict (itinerary etc)
                    for subkey, sub in content.items():
                        if isinstance(sub, str):
                            text = sub.strip()
                        elif isinstance(sub, list) and all(isinstance(i, str) for i in sub):
                            text = " ".join(sub).strip()
                        else:
                            continue
                        flat_sections.append((f"{header}_{subkey}", text))

                else:
                    # skip numeric or None
                    continue

            # 3) Chunk each flattened section
            chunks = []
            for header, text in flat_sections:
                tokens = text.split()
                start, idx = 0, 0
                while start < len(tokens):
                    window = tokens[start : start + self.chunk_size]
                    chunk_text = " ".join(window)
                    chunk_id   = f"{page_id}__{header}__{idx}"
                    chunks.append({
                        "id": chunk_id,
                        "text": chunk_text,
                        "metadata": {
                            "page_id": page_id,
                            "section": header,
                            "chunk_index": idx
                        }
                    })
                    start += self.chunk_size - self.overlap
                    idx   += 1

            # 4) Attach & overwrite
            doc["chunks"] = chunks
            file.write_text(
                json.dumps(doc, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
