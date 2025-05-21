# app/db/booking_models.py

from pydantic import BaseModel, Field
from app.db.mongodb import get_db

class BookingRequest(BaseModel):
    name: str = Field(..., example="Jane Doe")
    phone: str = Field(..., example="+1234567890")
    trip_name: str = Field(..., example="5-Day Hunza Tour")

def save_booking(booking: BookingRequest) -> str:
    """
    Insert a booking into MongoDB and return its ID.
    """
    db = get_db()
    result = db.bookings.insert_one(booking.dict())
    return str(result.inserted_id)
