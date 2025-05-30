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
    messages: list[dict],
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.0,
    max_tokens: int = 256
) -> str:
    """
    Send a chat completion request via the OpenAI v1 Chat API.
    `messages` is a list of {"role": "system"|"user"|"assistant", "content": str}.
    Returns the assistant's reply content.
    """
    resp = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
    )
    return resp.choices[0].message.content.strip()
