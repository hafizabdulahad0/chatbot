# app.py

import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# 1) Load .env so OPENAI_API_KEY, MONGO_URI, etc. are available
load_dotenv()

# 2) Import your RAG pipeline
from app.core.rag_pipeline import run_rag

# 3) Import booking service (ensure booking.py has load_dotenv() already)
from services.booking import create_booking, cancel_booking, booking_exists

app = Flask(__name__, static_folder="frontend")
CORS(app)  # allow all origins during development

# ─── Health Check ───────────────────────────────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    return jsonify(status="ok", message="Flask chatbot running")

# ─── Chat endpoint (accepts both /chat and /chat/) ───────────────────────────────
@app.route("/chat", methods=["POST"], strict_slashes=False)
def chat():
    data = request.get_json(force=True)
    msg = data.get("message")
    if not msg:
        return jsonify(error="Missing 'message' in JSON"), 422
    try:
        answer, sources = run_rag(msg)
        return jsonify(answer=answer, sources=sources)
    except Exception as e:
        return jsonify(error=str(e)), 500

# ─── Create Booking endpoint (accepts both /booking/create and /booking/create/) ──
@app.route("/booking/create", methods=["POST"], strict_slashes=False)
def create_booking_endpoint():
    body = request.get_json(force=True)
    # Validate required fields
    for field in ["name", "phone", "trip_name", "preferred_date", "starting_city"]:
        if not body.get(field):
            return jsonify(error=f"Missing field: {field}"), 422

    try:
        new_id = create_booking(
            name=body["name"],
            phone=body["phone"],
            trip_name=body["trip_name"],
            preferred_date=body["preferred_date"],
            starting_city=body["starting_city"],
            email=body.get("email"),
            special_requests=body.get("special_requests"),
        )
        return jsonify(booking_id=new_id), 201
    except Exception as e:
        return jsonify(error=str(e)), 500

# ─── Cancel Booking endpoint (accepts both /booking/cancel and /booking/cancel/) ───
@app.route("/booking/cancel", methods=["POST"], strict_slashes=False)
def cancel_booking_endpoint():
    body = request.get_json(force=True)
    bid = body.get("booking_id")
    if not bid:
        return jsonify(error="Missing field: booking_id"), 422

    if not booking_exists(bid):
        return jsonify(error="Booking not found"), 404

    try:
        success = cancel_booking(bid)
        return jsonify(success=success), 200
    except Exception as e:
        return jsonify(error=str(e)), 500

# ─── Serve your static frontend files ───────────────────────────────────────────
@app.route("/", defaults={"path": "index.html"})
@app.route("/<path:path>")
def serve_frontend(path):
    return send_from_directory(app.static_folder, path)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True)
