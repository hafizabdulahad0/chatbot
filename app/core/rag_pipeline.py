# app/core/rag_pipeline.py

import os
import openai
from chromadb import PersistentClient
from app.core.llm_client import call_llm

# Read API key & vectorstore path
openai.api_key = os.getenv("OPENAI_API_KEY")
DB_PATH = os.getenv("VECTORSTORE_PATH", "vectorstores/my_company/chroma.sqlite3")

# Initialize Chroma client & collection
client = PersistentClient(path=DB_PATH)
collection = client.get_or_create_collection(name="docs")

def get_query_embedding(text: str) -> list[float]:
    """
    Create an embedding for the user's query.
    """
    resp = openai.Embedding.create(model="text-embedding-ada-002", input=text)
    return resp["data"][0]["embedding"]

def run_rag(query: str, top_k: int=3) -> tuple[str, list[str]]:
    """
    1. Embed the query.
    2. Retrieve top_k chunks from Chroma.
    3. Build a prompt with those chunks.
    4. Call LLM to get the answer.
    Returns (answer, [source_page_ids]).
    """
    # 1) Embed user question
    q_emb = get_query_embedding(query)

    # 2) Query vectorstore
    res = collection.query(query_embeddings=[q_emb], n_results=top_k)
    docs, metadatas = res["documents"][0], res["metadatas"][0]

    # 3) Build the RAG prompt
    context = "\n---\n".join(docs)
    prompt = (
        "You are a knowledgeable travel assistant. Use the following context:\n\n"
        f"{context}\n\nQuestion: {query}\nAnswer:"
    )

    # 4) Get the answer from the LLM
    answer = call_llm(prompt)

    # Extract source page_ids from metadata
    sources = [md.get("page_id","unknown") for md in metadatas]
    return answer, sources
