# services/data_ingestion/parser.py

import json
import re
import logging
from pathlib import Path
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)

class HtmlParser:
    """
    Rule-based parser that extracts tour data from HTML
    into the client’s exact JSON schema.
    """

    def __init__(self, raw_dir: Path, processed_dir: Path, manifest_dir: Path):
        self.raw_dir       = raw_dir
        self.processed_dir = processed_dir
        self.manifest_dir  = manifest_dir

        self.processed_dir.mkdir(parents=True, exist_ok=True)

        # Build page_id → url map from your manifest JSONs
        self.url_map = {}
        for f in manifest_dir.glob("*.json"):
            data = json.loads(f.read_text(encoding="utf-8"))
            if "url" in data:
                self.url_map[f.stem] = data["url"]

    def parse_all(self):
        for html_file in self.raw_dir.glob("*.html"):
            page_id = html_file.stem
            logging.info(f"Parsing {page_id}")
            html = html_file.read_text(encoding="utf-8")
            soup = BeautifulSoup(html, "html.parser")

            # 1) page_title
            title_tag = soup.select_one("h1") or soup.find("title")
            page_title = title_tag.get_text(strip=True) if title_tag else page_id

            # 2) url
            url = self.url_map.get(page_id, "")

            # 3) overview: first paragraph under main content
            overview_tag = soup.select_one(".overview p") or soup.select_one("p")
            overview = overview_tag.get_text(strip=True) if overview_tag else ""

            # 4) travel_days: look for "x Day" or "x Days"
            days = 0
            day_text = soup.find(text=re.compile(r"(\d+)\s+Days?"))
            if day_text:
                days = int(re.search(r"(\d+)\s+Days?", day_text).group(1))

            # 5) pick_and_drop_point: look for keywords
            pd = ""
            pd_tag = soup.find(text=re.compile(r"Pickup.*Drop", re.I))
            if pd_tag:
                pd = pd_tag.strip()

            # 6) tour_highlights: list items under some .highlights class or first UL
            highlights = []
            for ul in soup.select(".highlights ul") or soup.select("ul"):
                for li in ul.select("li"):
                    highlights.append(li.get_text(strip=True))
                if highlights:
                    break

            # 7) itinerary: map each Day header to its list of steps
            itinerary = {}
            for hdr in soup.find_all(re.compile("^h[1-4]$")):
                txt = hdr.get_text(strip=True)
                m = re.match(r"Day\s*(\d+)", txt, re.I)
                if m:
                    key = f"Day_{m.group(1)}"
                    steps = []
                    # collect <li> under the next UL, or subsequent <p> until next header
                    next_ul = hdr.find_next_sibling("ul")
                    if next_ul:
                        steps = [li.get_text(strip=True) for li in next_ul.select("li")]
                    else:
                        for sib in hdr.find_next_siblings():
                            if sib.name and re.match(r"h[1-4]", sib.name):
                                break
                            if sib.name == "p":
                                steps.append(sib.get_text(strip=True))
                    itinerary[key] = steps

            # 8) places_to_visit: find a section titled "places to visit"
            places = []
            sec = soup.find(lambda t: t.name in ["h2","h3"] and "place" in t.get_text(strip=True).lower())
            if sec:
                ul = sec.find_next_sibling("ul")
                if ul:
                    places = [li.get_text(strip=True) for li in ul.select("li")]

            # 9) trip_faqs: FAQs under a .faq class or DL
            faqs = []
            for block in soup.select(".faq") or soup.select("dl"):
                # dl terms
                if block.name == "dl":
                    terms = block.select("dt")
                    defs  = block.select("dd")
                    for q,a in zip(terms, defs):
                        faqs.append({
                            "question": q.get_text(strip=True),
                            "answer":   a.get_text(strip=True)
                        })
                else:
                    q = block.select_one(".question") or block.select_one("dt")
                    a = block.select_one(".answer")   or block.select_one("dd")
                    if q and a:
                        faqs.append({
                            "question": q.get_text(strip=True),
                            "answer":   a.get_text(strip=True)
                        })

            # 10) includes / excludes
            included = []
            exc      = []
            inc_hdr = soup.find(lambda t: t.name in ["h2","h3"] and "include" in t.get_text(strip=True).lower())
            if inc_hdr:
                ul = inc_hdr.find_next_sibling("ul")
                included = [li.get_text(strip=True) for li in ul.select("li")] if ul else []
            exc_hdr = soup.find(lambda t: t.name in ["h2","h3"] and "exclude" in t.get_text(strip=True).lower())
            if exc_hdr:
                ul = exc_hdr.find_next_sibling("ul")
                exc = [li.get_text(strip=True) for li in ul.select("li")] if ul else []

            # assemble
            structured = {
                "page_title": page_title,
                "url": url,
                "sections": {
                    "overview": overview,
                    "travel_days": days,
                    "pick_and_drop_point": pd,
                    "tour_highlights": highlights,
                    "itinerary": itinerary,
                    "places_to_visit": places,
                    "trip_faqs": faqs,
                    "what_is_included": included,
                    "what_is_excluded": exc,
                }
            }

            # write out
            out = self.processed_dir / f"{page_id}_structured.json"
            out.write_text(json.dumps(structured, ensure_ascii=False, indent=2), encoding="utf-8")
            logging.info(f"{page_id}: parsed → {out}")
