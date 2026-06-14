"""
build_documents.py

Creates all raw documents in documents/raw/ for the unofficial guide pipeline.
- Scrapes Bruinwalk class pages directly by URL (server-side rendered, no browser needed).
  For each class, also follows professor-course links to collect full review listings.
- Scrapes the professors who teach the most popular CS courses (the intro series),
  writing each one's review page to its own document.
  NOTE: Reddit was removed (HTTP 403 to unauthenticated scrapers, even the .json API).
  The UCLA registrar catalog and grades.natecation explorer were also removed because
  they are JS-rendered and a plain scrape only yields a stub or a "Loading ..." placeholder.

Usage:
    python build_documents.py
"""

import re
import sys
import requests
from pathlib import Path
from bs4 import BeautifulSoup

OUTPUT_DIR = Path("documents/raw")
HEADERS = {"User-Agent": "unofficial-guide-bot/1.0 (educational project)"}

# Bruinwalk class page URL → output filename
BRUINWALK_SOURCES = [
    ("https://www.bruinwalk.com/classes/com-sci-31/",  "bruinwalk_cs31_reviews.txt"),
    ("https://www.bruinwalk.com/classes/com-sci-32/",  "bruinwalk_cs32_reviews.txt"),
    ("https://www.bruinwalk.com/classes/com-sci-33/",  "bruinwalk_cs33_reviews.txt"),
    ("https://www.bruinwalk.com/classes/com-sci-35l/", "bruinwalk_cs35l_reviews.txt"),
]

# Professors are sourced from the most popular CS courses (the intro series, which
# are the most-taken and most-reviewed CS classes). We collect the professors who
# teach those courses and scrape each one's review page. This ties the professor
# documents to real, relevant courses rather than an alphabetical directory dump.
POPULAR_COURSE_URLS = [
    "https://www.bruinwalk.com/classes/com-sci-31/",
    "https://www.bruinwalk.com/classes/com-sci-32/",
    "https://www.bruinwalk.com/classes/com-sci-33/",
    "https://www.bruinwalk.com/classes/com-sci-35l/",
]
NUM_PROFESSORS = 6

# NOTE: Reddit (r/ucla) was dropped because it hard-blocks unauthenticated requests
# (HTTP 403 on both www and old.reddit, even via the .json API), requiring OAuth or
# a real browser session. The UCLA registrar catalog pages and the grades.natecation
# explorer were also dropped: both are JS-rendered, so a plain requests scrape only
# captures a title stub or a "Loading ..." placeholder with no usable content.


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _get_soup(url: str) -> BeautifulSoup:
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


def _parse_cards(soup: BeautifulSoup, source_url: str) -> list[str]:
    """Extract professor review blocks from a Bruinwalk aggregate-card page."""
    h2 = soup.select_one(".aggregate-header h2")
    course_title = h2.get_text(strip=True) if h2 else ""

    lines = [f"Source URL: {source_url}"]
    if course_title:
        lines.append(f"Course: {course_title}")
    lines.append("")

    for card in soup.select(".aggregate-card"):
        name_tag = card.select_one(".card-heading h2 a")
        prof_name = name_tag.get_text(strip=True) if name_tag else "Unknown"

        overall_tag = card.select_one(".overall-rating-badge")
        overall = overall_tag.get_text(strip=True) if overall_tag else "N/A"

        rating_pairs = []
        for rating_div in card.select(".rating"):
            labels = rating_div.find_all("b")
            if len(labels) == 2:
                label = labels[0].get_text(strip=True)
                value = labels[1].get_text(strip=True).split("/")[0].strip()
                rating_pairs.append(f"{label}: {value}/5")

        # .review-container has two <a> tags: a header link and the review text link
        review_links = card.select(".review-container a")
        review_text = ""
        if len(review_links) >= 2:
            review_text = _clean(review_links[1].get_text(" ", strip=True))
        elif len(review_links) == 1:
            review_text = _clean(review_links[0].get_text(" ", strip=True))

        if review_text in ("No reviews have been written yet.", ""):
            continue

        lines.append(f"Professor: {prof_name}")
        lines.append(f"Overall Rating: {overall}/5")
        if rating_pairs:
            lines.append("  " + " | ".join(rating_pairs))
        lines.append(f"Most Helpful Review: {review_text}")
        lines.append("")
        lines.append("---")
        lines.append("")

    return lines


def scrape_bruinwalk_class(url: str) -> str:
    """Scrape a Bruinwalk class page and all linked professor-course pages."""
    soup = _get_soup(url)
    lines = _parse_cards(soup, url)

    # Collect unique professor-course URLs from card heading links
    # Pattern: /professors/{slug}/{course-slug}/
    prof_urls = []
    seen_urls: set[str] = set()
    for a in soup.select(".card-heading h2 a[href*='/professors/']"):
        href = a.get("href", "")
        if href and href not in seen_urls:
            seen_urls.add(href)
            prof_urls.append(href)

    for prof_url in prof_urls:
        try:
            prof_soup = _get_soup(prof_url)
            lines += ["", f"=== {prof_url} ===", ""]
            lines += _parse_cards(prof_soup, prof_url)
        except Exception as e:
            lines.append(f"[could not fetch {prof_url}: {e}]")

    return "\n".join(lines)


def scrape_top_professors(course_urls: list[str], count: int) -> list[tuple[str, str]]:
    """Scrape professors who teach the most popular CS courses.

    Collects professor profile links from each course page (in listed order),
    then scrapes the first `count` unique professors' review pages.
    Returns a list of (output_filename, document_text) tuples, one per professor.
    """
    slugs: list[str] = []
    for course_url in course_urls:
        soup = _get_soup(course_url)
        for a in soup.select(".card-heading h2 a[href*='/professors/']"):
            m = re.match(r"^/professors/([a-z0-9-]+)/", a.get("href", ""))
            if m and m.group(1) != "not-found" and m.group(1) not in slugs:
                slugs.append(m.group(1))

    results: list[tuple[str, str]] = []
    for slug in slugs:
        if len(results) >= count:
            break
        prof_url = f"https://www.bruinwalk.com/professors/{slug}/"
        prof_soup = _get_soup(prof_url)
        text = "\n".join(_parse_cards(prof_soup, prof_url))
        # Skip professors with no written reviews — _parse_cards only emits a
        # "Most Helpful Review:" line when a card has actual review text.
        if "Most Helpful Review:" not in text:
            print(f"[skip] {slug}: no reviews")
            continue
        out_name = f"bruinwalk_prof_{slug.replace('-', '_')}.txt"
        results.append((out_name, text))

    return results


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    errors = []

    for url, out_name in BRUINWALK_SOURCES:
        try:
            text = scrape_bruinwalk_class(url)
            out = OUTPUT_DIR / out_name
            out.write_text(text, encoding="utf-8")
            print(f"[OK]   {out}")
        except Exception as e:
            print(f"[ERR]  {url}: {e}")
            errors.append(url)

    try:
        for out_name, text in scrape_top_professors(POPULAR_COURSE_URLS, NUM_PROFESSORS):
            out = OUTPUT_DIR / out_name
            out.write_text(text, encoding="utf-8")
            print(f"[OK]   {out}")
    except Exception as e:
        print(f"[ERR]  professors from popular courses: {e}")
        errors.append("top_professors")

    if errors:
        print(f"\n{len(errors)} source(s) failed.")
        sys.exit(1)
    else:
        print("\nAll documents written.")


if __name__ == "__main__":
    main()
