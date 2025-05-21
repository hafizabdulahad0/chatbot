# app/main.py

from fastapi import FastAPI
from dotenv import load_dotenv
from app.api.chat import router as chat_router
from app.db.mongodb import connect_to_mongo

# Load .env into os.environ
load_dotenv()

app = FastAPI(
    title="Custom Chatbot Backend",
    description="OpenAI‐powered RAG chatbot service",
    version="1.0.0"
)

# Initialize MongoDB if booking feature is used
connect_to_mongo()

# Mount our /chat endpoint
app.include_router(chat_router, prefix="/chat")

@app.get("/", tags=["Health"])
async def health_check():
    # Simple health check endpoint
    return {"status": "ok", "message": "Service is running"}
