import os, json
from pathlib import Path
import openai
from chromadb import PersistentClient
from .config import PROCESSED_DIR, VECTORSTORE_DIR

# Load API key
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise RuntimeError("Please set OPENAI_API_KEY")

def get_embedding(text: str) -> list[float]:
    # Call OpenAI to get a vector for this text
    resp = openai.Embedding.create(model="text-embedding-ada-002", input=text)
    return resp["data"][0]["embedding"]

def main():
    # Ensure output directory exists
    VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)

    # Connect to (or create) the Chroma collection
    client = PersistentClient(path=str(VECTORSTORE_DIR / "chroma.sqlite3"))
    collection = client.get_or_create_collection(name="docs")

    # Iterate over all structured JSON docs
    for f in PROCESSED_DIR.glob("*_structured.json"):
        doc = json.loads(f.read_text(encoding="utf-8"))
        for chunk in doc.get("chunks", []):
            emb = get_embedding(chunk["text"])
            collection.upsert(
                ids=[chunk["id"]],
                embeddings=[emb],
                documents=[chunk["text"]],
                metadatas=[chunk["metadata"]],
            )

    print(f"✅ Vectorstore built at {VECTORSTORE_DIR / 'chroma.sqlite3'}")

if __name__ == "__main__":
    main()
