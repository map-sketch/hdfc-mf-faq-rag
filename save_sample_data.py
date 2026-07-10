import json
import os
from src.scraper import scrape_url
from src.config import GROWW_SCHEME_URLS
from src.query_processor import QueryProcessor

def save_scraped_data():
    data_dir = os.path.join("data", "scraped_pages")
    os.makedirs(data_dir, exist_ok=True)
    
    for url in GROWW_SCHEME_URLS:
        print(f"Scraping {url}...")
        content = scrape_url(url)
        filename = url.split('/')[-1] + ".txt"
        filepath = os.path.join(data_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Saved {filepath}")

def save_phase3_data():
    queries = [
        "What is the exit load?",
        "My PAN is ABCDE1234F. What is the NAV?",
        "My phone number is 9876543210.",
        "Should I invest in HDFC Mid Cap?",
        "What is the best fund for long term?",
        "Compare HDFC Gold and Silver.",
        "What is the expense ratio for HDFC Flexi Cap?"
    ]
    
    qp = QueryProcessor()
    results = []
    
    for q in queries:
        is_valid, msg = qp.process(q)
        results.append({
            "query": q,
            "is_valid": is_valid,
            "refusal_message": msg
        })
        
    with open(os.path.join("data", "phase3_evaluation.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)
    print("Saved Phase 3 evaluation to data/phase3_evaluation.json")

if __name__ == "__main__":
    save_scraped_data()
    save_phase3_data()
