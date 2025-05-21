# app/api/chat.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

from app.core.rag_pipeline import run_rag

router = APIRouter()

class ChatRequest(BaseModel):
    message: str  # The user's input message

class ChatResponse(BaseModel):
    answer: str      # The LLM's answer
    sources: List[str]  # Identifiers of the source chunks used

@router.post("/", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    Handle POST /chat requests:
    1. Run RAG pipeline on the message.
    2. Return answer + list of source IDs.
    """
    try:
        answer, sources = run_rag(req.message)
        return ChatResponse(answer=answer, sources=sources)
    except Exception as e:
        # Return a 500 error if something goes wrong
        raise HTTPException(status_code=500, detail=str(e))
