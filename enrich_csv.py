import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time

BASE_URL = "https://www.raise.sg/directory/"
HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

EMAIL_REGEX = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')
PHONE_REGEX = re.compile(r'\+?\d[\d\s\-\(\)]{6,}\d')

session = requests.Session()
session.headers.update(HEADERS)

def slugify(name):
    slug = name.lower().replace("&", "and").replace("(", "").replace(")", "")
    slug = re.sub(r'[^a-z0-9]+', "-", slug).strip("-")
    return slug

def fetch_details(slug):
    url = f"{BASE_URL}{slug}/"
    try:
        resp = session.get(url, timeout=10)
        resp.raise_for_status()
    except Exception:
        return None  # trigger fallback
    soup = BeautifulSoup(resp.text, "html.parser")
    result = {"address": None, "email": None, "phone": None}

    # Address
    addr_heading = soup.find('h4', string="Address")
    if addr_heading and addr_heading.find_next_sibling("p"):
        result["address"] = addr_heading.find_next_sibling("p").get_text(strip=True)

    # Contact info
    contact_heading = soup.find(string="Contact")
    if contact_heading:
        parent = contact_heading.find_parent()
        text = parent.get_text(separator=" ", strip=True)
        emails = EMAIL_REGEX.findall(text)
        phones = PHONE_REGEX.findall(text)
        result["email"] = emails[0] if emails else None
        result["phone"] = phones[0] if phones else None

    return result

def enrich_csv(input_file, output_file):
    df = pd.read_csv(input_file)
    enriched = []

    for _, row in df.iterrows():
        name = row['name']
        slug = slugify(name)
        print(f"Trying: {slug}")
        details = fetch_details(slug)

        # fallback
        if not details:
            fallback_name = name + " pte ltd"
            fallback_slug = slugify(fallback_name)
            print(f"Retrying with fallback slug: {fallback_slug}")
            details = fetch_details(fallback_slug)

        enriched.append({
            "id": row.get("id"),
            "name": name,
            "address": details.get("address") if details else None,
            "email": details.get("email") if details else None,
            "phone": details.get("phone") if details else None
        })

        time.sleep(0.3)

    pd.DataFrame(enriched).to_csv(output_file, index=False)
    print(f"✅ Enriched CSV saved to: {output_file}")

if __name__ == "__main__":
    enrich_csv("raise_social_enterprises.csv", "raise_directory_enriched.csv")
