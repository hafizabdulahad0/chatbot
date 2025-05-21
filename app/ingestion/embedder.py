import os
import openai

# Read the API key at runtime
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_embedding(text: str, model: str="text-embedding-ada-002") -> list[float]:
    """
    Call OpenAI's embedding endpoint for any text.
    """
    resp = openai.Embedding.create(model=model, input=text)
    return resp["data"][0]["embedding"] 