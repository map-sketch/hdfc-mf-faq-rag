import requests
import time
import random
from bs4 import BeautifulSoup

# Rotating list of realistic browser User-Agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
]

def get_session():
    session = requests.Session()
    session.headers.update({
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    })
    return session


def fetch_page_content(url, retries=3):
    for attempt in range(retries):
        try:
            session = get_session()
            # First hit the homepage to establish a session/cookies like a real browser
            session.get("https://groww.in", timeout=15)
            time.sleep(random.uniform(2, 4))

            response = session.get(url, timeout=20)
            response.raise_for_status()

            if len(response.text) < 500:
                print(f"  Warning: Very short response on attempt {attempt+1} for {url}")
                time.sleep(random.uniform(3, 6))
                continue

            return response.text

        except Exception as e:
            print(f"  Error on attempt {attempt+1} for {url}: {e}")
            if attempt < retries - 1:
                time.sleep(random.uniform(5, 10))

    return ""


def clean_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove non-content elements
    for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'noscript', 'iframe']):
        tag.extract()

    # Remove elements that are typically ads/social/cookie banners by class/id hints
    for tag in soup.find_all(True, {'class': lambda c: c and any(
        x in ' '.join(c) for x in ['cookie', 'banner', 'popup', 'modal', 'ad-', 'social']
    )}):
        tag.extract()

    text = soup.get_text(separator='\n')

    # Clean up whitespace
    lines = [line.strip() for line in text.splitlines()]
    cleaned_lines = [line for line in lines if line and len(line) > 2]
    cleaned_text = '\n'.join(cleaned_lines)

    return cleaned_text


def scrape_url(url):
    print(f"  Fetching: {url}")
    html = fetch_page_content(url)
    if not html:
        print(f"  Failed to fetch content for {url}")
        return ""
    cleaned = clean_html(html)
    print(f"  Fetched {len(cleaned)} characters from {url}")
    return cleaned
