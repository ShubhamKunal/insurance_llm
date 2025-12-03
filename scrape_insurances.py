from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from urllib.parse import urlparse, urljoin
import collections
import requests
import re
from am_best_scraper import fetch_am_best_ratings




import os
from prompts.prompt import build_prompt
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from dotenv import load_dotenv
import google.generativeai as genai

BASE_DIR = Path(__file__).parent
WEBSITES_FILE = BASE_DIR / "websites.txt"
SCRAPED_DIR = BASE_DIR / "scraped_data"
MAX_CHARS_PER_SITE_FOR_AI = 10000  
GEMINI_MODEL = "gemini-2.5-flash"

TRUCK_KEYWORDS = ["truck", "trucking", "commercial-auto", "fleet", "motor-carrier", "commercial-auto"]



def load_env():
    load_dotenv()
    if not os.getenv("GEMINI_API_KEY"):
        raise RuntimeError("GEMINI_API_KEY missing from environment or .env file.")
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def read_websites(file_path: Path):
    sites = []
    with file_path.open("r", encoding="utf-8") as f:
        for line in f:
            url = line.strip()
            if url and not url.startswith("#"):
                sites.append(url)
    return sites


def domain_from_url(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host or parsed.path.replace("/", "_") or "unknown_site"


def is_truck_relevant(url: str, link_text: str) -> bool:
    text = (url + " " + (link_text or "")).lower()
    return any(k in text for k in TRUCK_KEYWORDS)


def extract_visible_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
        tag.decompose()

    texts = []
    for tag in soup.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
        txt = tag.get_text(separator=" ", strip=True)
        if txt:
            texts.append(txt)
    return "\n".join(texts)


def scrape_truck_pages(start_url: str, max_pages: int = 5) -> str:
    """
    Crawl up to `max_pages` internal pages that look relevant
    to truck/trucking/commercial auto content.
    """
    print(f"[SCRAPE] Deep truck scrape starting at {start_url} ...")

    parsed_start = urlparse(start_url)
    base_domain = parsed_start.netloc

    visited = set()
    queue = collections.deque([start_url])
    collected_texts = []

    headers = {
        "User-Agent": "Mozilla/5.0 (CommercialTruckScraper/1.0)"
    }

    pages_scraped = 0

    while queue and pages_scraped < max_pages:
        url = queue.popleft()
        if url in visited:
            continue
        visited.add(url)

        try:
            resp = requests.get(url, headers=headers, timeout=20)
            resp.raise_for_status()
        except Exception as e:
            print(f"[SCRAPE] Failed {url}: {e}")
            continue

        pages_scraped += 1
        print(f"[SCRAPE] [{pages_scraped}/{max_pages}] {url}")

        html = resp.text
        page_text = extract_visible_text(html)
        collected_texts.append(page_text)

        # find more truck-related internal links
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            link_text = a.get_text(strip=True)
            new_url = urljoin(url, href)

            parsed_new = urlparse(new_url)
            if parsed_new.netloc != base_domain:
                continue  # external

            if new_url in visited:
                continue

            # only queue truck-relevant links
            if is_truck_relevant(new_url, link_text):
                queue.append(new_url)

    combined = "\n\n".join(collected_texts)
    print(f"[SCRAPE] Total collected characters for {start_url}: {len(combined)}")
    return combined

def save_scraped_text(domain: str, text: str):
    site_dir = SCRAPED_DIR / domain
    site_dir.mkdir(parents=True, exist_ok=True)

    out_file = site_dir / "content.txt"
    with out_file.open("w", encoding="utf-8") as f:
        f.write(text)

    print(f"[SAVE] Saved text -> {out_file}")


def collect_scraped_texts() -> dict:
    results = {}
    if not SCRAPED_DIR.exists():
        return results

    for site_dir in SCRAPED_DIR.iterdir():
        if not site_dir.is_dir():
            continue

        content_file = site_dir / "content.txt"
        if not content_file.exists():
            continue

        with content_file.open("r", encoding="utf-8") as f:
            results[site_dir.name] = f.read()

    return results



def create_pdf_from_response(response_text: str, pdf_path: str = "output.pdf"):
    styles = getSampleStyleSheet()

    heading_style = ParagraphStyle(
        "Heading",
        parent=styles["Heading1"],
        fontSize=16,
        leading=20,
        spaceAfter=10,
        textColor=colors.darkblue,
    )

    subheading_style = ParagraphStyle(
        "SubHeading",
        parent=styles["Heading2"],
        fontSize=13,
        leading=16,
        spaceAfter=6,
        textColor=colors.darkred,
    )

    body_style = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontSize=10,
        leading=13,
        spaceAfter=3,
    )

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=LETTER,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    story = []

    # Convert markdown **bold** to HTML <b>
    def md_to_html(s: str) -> str:
        return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)

    # Split by headings
    idx1 = response_text.find("### 1.")
    idx2 = response_text.find("### 2.")
    idx3 = response_text.find("### 3.")

    if idx1 == -1:
        # Fallback: just dump everything
        story.append(Paragraph(md_to_html(response_text).replace("\n", "<br/>"), body_style))
        doc.build(story)
        return

    section1 = response_text[idx1 : idx2 if idx2 != -1 else len(response_text)].strip()
    section2 = response_text[idx2 : idx3 if idx3 != -1 else len(response_text)].strip() if idx2 != -1 else ""
    section3 = response_text[idx3:].strip() if idx3 != -1 else ""

    def add_section(section_text: str, default_title: str):
        if not section_text:
            return

        lines = section_text.splitlines()

        # first heading line
        heading_line = next((l for l in lines if l.startswith("###")), f"### {default_title}")
        title = heading_line.lstrip("#").strip()

        # add main heading
        story.append(Paragraph(title, heading_style))
        story.append(Spacer(1, 8))

        # optional: local subheading (like "Companies & Coverages", etc.) – not strictly needed
        # story.append(Paragraph(subtitle, subheading_style))
        # story.append(Spacer(1, 6))

        # other lines -> paragraphs
        content_lines = [
            l for l in lines
            if not l.startswith("###") and not l.strip().startswith("---")
        ]

        for line in content_lines:
            cleaned = line.rstrip()
            if not cleaned:
                story.append(Spacer(1, 4))
                continue

            # no bullet stripping needed if prompt obeyed, but just in case:
            cleaned = cleaned.lstrip("*-•").strip()

            # Turn numbered lines and normal lines into Paragraphs
            html = md_to_html(cleaned)
            story.append(Paragraph(html, body_style))

        story.append(Spacer(1, 16))

    # Add all three sections
    add_section(section1, "1. Commercial Truck Insurance Coverages and Other Notes")
    add_section(section2, "2. Clean Comparison Narrative")
    add_section(section3, "3. Comparison Summary, Observations, and Differentiators")

    doc.build(story)
    print(f"[PDF] Written to {pdf_path}")

