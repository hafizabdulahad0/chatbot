# app/main.py

import os
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional

# Load environment variables from .env (so MONGO_URI and OPENAI_API_KEY are available)
load_dotenv()

# ─── Import Chat Router (existing RAG endpoint) ──────────────────────────────────
from app.api.chat import router as chat_router

# ─── Import MongoDB connection helper and booking service functions ──────────────
from app.db.mongodb import connect_to_mongo  # must initialize MongoDB
from services.booking import (
    create_booking,
    cancel_booking,
    booking_exists,
)


# ─── FastAPI app instance ─────────────────────────────────────────────────────────
app = FastAPI(
    title="Custom Chatbot + Booking Backend",
    version="1.0.0",
    description="OpenAI-powered RAG chatbot + MongoDB booking endpoints",
)

# Allow any origin for development (so Swagger UI, JS front-end, etc. can call /chat and /booking)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the “frontend” folder (if you have an index.html, etc.) at `/frontend`
app.mount("/frontend", StaticFiles(directory="frontend", html=True), name="frontend")


# ─── Startup event: Connect to MongoDB before handling any requests ────────────────
@app.on_event("startup")
async def startup_event():
    """
    When FastAPI starts, this runs once.
    We use it to connect to MongoDB (services/booking.py uses that connection).
    """
    connect_to_mongo()


# ─── Include existing chat routes under /chat ──────────────────────────────────────
app.include_router(chat_router, prefix="/chat")


# ─── Booking Request Models ───────────────────────────────────────────────────────
class BookingCreateRequest(BaseModel):
    name: str = Field(..., example="Alice Khan")
    phone: str = Field(..., example="+92-300-1234567")
    trip_name: str = Field(..., example="5-Day Hunza Tour")
    preferred_date: str = Field(..., example="2025-06-20")
    starting_city: str = Field(..., example="Karachi")
    email: Optional[str] = Field(None, example="alice@example.com")
    special_requests: Optional[str] = Field(None, example="Vegetarian meals only")


class BookingCancelRequest(BaseModel):
    booking_id: str = Field(..., example="64a5f3d2b1e8c4f7b9a2dff1")


# ─── Booking Endpoints ─────────────────────────────────────────────────────────────
@app.post("/booking/create", status_code=201)
def booking_create(request: BookingCreateRequest):
    """
    Create a new booking in MongoDB.
    Returns:
        {
          "booking_id": "<mongo-generated-id>"
        }
    """
    try:
        new_id = create_booking(
            name=request.name,
            phone=request.phone,
            trip_name=request.trip_name,
            preferred_date=request.preferred_date,
            starting_city=request.starting_city,
            email=request.email,
            special_requests=request.special_requests,
        )
        return {"booking_id": new_id}
    except Exception as e:
        # If validation or other error occurs, return 400
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/booking/cancel")
def booking_cancel(request: BookingCancelRequest):
    """
    Cancel (delete) an existing booking by its ID.
    Returns:
        { "success": true }
    or 404 if booking was not found.
    """
    # 1. Check existence
    if not booking_exists(request.booking_id):
        raise HTTPException(
            status_code=404,
            detail=f"Booking {request.booking_id} not found"
        )

    # 2. Attempt deletion
    try:
        success = cancel_booking(request.booking_id)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── (Optional) Health Check ───────────────────────────────────────────────────────
@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "FastAPI service is running"}


# ─── Root redirect (optional) ──────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {"message": "Welcome! Use /chat or /booking/create /booking/cancel"}


# If you prefer to run this file directly via `python app/main.py`, uncomment below:
# (But typically we run via `uvicorn app.main:app --reload`)
#
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

