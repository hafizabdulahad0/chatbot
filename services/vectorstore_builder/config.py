from pathlib import Path
import os

# Use COMPANY_NAME from .env or fallback
COMPANY_NAME = os.getenv("COMPANY_NAME", "my_company")

# Base project directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Where structured JSON lives
PROCESSED_DIR = BASE_DIR / "processed_data" / COMPANY_NAME

# Where ChromaDB will be stored
VECTORSTORE_DIR = BASE_DIR / "vectorstores" / COMPANY_NAME
