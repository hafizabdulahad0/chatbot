#!/usr/bin/env python3
"""
build_vectorstore.py

Loads .env → Reads processed JSON → Calls OpenAI v1 Embeddings API → Upserts to Chroma.
"""

import os, json
from pathlib import Path
from dotenv import load_dotenv

# 1) Load .env so OPENAI_API_KEY is available
load_dotenv()

import openai
from chromadb import PersistentClient
from .config import PROCESSED_DIR, VECTORSTORE_DIR

def get_embedding(text: str) -> list[float]:
    """
    Use the new v1 embeddings endpoint and return the embedding vector.
    """
    # Call the v1 Embeddings API
    resp = openai.embeddings.create(
        model="text-embedding-ada-002",
        input=text
    )
    # resp.data is a list of objects; .embedding holds the vector
    return resp.data[0].embedding

def main():
    """
    1. Read API key from environment (after load_dotenv above).
    2. Walk through PROCESSED_DIR, embed each chunk.
    3. Upsert into Chroma at VECTORSTORE_DIR/chroma.sqlite3.
    """
    # 2) Ensure the API key is set
    openai.api_key = os.getenv("OPENAI_API_KEY")
    if not openai.api_key:
        raise RuntimeError("Please set OPENAI_API_KEY in your .env or environment")

    # 3) Prepare output directory
    VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)

    # 4) Connect to (or create) the Chroma collection
    client = PersistentClient(path=str(VECTORSTORE_DIR / "chroma.sqlite3"))
    collection = client.get_or_create_collection(name="docs")

    # 5) Iterate over each structured JSON file
    for file_path in PROCESSED_DIR.glob("*_structured.json"):
        doc = json.loads(file_path.read_text(encoding="utf-8"))
        for chunk in doc.get("chunks", []):
            # a) Generate embedding for this chunk
            vector = get_embedding(chunk["text"])
            # b) Upsert into ChromaDB
            collection.upsert(
                ids=[chunk["id"]],
                embeddings=[vector],
                documents=[chunk["text"]],
                metadatas=[chunk["metadata"]],
            )

    print(f"✅ Vectorstore built at {VECTORSTORE_DIR / 'chroma.sqlite3'}")

if __name__ == "__main__":
    main()
