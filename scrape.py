import requests
import time
import csv
from bs4 import BeautifulSoup

API_URL = "https://www.raise.sg/wp-json/directory/v1/filter?_wpnonce=676033530a"
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0"
}

def fetch_page(page_num):
    payload = {
        "value": {
            "page_num": page_num
        },
        "nonce": "676033530a"
    }
    res = requests.post(API_URL, json=payload, headers=HEADERS)
    return res.json()

def parse_entry(entry):
    soup = BeautifulSoup(entry["template"], "html.parser")
    name = entry.get("name", "").strip()
    raw_text = soup.get_text(separator=" ", strip=True)
    return {
        "id": soup.get("data-id"),
        "name": name,
        "text": raw_text
    }

def scrape_all(pages=48):
    all_entries = []
    for page in range(1, pages + 1):
        print(f"Scraping page {page}")
        response = fetch_page(page)
        for entry in response.get("data", []):
            parsed = parse_entry(entry)
            all_entries.append(parsed)
        time.sleep(0.3)  # be polite
    return all_entries

def save_to_csv(data, filename="raise_social_enterprises.csv"):
    with open(filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "name", "text"])
        writer.writeheader()
        writer.writerows(data)

if __name__ == "__main__":
    data = scrape_all()
    save_to_csv(data)
    print(f"✅ Saved {len(data)} entries to CSV.")
