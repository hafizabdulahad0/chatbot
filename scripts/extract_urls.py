import json
from pathlib import Path

def extract_urls(manifest_dir: Path) -> list[str]:
    """
    Read every .json manifest and collect the 'url' field.
    """
    urls = []
    for f in manifest_dir.glob("*.json"):
        data = json.loads(f.read_text(encoding="utf-8"))
        if u := data.get("url"):
            urls.append(u)
    return urls

if __name__ == "__main__":
    manifest_dir = Path("data") / "webpages"
    urls = extract_urls(manifest_dir)
    out_file = Path("scripts") / "urls.txt"
    out_file.write_text("\n".join(urls), encoding='utf-8')
    print(f"Extracted {len(urls)} URLs → {out_file}") 