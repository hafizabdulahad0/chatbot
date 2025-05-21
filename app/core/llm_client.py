# app/core/llm_client.py

import os
import openai

# Read API key
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise RuntimeError("Please set OPENAI_API_KEY")

def call_llm(
    prompt: str,
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.0,
    max_tokens: int = 512
) -> str:
    """
    Send a chat completion request to OpenAI and return the assistant's reply.
    """
    resp = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user",   "content": prompt}
        ],
        temperature=temperature,
        max_tokens=max_tokens
    )
    return resp.choices[0].message.content.strip()
