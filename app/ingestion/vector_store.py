import os
from chromadb import PersistentClient

class VectorStore:
    """
    Runtime wrapper around ChromaDB for upsert & query.
    """

    def __init__(self, db_path: str, collection_name: str="docs"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.client = PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def upsert_chunk(self, chunk_id: str, embedding: list[float], text: str, metadata: dict):
        """
        Insert or update a single text chunk into the vector store.
        """
        self.collection.upsert(
            ids=[chunk_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata]
        )

    def query(self, query_emb: list[float], top_k: int=3):
        """
        Query the vector store and return (docs, metadatas).
        """
        res = self.collection.query(query_embeddings=[query_emb], n_results=top_k)
        return res["documents"][0], res["metadatas"][0] 