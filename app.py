# app.py

import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# 1) Load .env
load_dotenv()

# 2) Import your existing RAG pipeline
from app.core.rag_pipeline import run_rag  # adjust import path if needed

app = Flask(__name__, static_folder="frontend")
CORS(app)  # allow all origins for development

# Health check
@app.route("/health", methods=["GET"])
def health():
    return jsonify(status="ok", message="Flask chatbot running")

# Chat endpoint
@app.route("/chat/", methods=["POST"])
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

# Serve the frontend
@app.route("/", defaults={"path": "index.html"})
@app.route("/<path:path>")
def serve_frontend(path):
    return send_from_directory(app.static_folder, path)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True)
