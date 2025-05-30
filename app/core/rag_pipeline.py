# app/core/rag_pipeline.py
import re
import os, json
from pathlib import Path
from dotenv import load_dotenv

import openai
from chromadb import PersistentClient
from app.core.llm_client import call_llm

load_dotenv()
COMPANY   = os.getenv("COMPANY_NAME", "my_company")
DB_PATH   = os.getenv("VECTORSTORE_PATH", f"vectorstores/{COMPANY}/chroma.sqlite3")
BASE_DIR  = Path(__file__).parent.parent.parent
PROCESSED = BASE_DIR / "processed_data" / COMPANY

openai.api_key = os.getenv("OPENAI_API_KEY") or ""
if not openai.api_key:
    raise RuntimeError("Please set OPENAI_API_KEY in your environment")

client     = PersistentClient(path=DB_PATH)
collection = client.get_or_create_collection(name="docs")


def get_query_embedding(text: str) -> list[float]:
    resp = openai.Embedding.create(
        model="text-embedding-ada-002",
        input=text
    )
    return resp.data[0].embedding


def find_exact_page(query: str) -> Path | None:
    """
    If the query mentions an N-Day tour, try to find
    a {N}-days-*.json file under processed_data.
    """
    m = re.search(r"(\d+)[-\s]*day", query.lower())
    if m:
        n = m.group(1)
        # gather all JSONs whose stem starts with "{n}-days"
        candidates = [
            p for p in PROCESSED.glob(f"{n}-days-*_structured.json")
            if "hunza" in p.stem
        ]
        if not candidates:
            # fallback: any {n}-days file
            candidates = list(PROCESSED.glob(f"{n}-days-*_structured.json"))
        if candidates:
            return candidates[0]
    return None


def direct_json_lookup(query: str):
    q = query.lower()
    # map trigger → json key
    section_map = {
        "include":    ("what_is_included",   True),
        "exclude":    ("what_is_excluded",   True),
        "itinerar":   ("itinerary",          False),
        "highlight":  ("tour_highlights",    False),
        "overview":   ("overview",           False),
        "faq":        ("trip_faqs",          False),
    }
    # 1) see if it's an N-day query
    page_file = find_exact_page(query)
    if page_file:
        data = json.loads(page_file.read_text(encoding="utf-8"))
    else:
        # 2) else we fallback to best-1 via embedding
        emb     = get_query_embedding(query)
        results = collection.query(query_embeddings=[emb], n_results=1)
        meta    = results["metadatas"][0][0]
        page_id = meta["page_id"]
        page_file = PROCESSED / f"{page_id}_structured.json"
        if not page_file.exists():
            return None
        data = json.loads(page_file.read_text(encoding="utf-8"))

    title    = data.get("page_title", page_file.stem)
    sections = data.get("sections", {})

    # unify list/dict handling
    def get_section(key):
        if isinstance(sections, dict):
            return sections.get(key)
        else:
            for s in sections:
                if s.get("header") == key:
                    return s.get("content")
        return None

    # 3) find which section they want
    for token, (sec_key, is_list) in section_map.items():
        if token in q:
            sec = get_section(sec_key)
            if sec_key in ("what_is_included", "what_is_excluded") and isinstance(sec, list) and sec:
                items = sec
                body  = (
                    items[0] if len(items)==1
                    else ", ".join(items[:-1]) + " and " + items[-1]
                )
                verb = "includes" if sec_key=="what_is_included" else "excludes"
                answer = (
                    f"For the “{title}” package, the tour {verb} "
                    f"{body}."
                )
                return answer, [data.get("page_id")]

            if sec_key == "itinerary" and isinstance(sec, dict):
                lines = []
                for day, plan in sec.items():
                    detail = "; ".join(plan) if isinstance(plan, list) else str(plan)
                    lines.append(f"{day}: {detail}")
                answer = f"Here’s the itinerary for “{title}”: " + " | ".join(lines)
                return answer, [data.get("page_id")]

            if sec_key == "tour_highlights" and isinstance(sec, list) and sec:
                top3 = sec[:3]
                answer = (
                    f"Key highlights of “{title}” include "
                    f"{', '.join(top3[:-1])} and {top3[-1]}."
                )
                return answer, [data.get("page_id")]

            # fallback simple sections
            if sec is not None:
                if isinstance(sec, list):
                    answer = "; ".join(str(x) for x in sec)
                else:
                    answer = str(sec)
                return answer, [data.get("page_id")]

            return None
    return None


def run_rag(query: str, top_k: int = 3):
    # 1) try direct JSON lookup (with exact N-day matching)
    direct = direct_json_lookup(query)
    if direct:
        return direct

    # 2) fallback to RAG-vector + LLM
    q_emb   = get_query_embedding(query)
    results = collection.query(query_embeddings=[q_emb], n_results=top_k)
    docs      = results["documents"][0]
    metadatas = results["metadatas"][0]

    system_instructions = (
        "You are a travel‐specialist assistant **only** trained on the provided context.  "
        "• **Answer exclusively** from the context below—no external knowledge.  "
        "• If the user’s question is **not** covered in the context, reply exactly:  "
        "`I’m sorry, I don’t know about that.`  "
        "• Keep answers **concise** and **professional**."
    )
    context = "\n---\n".join(docs)
    user_msg = f"Context:\n{context}\n\nQuestion: {query}\nAnswer:"

    answer = call_llm(
        messages=[
            {"role": "system",  "content": system_instructions},
            {"role": "user",    "content": user_msg}
        ],
        max_tokens=150
    )
    sources = [md.get("page_id", "unknown") for md in metadatas]
    return answer, sources
