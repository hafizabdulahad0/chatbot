#!/usr/bin/env python3
"""
run_pipeline.py

1) Read & sanitize URLs
2) Scrape HTML
3) Structure JSON via OpenAI LLM
4) Build ChromaDB vectorstore from that JSON
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 1) Load configuration
load_dotenv()  # ensures OPENAI_API_KEY, COMPANY_NAME, VECTORSTORE_PATH, etc. are set

# 2) Import your ingestion & vectorstore builder
from scripts.extract_urls import extract_urls
from services.data_ingestion.scraper     import WebScraper
from services.data_ingestion.llm_structurer import LLMStructurer
from services.vectorstore_builder.build_vectorstore import main as build_vectorstore

def main():
    root    = Path(__file__).parent
    company = os.getenv("COMPANY_NAME", "my_company")

    # ── 1. Load & clean URLs ────────────────────────────────────────
    url_file = root / "scripts" / "urls.txt"
    if not url_file.exists():
        raise FileNotFoundError(f"{url_file} not found. Please add URLs first.")
    urls = [line.split()[0] for line in url_file.read_text().splitlines() 
            if line.strip() and not line.strip().startswith("#")]
    print(f"✅ Loaded {len(urls)} URLs")

    # ── 2. Scrape HTML ───────────────────────────────────────────────
    raw_dir = root / "raw_data" / company
    raw_dir.mkdir(parents=True, exist_ok=True)
    print(f"🔍 Scraping HTML into {raw_dir}")
    WebScraper(output_dir=raw_dir).scrape(urls)

    # ── 3. LLM-based Structuring ────────────────────────────────────
    manifest_dir  = root / "data" / "webpages"
    processed_dir = root / "processed_data" / company
    print(f"🤖 Structuring JSON via LLM into {processed_dir}")
    structurer = LLMStructurer(
        manifest_dir=manifest_dir,
        raw_dir=raw_dir,
        processed_dir=processed_dir
    )
    structurer.structure_all()

    # ── 4. Build ChromaDB Vectorstore ──────────────────────────────
    print(f"🛠 Building ChromaDB vectorstore at {os.getenv('VECTORSTORE_PATH')}")
    build_vectorstore()

    print("🎉 Pipeline complete! Your JSON is structured and vectorstore is ready.")

if __name__ == "__main__":
    main()
