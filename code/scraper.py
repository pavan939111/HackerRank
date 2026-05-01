import asyncio
import httpx
import hashlib
import json
import os
import time
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import trafilatura
from tqdm import tqdm

RAW_DIR = Path("data/raw")
SCRAPED_DIR = Path("data/scraped")
VISITED_FILE = Path("data/visited_urls.json")
DELAY = 1.2
MAX_PAGES = 500
TIMEOUT = 15

HACKERRANK = "https://support.hackerrank.com/hc/en-us"
CLAUDE = "https://support.anthropic.com/en/"
VISA = "https://www.visa.co.in/support.html"

COMPANY_CONFIG = {
    "hackerrank": {
        "seed": HACKERRANK,
        "allowed_domain": "support.hackerrank.com",
        "article_url_patterns": ["/hc/en-us/articles/"],
    },
    "claude": {
        "seed": CLAUDE,
        "allowed_domain": "support.anthropic.com",
        "article_url_patterns": ["/en/articles/", "/articles/"],
    },
    "visa": {
        "seed": VISA,
        "allowed_domain": "www.visa.co.in",
        "article_url_patterns": ["/support/"],
    },
}

def load_visited() -> set[str]:
    if VISITED_FILE.exists():
        try:
            with open(VISITED_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_visited(visited: set[str]):
    VISITED_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(VISITED_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(list(visited)), f, indent=2)

def is_article_url(url: str, patterns: list[str]) -> bool:
    for p in patterns:
        if p in url:
            return True
    return False

def extract_links(html: str, base_url: str, allowed_domain: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)
        if parsed.netloc == allowed_domain:
            clean_url = parsed._replace(fragment="", query="").geturl()
            links.add(clean_url)
    return list(links)

def extract_text(html: str, url: str) -> dict | None:
    result = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=True,
        no_fallback=False,
        favor_precision=True,
    )
    if not result or len(result.strip()) < 100:
        return None
        
    soup = BeautifulSoup(html, "lxml")
    title = soup.find("title")
    title_text = title.get_text(strip=True) if title else ""
    
    h = soup.find(["h1", "h2"])
    heading = h.get_text(strip=True)[:80] if h else ""
    
    return {
        "url": url,
        "title": title_text,
        "heading": heading,
        "text": result.strip(),
        "char_count": len(result.strip()),
    }

async def scrape_company(company: str, config: dict, visited: set[str]):
    (RAW_DIR / company).mkdir(parents=True, exist_ok=True)
    (SCRAPED_DIR / company).mkdir(parents=True, exist_ok=True)
    
    queue = [config["seed"]]
    scraped_count = 0
    
    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0 (support-triage-bot/1.0)"}) as client:
        while queue and scraped_count < MAX_PAGES:
            url = queue.pop(0)
            if url in visited:
                continue
            visited.add(url)
            
            try:
                resp = await client.get(url)
                if resp.status_code != 200:
                    continue
                html = resp.text
                
                slug = hashlib.md5(url.encode()).hexdigest()[:12]
                (RAW_DIR / company / f"{slug}.html").write_text(html, encoding="utf-8")
                
                links = extract_links(html, url, config["allowed_domain"])
                for link in links:
                    if link not in visited and link not in queue:
                        queue.append(link)
                        
                if is_article_url(url, config["article_url_patterns"]) or url == config["seed"]:
                    data = extract_text(html, url)
                    if data:
                        out_path = SCRAPED_DIR / company / f"{slug}.json"
                        out_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
                        scraped_count += 1
                        print(f"  [{company}] {scraped_count}: {data['title'][:60]}")
                        
                await asyncio.sleep(DELAY)
                
            except Exception as e:
                print(f"  [{company}] ERROR {url}: {e}")
                continue

    print(f"[{company}] Done: {scraped_count} articles saved")

def run_scraper():
    visited = load_visited()
    for company, config in COMPANY_CONFIG.items():
        print(f"\nScraping {company}...")
        asyncio.run(scrape_company(company, config, visited))
        save_visited(visited)
    print("\nAll scraping complete.")

if __name__ == "__main__":
    import sys
    if SCRAPED_DIR.exists() and any(SCRAPED_DIR.iterdir()):
        if "--force" not in sys.argv:
            print(f"Already have scraped data in {SCRAPED_DIR}. Pass --force to re-scrape.")
            count = sum(1 for _ in SCRAPED_DIR.rglob("*.json"))
            print(f"Current count: {count} JSON files.")
            sys.exit(0)
    run_scraper()
