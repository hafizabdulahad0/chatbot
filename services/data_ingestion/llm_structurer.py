import os, re, json, logging
from pathlib import Path
from dotenv import load_dotenv
import openai
from bs4 import BeautifulSoup

# ─── Logging setup ─────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

# ─── Load OpenAI key ───────────────────────────────────────────────────
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY") or ""
if not openai.api_key:
    raise RuntimeError("Please set OPENAI_API_KEY in your .env")

# ─── Prompt: strict JSON schema, arrays for days, objects for FAQs ─────
SCHEMA_PROMPT = """
You are a JSON formatter. Given raw text plus explicit Day sections, extract EXACTLY this JSON schema:

{
  "page_title": "",
  "url": "",
  "sections": {
    "overview": "",
    "travel_days": 0,
    "pick_and_drop_point": "",
    "tour_highlights": [],
    "itinerary": {
      "Day_1": [],
      "Day_2": [],
      /* ... up to Day_N ... */
    },
    "places_to_visit": [],
    "trip_faqs": [
      { "question": "", "answer": "" }
    ],
    "what_is_included": [],
    "what_is_excluded": []
  }
}

IMPORTANT:
- NO trailing commas.
- Respond with RAW JSON only.
- Each Day_X must be an ARRAY of strings.
- If an FAQ has no answer, use:
  "This information is not available in the provided text."
"""

MAX_CHARS = 10_000  # truncate page text to avoid context‐length errors

class LLMStructurer:
    def __init__(self, manifest_dir: Path, raw_dir: Path, processed_dir: Path):
        self.raw_dir       = raw_dir
        self.processed_dir = processed_dir
        self.processed_dir.mkdir(parents=True, exist_ok=True)

        # page_id → provided URL map
        self.url_map = {}
        for f in manifest_dir.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                self.url_map[f.stem] = data.get("url", "")
            except:
                pass

    def structure_all(self):
        for html_file in self.raw_dir.glob("*.html"):
            page_id = html_file.stem
            logging.info(f"Processing {page_id}")

            # ── 1) Extract & truncate visible text ───────────────
            raw_html = html_file.read_text(encoding="utf-8")
            soup     = BeautifulSoup(raw_html, "html.parser")
            full_txt = soup.get_text(separator="\n").strip()
            text = full_txt[:MAX_CHARS]
            if len(full_txt) > MAX_CHARS:
                logging.warning(f"{page_id}: truncated to {MAX_CHARS} chars")

            # ── 2) Pull out Day X sections from ALL headers ───────
            day_sections = {}
            for hdr in soup.find_all(
                lambda t: t.name in [f"h{i}" for i in range(1,7)]
                            and re.match(r"Day\s*\d+", t.get_text(strip=True))
            ):
                key = hdr.get_text(strip=True).replace(" ", "_")
                steps = []
                for sib in hdr.find_next_siblings():
                    txt = sib.get_text(" ", strip=True)
                    if not txt: continue
                    if sib.name in [f"h{i}" for i in range(1,7)] and re.match(r"Day\s*\d+", txt):
                        break
                    steps.append(txt)
                day_sections[key] = steps

            url = self.url_map.get(page_id, "")

            # ── 3) Build the prompt ──────────────────────────────
            day_ctx = "\n\n".join(f"{k}:\n" + "\n".join(v) for k,v in day_sections.items())
            prompt = (
                f"{SCHEMA_PROMPT}\n\n"
                f"URL: {url}\n\n"
                f"RAW_DAY_SECTIONS:\n{day_ctx}\n\n"
                f"PAGE_TEXT:\n{text}"
            )

            # ── 4) Call the API ──────────────────────────────────
            try:
                resp = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role":"system","content":"You are an expert JSON extractor."},
                        {"role":"user",  "content":prompt}
                    ],
                    temperature=0.0,
                    max_tokens=1500
                )
                raw = resp.choices[0].message.content.strip()
            except Exception as e:
                logging.error(f"{page_id}: OpenAI API error: {e}")
                raw = ""

            # ── 5) Clean & extract JSON block ───────────────────
            raw = re.sub(r"```(?:json)?", "", raw)
            start = raw.find("{"); end = raw.rfind("}")+1
            json_str = raw[start:end] if start>=0 and end>start else ""
            json_str = re.sub(r",\s*([\]}])", r"\1", json_str)

            # ── 6) Try parse; on failure build a proper stub ─────
            try:
                structured = json.loads(json_str)
            except Exception as e:
                logging.warning(f"{page_id}: JSON parse failed ({e}); using stub")
                # Prepare stub with real title, URL, days
                can   = soup.find("link", rel="canonical")
                og    = soup.find("meta", property="og:url")
                real_url = (can and can.get("href")) or (og and og.get("content")) or url
                title_t = soup.find("title") or soup.find("h1")
                real_title = title_t.get_text(strip=True) if title_t else page_id.replace("-", " ").title()
                travel_days = len(day_sections)
                structured = {
                    "page_title": real_title,
                    "url": real_url or f"https://example.com/{page_id}",
                    "sections": {
                        "overview": "",
                        "travel_days": travel_days,
                        "pick_and_drop_point": "",
                        "tour_highlights": [],
                        "itinerary": day_sections,
                        "places_to_visit": [],
                        "trip_faqs": [],
                        "what_is_included": [],
                        "what_is_excluded": []
                    }
                }

            # ── 7) Normalize itinerary for all days ────────────
            td = structured["sections"].get("travel_days", len(day_sections))
            itn = structured["sections"].get("itinerary", {})
            full_itn = {}
            for i in range(1, td+1):
                key = f"Day_{i}"
                val = itn.get(key) or day_sections.get(key) or []
                if isinstance(val, str):
                    val = [line.strip() for line in val.split("\n") if line.strip()]
                full_itn[key] = val
            structured["sections"]["itinerary"] = full_itn

            # ── 8) Ensure FAQs are objects ─────────────────────
            raw_faqs = structured["sections"].get("trip_faqs", [])
            faqs = []
            for e in raw_faqs:
                if isinstance(e, dict) and "question" in e and "answer" in e:
                    faqs.append(e)
                elif isinstance(e, str):
                    faqs.append({
                        "question": e,
                        "answer": "This information is not available in the provided text."
                    })
            structured["sections"]["trip_faqs"] = faqs

            # ── 9) Save JSON ───────────────────────────────────
            out = self.processed_dir / f"{page_id}_structured.json"
            try:
                out.write_text(json.dumps(structured, ensure_ascii=False, indent=2), encoding="utf-8")
                logging.info(f"{page_id}: structured JSON saved → {out}")
            except Exception as e:
                logging.error(f"{page_id}: failed to write file: {e}")
