#!/usr/bin/env python3
"""
run_pipeline_with_manual_scraping.py

Assumes your *_structured.json files live in processed_data/<COMPANY_NAME>/.
1) Chunk them
2) Validate them
3) Build Chroma vectorstore
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from services.data_ingestion.transformer import Transformer
from services.data_ingestion.loader      import Loader
from services.vectorstore_builder.build_vectorstore import main as build_vectorstore

def main():
    root    = Path(__file__).parent
    company = os.getenv("COMPANY_NAME", "my_company")
    processed_dir = root / "processed_data" / company

    if not processed_dir.exists() or not any(processed_dir.glob("*_structured.json")):
        raise FileNotFoundError(f"No *_structured.json files found in {processed_dir}")

    print(f"✅ Found structured JSON in {processed_dir}")

    print("✂️  Chunking JSON → token‐limited slices")
    Transformer(processed_dir=processed_dir).transform_all()

    print("🔍 Validating structured JSON documents")
    Loader(processed_dir=processed_dir).validate_all()

    print("🛠  Building Chroma vectorstore")
    build_vectorstore()

    print("🎉 Pipeline complete!")

if __name__ == "__main__":
    main()
