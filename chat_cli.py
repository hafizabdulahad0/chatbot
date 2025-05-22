#!/usr/bin/env python3
"""
chat_cli.py

A simple command-line interface to your /chat endpoint.
"""

import requests

API_URL = "http://127.0.0.1:8000/chat/"

def main():
    print("🗨️  Chat CLI. Type 'exit' or Ctrl-C to quit.")
    while True:
        try:
            msg = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        if not msg or msg.lower() in ("exit", "quit"):
            print("Goodbye!")
            break

        # Send to your FastAPI endpoint
        try:
            resp = requests.post(API_URL, json={"message": msg})
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print("❌ Request failed:", e)
            continue

        # Print bot answer and sources
        print("Bot:", data.get("answer", "(no answer)"))
        sources = data.get("sources", [])
        if sources:
            print("Sources:", ", ".join(sources))
        print()

if __name__ == "__main__":
    main()
