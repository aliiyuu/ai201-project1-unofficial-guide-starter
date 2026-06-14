"""
parse_bruinwalk_html.py

Parses a locally-saved Bruinwalk class page HTML file and extracts
professor cards (name, ratings, review snippet) as clean text.

Usage:
    python parse_bruinwalk_html.py "COM SCI 31 _ Bruinwalk.html" documents/raw/bruinwalk_cs31_reviews.txt
"""

import re
import sys
from pathlib import Path
from bs4 import BeautifulSoup


def parse_class_page(html_path: str) -> str:
    html = Path(html_path).read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")

    # Extract course title
    h2 = soup.select_one(".aggregate-header h2")
    course_title = h2.get_text(strip=True) if h2 else "Unknown Course"

    # Find the source URL from the og:url meta tag
    og_url = soup.find("meta", property="og:url")
    source_url = og_url["content"] if og_url else html_path

    lines = [
        f"Source URL: {source_url}",
        f"Course: {course_title}",
        "",
    ]

    cards = soup.select(".aggregate-card")
    for card in cards:
        # Professor name
        name_tag = card.select_one(".card-heading h2 a")
        prof_name = name_tag.get_text(strip=True) if name_tag else "Unknown"

        # Overall rating
        overall_tag = card.select_one(".overall-rating-badge")
        overall = overall_tag.get_text(strip=True) if overall_tag else "N/A"

        # Individual ratings
        rating_pairs = []
        for rating_div in card.select(".rating"):
            labels = rating_div.find_all("b")
            if len(labels) == 2:
                label = labels[0].get_text(strip=True)
                value = labels[1].get_text(strip=True).split("/")[0].strip()
                rating_pairs.append(f"{label}: {value}/5")

        # Review snippet — second <a> inside .review-container is the text
        review_links = card.select(".review-container a")
        review_text = ""
        if len(review_links) >= 2:
            review_text = re.sub(r"\s+", " ", review_links[1].get_text(" ", strip=True))
        elif len(review_links) == 1:
            review_text = re.sub(r"\s+", " ", review_links[0].get_text(" ", strip=True))

        if review_text in ("No reviews have been written yet.", ""):
            continue  # Skip professors with no reviews

        lines.append(f"Professor: {prof_name}")
        lines.append(f"Overall Rating: {overall}/5")
        if rating_pairs:
            lines.append("  " + " | ".join(rating_pairs))
        lines.append(f"Most Helpful Review: {review_text}")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python parse_bruinwalk_html.py <input_html> <output_txt>")
        sys.exit(1)

    html_path = sys.argv[1]
    out_path = sys.argv[2]

    result = parse_class_page(html_path)
    Path(out_path).write_text(result, encoding="utf-8")
    print(f"Written to {out_path}")
    # Preview
    print("\n--- Preview (first 800 chars) ---")
    print(result[:800])
