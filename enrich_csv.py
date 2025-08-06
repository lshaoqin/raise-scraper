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
    url = f"https://www.raise.sg/directory/{slug}/"
    try:
        resp = session.get(url, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"Failed: {slug} ({e})")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    result = {"address": None, "email": None, "phone": None}

    # --- Address ---
    address_heading = soup.find('p', string=re.compile(r'^\s*Address\s*$', re.IGNORECASE))
    if address_heading:
        address_container = address_heading.find_next('div')
        if address_container:
            address_text = address_container.get_text(separator=" ", strip=True)
            result["address"] = address_text if address_text else None

    # --- Email ---
    email_tag = soup.find('a', href=re.compile(r'^mailto:', re.IGNORECASE))
    if email_tag:
        result["email"] = email_tag.get_text(strip=True)

    # --- Phone ---
    phone_tag = soup.find('a', href=re.compile(r'^tel:', re.IGNORECASE))
    if phone_tag:
        result["phone"] = phone_tag.get_text(strip=True)
    else:
        # fallback via regex search inside contact section
        contact_popup = soup.select_one('.js-bfg-brand-contact-info-popup')
        if contact_popup:
            phones = PHONE_REGEX.findall(contact_popup.get_text())
            if phones:
                result["phone"] = phones[0]

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
