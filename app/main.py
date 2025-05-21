# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware   # ← import this
from dotenv import load_dotenv
from app.api.chat import router as chat_router
from app.db.mongodb import connect_to_mongo

load_dotenv()

app = FastAPI(
    title="Custom Chatbot Backend",
    description="OpenAI‐powered RAG chatbot service",
    version="1.0.0"
)

# ─── CORS SETTINGS ───────────────────────────────────────────
# Allow your Swagger UI (and any browser client) to call /chat
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            # <-- for dev you can allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ─────────────────────────────────────────────────────────────

connect_to_mongo()
app.include_router(chat_router, prefix="/chat")

@app.get("/", tags=["Health"])
async def health_check():
    return {"status": "ok", "message": "Service is running"}
