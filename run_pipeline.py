#!/usr/bin/env python3
"""
run_pipeline.py

Read clean URLs from scripts/urls.txt → Scrape HTML → Parse → Chunk → Validate → Build vectorstore.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env so we always have OPENAI_API_KEY etc.
load_dotenv()

# Offline‐ETL classes
from services.data_ingestion.scraper     import WebScraper
from services.data_ingestion.parser      import HtmlParser
from services.data_ingestion.transformer import Transformer
from services.data_ingestion.loader      import Loader

# Vectorstore builder entrypoint
from services.vectorstore_builder.build_vectorstore import main as build_vectorstore

def main():
    root    = Path(__file__).parent
    company = os.getenv("COMPANY_NAME", "my_company")

    # ── 1. Load & sanitize URLs ────────────────────────────────────
    url_file = root / "scripts" / "urls.txt"
    if not url_file.exists():
        raise FileNotFoundError(f"{url_file} not found – please populate it with one URL per line.")
    raw_lines = url_file.read_text(encoding="utf-8").splitlines()

    # Keep only the first whitespace‐separated token on each non-blank line
    urls = []
    for line in raw_lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        clean_url = line.split()[0]  # drop trailing citations or markup
        urls.append(clean_url)

    print(f"✅ Loaded {len(urls)} clean URLs from {url_file}")

    # ── 2. Scrape raw HTML pages ────────────────────────────────────
    raw_dir = root / "raw_data" / company
    raw_dir.mkdir(parents=True, exist_ok=True)
    print(f"🔍 Scraping HTML → {raw_dir}")
    WebScraper(output_dir=raw_dir).scrape(urls)

    # ── 3. Parse HTML into structured JSON ─────────────────────────
    manifest_dir  = root / "data" / "webpages"        # <— new manifest_dir
    processed_dir = root / "processed_data" / company
    processed_dir.mkdir(parents=True, exist_ok=True)
    print(f"📄 Parsing HTML → JSON in {processed_dir}")
    HtmlParser(
        manifest_dir=manifest_dir,                    # <— pass manifest_dir
        raw_dir=raw_dir,
        processed_dir=processed_dir
    ).parse_all()

    # ── 4. Chunk text into token‐limited slices ────────────────────
    print("✂️  Chunking text into ≤500-token pieces")
    Transformer(processed_dir=processed_dir).transform_all()

    # ── 5. Validate JSON schema integrity ──────────────────────────
    print("🔍 Validating structured JSON documents")
    Loader(processed_dir=processed_dir).validate_all()

    # ── 6. Build the Chroma vectorstore ────────────────────────────
    print("🛠  Building Chroma vectorstore")
    build_vectorstore()

    print("🎉 Pipeline complete!")

if __name__ == "__main__":
    main()
