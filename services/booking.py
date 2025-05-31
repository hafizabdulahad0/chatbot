import os
import datetime
from dotenv import load_dotenv
from mongoengine import (
    connect,
    Document,
    StringField,
    EmailField,
    DateTimeField,
    ValidationError,
    DoesNotExist,
)

# ─── Load .env so MONGO_URI is available ─────────────────────────────────────
load_dotenv()  
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise RuntimeError("Please set MONGO_URI in your environment (.env)")

# Connect to MongoDB
connect(host=MONGO_URI)

class BookingRequest(Document):
    # … your fields as before …
    name = StringField(required=True)
    phone = StringField(required=True)
    trip_name = StringField(required=True)
    preferred_date = StringField(required=False)
    starting_city = StringField(required=False)
    email = EmailField(required=False)
    special_requests = StringField(required=False)
    created_at = DateTimeField(default=datetime.datetime.utcnow)

    meta = {"collection": "bookings"}
    
def create_booking(
    name: str,
    phone: str,
    trip_name: str,
    preferred_date: str = None,
    starting_city: str = None,
    email: str = None,
    special_requests: str = None,
) -> str:
    """
    Create and save a new BookingRequest document in MongoDB.
    Returns the stringified booking_id (_id).
    Raises ValidationError if required fields are missing or invalid.
    """
    doc = BookingRequest(
        name=name,
        phone=phone,
        trip_name=trip_name,
        preferred_date=preferred_date,
        starting_city=starting_city,
        email=email,
        special_requests=special_requests,
    )
    doc.save()                 # Insert into MongoDB
    return str(doc.id)         # Return the generated ObjectId as a string


def cancel_booking(booking_id: str) -> bool:
    """
    Delete the BookingRequest document with the given booking_id.
    Returns True if it existed and was deleted, False otherwise.
    """
    try:
        obj = BookingRequest.objects(id=booking_id).first()
        if obj:
            obj.delete()
            return True
        return False
    except (ValidationError, DoesNotExist):
        # If the provided booking_id is invalid or not found:
        return False


def booking_exists(booking_id: str) -> bool:
    """
    Returns True if a booking with this ID exists in MongoDB.
    """
    try:
        return BookingRequest.objects(id=booking_id).first() is not None
    except (ValidationError, DoesNotExist):
        return False
