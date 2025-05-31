"""
Simple fallback web scraper using only BeautifulSoup
"""

import requests
from bs4 import BeautifulSoup


def simple_scrape(url: str, timeout: int = 10) -> str:
    """Simple web scraping fallback"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }

        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text content
        text = soup.get_text()

        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = " ".join(chunk for chunk in chunks if chunk)

        return text[:50000]  # Limit content size

    except Exception as e:
        raise Exception(f"Scraping failed: {e}")


if __name__ == "__main__":
    # Test the simple scraper
    test_url = "https://httpbin.org/html"
    try:
        content = simple_scrape(test_url)
        print(f"✅ Simple scraper works! Extracted {len(content)} characters")
    except Exception as e:
        print(f"❌ Simple scraper failed: {e}")
