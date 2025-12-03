
import re
from pathlib import Path
from typing import Dict, List

from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).parent
AM_BEST_DIR = BASE_DIR / "am_best"

AM_BEST_FILES = {
    "progressivecommercial.com": "",
    "travelers.com": "The Travelers Indemnity Company of Connecticut - Company Profile - Best's Credit Rating Center.html",
    "libertymutual.com":"Liberty Mutual Insurance Company - Company Profile - Best's Credit Rating Center.html",
    "sentry.com":"Sentry Insurance Company - Company Profile - Best's Credit Rating Center.html",
    "oldrepublic.com":"Old Republic Life Insurance Company - Company Profile - Best's Credit Rating Center.html",
    "berkshirehathaway.com":"Berkshire Hathaway Life Insurance Company of Nebraska - Company Profile - Best's Credit Rating Center.html",
    "zurichna.com":"Zurich Insurance Company Limited - Company Profile - Best's Credit Rating Center.html",
    "thehartford.com":"Hartford Life and Accident Insurance Company - Company Profile - Best's Credit Rating Center.html",
    "statefarm.com":"State Farm Life Insurance Company - Company Profile - Best's Credit Rating Center.html",
    "gwccnet.com":"Great West Casualty Company - Company Profile - Best's Credit Rating Center.html",
    
}

def extract_rating_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator="\n", strip=True)

    patterns = [
        r"Financial Strength Rating\s*\(FSR\)\s*:\s*([A-Z][+A-Z ]+\(?[A-Za-z ]*\)?)",
        r"Best's Financial Strength Rating\s*:\s*([A-Z][+A-Z ]+\(?[A-Za-z ]*\)?)",
        r"Financial Strength Rating\s*:\s*([A-Z][+A-Z ]+\(?[A-Za-z ]*\)?)",
        r"FSR\s*:\s*([A-Z][+A-Z ]+\(?[A-Za-z ]*\)?)",
    ]

    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return m.group(1).strip()

    approx = re.search(r"\b([ABCD][+-]?(?:\s*\([A-Za-z ]+\))?)\b", text)
    if approx:
        return approx.group(1).strip()

    return "Not Available"


def fetch_am_best_ratings(domains: List[str]) -> Dict[str, str]:
    """
    For each domain, load its corresponding AM Best HTML file from am_best/
    and extract the Financial Strength Rating.

    Returns:
        { domain: rating_str }
    """
    ratings: Dict[str, str] = {}

    for domain in domains:
        filename = AM_BEST_FILES.get(domain, "")
        if not filename:
            print(f"[AM BEST] No local HTML file configured for {domain}")
            ratings[domain] = "Not Available"
            continue

        file_path = AM_BEST_DIR / filename
        if not file_path.exists():
            print(f"[AM BEST] File not found for {domain}: {file_path}")
            ratings[domain] = "Not Available"
            continue

        try:
            html = file_path.read_text(encoding="utf-8", errors="ignore")
            rating = extract_rating_from_html(html)
            ratings[domain] = rating
            print(f"[AM BEST] {domain}: {rating}")
        except Exception as e:
            print(f"[AM BEST] Error reading/parsing {file_path}: {e}")
            ratings[domain] = "Not Available"

    return ratings