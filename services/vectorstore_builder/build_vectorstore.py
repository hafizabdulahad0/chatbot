# services/vectorstore_builder/build_vectorstore.py

import os
import json
from pathlib import Path
from dotenv import load_dotenv

import openai
from chromadb import PersistentClient

# ─── Load API key & config ────────────────────────────────────────────────
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise RuntimeError("Please set OPENAI_API_KEY in your environment")

# ─── Helper to generate embeddings ─────────────────────────────────────────
def get_embedding(text: str) -> list[float]:
    """
    Generate an embedding for `text` using OpenAI v1 Embedding API.
    """
    resp = openai.Embedding.create(
        model="text-embedding-ada-002",
        input=text
    )
    # v1 response shape: { data: [ { embedding: [...] } ], ... }
    return resp.data[0].embedding

# ─── Main vectorstore builder ─────────────────────────────────────────────
def main():
    company = os.getenv("COMPANY_NAME", "my_company")
    # where to store / load your Chroma DB
    db_path = os.getenv(
        "VECTORSTORE_PATH",
        f"vectorstores/{company}/chroma.sqlite3"
    )

    # open (or create) the Chroma collection
    client     = PersistentClient(path=db_path)
    collection = client.get_or_create_collection(name="docs")

    # walk through all your chunked JSON files
    root           = Path(__file__).parent.parent.parent
    processed_dir  = root / "processed_data" / company

    if not processed_dir.exists():
        raise FileNotFoundError(f"{processed_dir} does not exist")

    for file in processed_dir.glob("*_structured.json"):
        doc = json.loads(file.read_text(encoding="utf-8"))
        # each file has a "chunks" list
        for chunk in doc.get("chunks", []):
            text = chunk["text"]
            emb  = get_embedding(text)

            # Add into Chroma
            collection.add(
                documents=[text],
                embeddings=[emb],
                metadatas=[{"page_id": chunk["metadata"]["page_id"]}],
                ids=[chunk["id"]],
            )

    print(f"✅ Vectorstore built at {db_path}")
