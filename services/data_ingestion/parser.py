# services/data_ingestion/parser.py

from bs4 import BeautifulSoup
from pathlib import Path
import json

class HtmlParser:
    """
    Convert raw HTML files into a structured JSON format,
    splitting content by header tags (<h1>–<h6>).
    """

    def __init__(self, raw_dir: Path, processed_dir: Path):
        # raw_dir: where .html files live
        # processed_dir: where *_structured.json will be written
        self.raw_dir = raw_dir
        self.processed_dir = processed_dir
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def parse_all(self):
        """
        For each .html file in raw_dir:
        1. Load and parse with BeautifulSoup.
        2. For each header tag, collect its text and all
           following sibling nodes until the next header.
        3. Build a JSON with:
           - page_id
           - metadata (title)
           - sections: [{ header, content }, …]
        4. Write out as <page_id>_structured.json.
        """
        for file in self.raw_dir.glob("*.html"):
            html = file.read_text(encoding='utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            sections = []
            # Find all header tags and group their content
            for header in soup.find_all(['h1','h2','h3','h4','h5','h6']):
                header_text = header.get_text(strip=True)
                content_nodes = []

                # Gather everything until the next header
                for sib in header.find_next_siblings():
                    if sib.name and sib.name.startswith('h'):
                        break
                    text = sib.get_text(strip=True)
                    if text:
                        content_nodes.append(text)

                # If multiple paragraphs, keep list; otherwise string or empty
                content = (
                    content_nodes
                    if len(content_nodes) > 1
                    else (content_nodes[0] if content_nodes else "")
                )
                sections.append({
                    'header': header_text,
                    'content': content
                })

            # Assemble the structured document
            doc = {
                'page_id': file.stem,
                'url': '',  # optional: fill if you want
                'metadata': {
                    'title': soup.title.string if soup.title else file.stem
                },
                'sections': sections
            }

            # Write JSON with pretty indentation
            out_file = self.processed_dir / f"{file.stem}_structured.json"
            out_file.write_text(
                json.dumps(doc, ensure_ascii=False, indent=2),
                encoding='utf-8'
            )
