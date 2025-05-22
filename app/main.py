# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from app.api.chat import router as chat_router
from app.db.mongodb import connect_to_mongo

load_dotenv()

app = FastAPI(
    title="Custom Chatbot Backend",
    version="1.0.0",
    description="OpenAI-powered RAG chatbot service"
)

# Allow Swagger, JS front-end, etc. to call /chat
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount our test UI at /frontend
app.mount("/frontend", StaticFiles(directory="frontend", html=True), name="frontend")

# Chat endpoint
connect_to_mongo()
app.include_router(chat_router, prefix="/chat")

# (Optional) health check at /health
@app.get("/health")
async def health_check():
    return {"status":"ok","message":"running"}
