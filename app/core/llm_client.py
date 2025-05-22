# app/core/llm_client.py

import os
from dotenv import load_dotenv
import openai

# ─── Load .env so OPENAI_API_KEY is available ─────────────────────────
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise RuntimeError("Please set OPENAI_API_KEY in your environment")

def call_llm(
    prompt: str,
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.0,
    max_tokens: int = 512
) -> str:
    """
    Send a chat completion request via the new v1 API and return the assistant's reply.
    """
    # Use the v1 endpoint for chat completions
    resp = openai.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user",   "content": prompt}
        ],
        temperature=temperature,
        max_tokens=max_tokens
    )
    # Extract the generated content
    return resp.choices[0].message.content.strip()
