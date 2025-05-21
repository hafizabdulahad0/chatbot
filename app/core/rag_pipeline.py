# app/core/rag_pipeline.py

"""
RAG pipeline using OpenAI v1 Embeddings + ChatCompletion.
"""

import os
from dotenv import load_dotenv

# Load .env so API key and VECTORSTORE_PATH are available
load_dotenv()

import openai
from chromadb import PersistentClient
from app.core.llm_client import call_llm

# Path to your Chroma DB (from .env or fallback)
DB_PATH = os.getenv("VECTORSTORE_PATH", "vectorstores/my_company/chroma.sqlite3")

# Initialize Chroma client & collection once
client = PersistentClient(path=DB_PATH)
collection = client.get_or_create_collection(name="docs")

def get_query_embedding(text: str) -> list[float]:
    """
    Generate an embedding for the query via OpenAI v1 API.
    """
    resp = openai.embeddings.create(
        model="text-embedding-ada-002",
        input=text
    )
    return resp.data[0].embedding

def run_rag(query: str, top_k: int = 3) -> tuple[str, list[str]]:
    """
    1) Embed the user query.
    2) Retrieve top_k chunks from Chroma.
    3) Build a context prompt and call the LLM.
    Returns (answer, [source_page_ids]).
    """
    # Ensure API key is set at runtime
    openai.api_key = os.getenv("OPENAI_API_KEY")
    if not openai.api_key:
        raise RuntimeError("Please set OPENAI_API_KEY in your .env or environment")

    # a) Embed query
    q_emb = get_query_embedding(query)

    # b) Query top_k documents
    results = collection.query(
        query_embeddings=[q_emb],
        n_results=top_k
    )
    docs, metadatas = results["documents"][0], results["metadatas"][0]

    # c) Build RAG prompt
    context = "\n---\n".join(docs)
    prompt = (
        "You are a knowledgeable travel assistant. Use the following context to answer the question.\n\n"
        f"{context}\n\nQuestion: {query}\nAnswer:"
    )

    # d) Obtain answer from the LLM
    answer = call_llm(prompt)

    # e) Extract source page_ids
    sources = [md.get("page_id", "unknown") for md in metadatas]
    return answer, sources
