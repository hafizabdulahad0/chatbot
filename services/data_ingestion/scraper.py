# services/data_ingestion/scraper.py

import requests
from pathlib import Path

class WebScraper:
    """
    Download raw HTML pages from a list of URLs.
    """

    def __init__(self, output_dir: Path):
        """
        output_dir: Path to folder where raw HTML files will be saved.
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def scrape(self, urls: list[str]):
        """
        For each URL:
        1. Derive a safe filename.
        2. Fetch HTML via HTTP.
        3. Save the response text to disk.
        """
        for url in urls:
            # Turn URL path into a filename (last path segment or 'index')
            name = url.rstrip('/').split('/')[-1] or 'index'
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()  # Stop if we get a bad HTTP status
            file_path = self.output_dir / f"{name}.html"
            file_path.write_text(resp.text, encoding='utf-8')