def compare_coverages_with_gemini(scraped_data: dict):
    if not scraped_data:
        print("[AI] No scraped data available.")
        return

    # 1) Fetch AM Best ratings from local HTML files
    domains = list(scraped_data.keys())
    am_best_ratings = fetch_am_best_ratings(domains)

    model = genai.GenerativeModel(GEMINI_MODEL)

    # 2) Build prompt with both scraped website text & AM Best ratings
    prompt = build_prompt(scraped_data, am_best_ratings)

    print("[AI] Sending request to Gemini 2.5 Flash...")
    response = model.generate_content(prompt)

    text = response.text or ""

    print("\n\n===== AI COMPARISON RESULT =====\n")
    print(text)

    # Save raw output
    with open("output.txt", "w", encoding="utf-8") as f:
        f.write(text)

    # Create the nicely formatted PDF (we keep your current style)
    create_pdf_from_response(text, pdf_path="output.pdf")


def main():
    load_env()

    if not WEBSITES_FILE.exists():
        raise FileNotFoundError("websites.txt not found.")

    websites = read_websites(WEBSITES_FILE)
    print(f"[INFO] Loaded {len(websites)} websites.\n")

    for url in websites:
        try:
            text = scrape_truck_pages(url, max_pages=6)  
            save_scraped_text(domain_from_url(url), text)
        except Exception as e:
            print(f"[ERROR] Failed to deep-scrape {url}: {e}")

    scraped = collect_scraped_texts()
    compare_coverages_with_gemini(scraped)


if __name__ == "__main__":
    main()
