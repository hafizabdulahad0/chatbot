# app/api/chat.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

from app.core.rag_pipeline import run_rag
from services.booking import create_booking, cancel_booking, booking_exists

router = APIRouter()


class ChatRequest(BaseModel):
    message: str  # The user's input message


class ChatResponse(BaseModel):
    answer: str              # The LLM's answer (or booking confirmation)
    sources: List[str] = []  # Identifiers of source chunks used (empty for booking)


@router.post("/", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    Handle POST /chat requests:

      1) If user starts with "create booking", parse:
           name=<...>, phone=<...>, trip_name=<...>,
           preferred_date=<...>, starting_city=<...>,
           email=<...>, special_requests=<...>
         Then save to MongoDB and return booking ID.

      2) If user starts with "cancel booking <booking_id>",
         attempt to delete that booking in MongoDB.

      3) Otherwise, run the RAG pipeline via run_rag().
    """
    original = req.message.strip()
    lower = original.lower()

    # ─── 1) CREATE BOOKING INTENT ────────────────────────────────────────────
    if lower.startswith("create booking"):
        # Expect format (case‐insensitive):
        #   create booking name=<Your Name>, phone=<1234>,
        #   trip_name=<5-days-hunza-china-border-trip>,
        #   preferred_date=<YYYY-MM-DD>, starting_city=<City>,
        #   email=<your@email.com>, special_requests=<...>
        remainder = original[len("create booking"):].strip()
        try:
            # Split on commas → a list of "key=value" strings
            parts = [p.strip() for p in remainder.split(",") if p.strip()]
            parsed = {}
            for part in parts:
                if "=" not in part:
                    raise ValueError("Each field must be key=value.")
                k, v = part.split("=", 1)
                parsed[k.strip().lower()] = v.strip()

            # Required fields
            name = parsed.get("name")
            phone = parsed.get("phone")
            trip_name = parsed.get("trip_name")
            if not name or not phone or not trip_name:
                raise KeyError("Missing name, phone, or trip_name.")

            # Optional fields
            preferred_date   = parsed.get("preferred_date")
            starting_city    = parsed.get("starting_city")
            email            = parsed.get("email")
            special_requests = parsed.get("special_requests")

            booking_id = create_booking(
                name=name,
                phone=phone,
                trip_name=trip_name,
                preferred_date=preferred_date,
                starting_city=starting_city,
                email=email,
                special_requests=special_requests,
            )
            return ChatResponse(
                answer=f"✅ Your booking is confirmed! Booking ID: {booking_id}",
                sources=[]
            )

        except KeyError:
            return ChatResponse(
                answer=(
                    "❌ To create a booking, please include at least:\n"
                    "`create booking name=<Your Name>, phone=<YourPhone>, trip_name=<TripCode>`\n"
                    "You may also optionally add: `preferred_date=<YYYY-MM-DD>, starting_city=<City>, email=<you@domain.com>, special_requests=<...>`"
                ),
                sources=[]
            )
        except Exception:
            return ChatResponse(
                answer=(
                    "❌ Booking wasn’t created. Please ensure all fields use exactly `key=value` separated by commas.\n"
                    "E.g.: `create booking name=Alice, phone=0312XXXXXXX, trip_name=5-days-hunza-china-border-trip, preferred_date=2025-07-01, starting_city=Lahore, email=alice@example.com, special_requests=Vegetarian`"
                ),
                sources=[]
            )

    # ─── 2) CANCEL BOOKING INTENT ───────────────────────────────────────────
    if lower.startswith("cancel booking"):
        # Expect: cancel booking <booking_id>
        tokens = original.split()
        if len(tokens) == 3:
            bid = tokens[-1].strip()
            if cancel_booking(bid):
                return ChatResponse(
                    answer=f"✅ Booking {bid} has been cancelled.",
                    sources=[]
                )
            else:
                return ChatResponse(
                    answer=f"❌ No booking found with ID {bid}.",
                    sources=[]
                )
        else:
            return ChatResponse(
                answer="❌ To cancel a booking, use exactly: `cancel booking <booking_id>`",
                sources=[]
            )

    # ─── 3) FALL BACK TO RAG PIPELINE ──────────────────────────────────────
    try:
        answer, sources = run_rag(original)
        return ChatResponse(answer=answer, sources=sources)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
