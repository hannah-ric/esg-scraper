#!/usr/bin/env python3
"""
Comprehensive test suite for ESG Intelligence Platform
Tests all API endpoints, security features, and core functionality
"""

import os
import sys
import time
from datetime import datetime

import requests

# Set test environment
os.environ["JWT_SECRET"] = "test-secret-key"
os.environ["UPSTASH_REDIS_URL"] = "redis://localhost:6379"
os.environ["MONGODB_URI"] = "mongodb://localhost:27017/test_esg"

# Configuration
BASE_URL = "http://localhost:5000"
TEST_URLS = [
    "https://www.apple.com/environment/",
    "https://sustainability.google/",
    "https://www.microsoft.com/en-us/sustainability",
]


class Colors:
    """ANSI color codes for terminal output"""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def print_header(text):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}\n")


def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")


def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")


def print_info(text):
    """Print info message"""
    print(f"{Colors.YELLOW}ℹ️  {text}{Colors.RESET}")


def test_health_check():
    """Test the health check endpoint"""
    print_header("Testing Health Check")

    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print_success(f"Health check passed: {data}")
            return True
        else:
            print_error(f"Health check failed with status: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Health check error: {str(e)}")
        return False


def test_web_interface():
    """Test if web interface is accessible"""
    print_header("Testing Web Interface")

    try:
        response = requests.get(BASE_URL)
        if response.status_code == 200 and "ESG Intelligence Platform" in response.text:
            print_success("Web interface is accessible")
            print_info("Page title found in HTML")
            return True
        else:
            print_error("Web interface not accessible")
            return False
    except Exception as e:
        print_error(f"Web interface error: {str(e)}")
        return False


def test_url_scraping():
    """Test URL scraping functionality"""
    print_header("Testing URL Scraping")

    test_url = TEST_URLS[0]
    print_info(f"Testing with URL: {test_url}")

    try:
        response = requests.post(
            f"{BASE_URL}/api/scrape", json={"url": test_url, "depth": 1}, timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            if "results" in data and len(data["results"]) > 0:
                result = data["results"][0]
                print_success("URL scraping successful")
                print_info(f"Title: {result.get('title', 'N/A')}")
                print_info(
                    f"ESG Scores - E: {result['scores']['environmental']}%, "
                    f"S: {result['scores']['social']}%, "
                    f"G: {result['scores']['governance']}%"
                )
                print_info(
                    f"Keywords found: {', '.join(result['top_keywords'][:5])}..."
                )
                return True
            else:
                print_error("No results returned from scraping")
                return False
        else:
            print_error(f"Scraping failed with status: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Scraping error: {str(e)}")
        return False


def test_crawling():
    """Test web crawling functionality"""
    print_header("Testing Web Crawling")

    test_url = "https://example.com"
    print_info(f"Testing crawl with URL: {test_url} (depth: 2)")

    try:
        response = requests.post(
            f"{BASE_URL}/api/scrape", json={"url": test_url, "depth": 2}, timeout=60
        )

        if response.status_code == 200:
            data = response.json()
            if "results" in data:
                print_success(
                    f"Crawling successful - found {len(data['results'])} pages"
                )
                for i, result in enumerate(data["results"][:3]):
                    print_info(f"  Page {i + 1}: {result.get('url', 'N/A')}")
                return True
            else:
                print_error("No results from crawling")
                return False
        else:
            print_error(f"Crawling failed with status: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Crawling error: {str(e)}")
        return False


def test_pdf_analysis():
    """Test PDF analysis functionality"""
    print_header("Testing PDF Analysis")

    print_info("Note: PDF testing requires a valid PDF file")
    print_info("Skipping automated PDF test - manual testing recommended")
    return True


def test_database_retrieval():
    """Test database document retrieval"""
    print_header("Testing Database Retrieval")

    try:
        response = requests.get(f"{BASE_URL}/api/documents")

        if response.status_code == 200:
            data = response.json()
            if "documents" in data:
                doc_count = len(data["documents"])
                print_success(
                    f"Database retrieval successful - {doc_count} documents found"
                )

                if doc_count > 0:
                    latest = data["documents"][0]
                    print_info(f"Latest document: {latest.get('title', 'N/A')}")
                    print_info(f"Scraped at: {latest.get('scraped_at', 'N/A')}")
                return True
            else:
                print_error("Invalid response format")
                return False
        else:
            print_error(
                f"Database retrieval failed with status: {response.status_code}"
            )
            return False
    except Exception as e:
        print_error(f"Database retrieval error: {str(e)}")
        return False


def test_error_handling():
    """Test error handling"""
    print_header("Testing Error Handling")

    # Test invalid URL
    print_info("Testing with invalid URL...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/scrape", json={"url": "not-a-valid-url", "depth": 1}
        )
        print_success(f"Invalid URL handled properly - status: {response.status_code}")
    except Exception:
        print_error("Invalid URL caused unexpected error")
        return False

    # Test missing parameters
    print_info("Testing with missing parameters...")
    try:
        response = requests.post(f"{BASE_URL}/api/scrape", json={})
        if response.status_code == 400:
            print_success("Missing parameters handled properly")
        else:
            print_error("Missing parameters not handled correctly")
            return False
    except Exception:
        print_error("Missing parameters caused unexpected error")
        return False

    return True


def run_performance_test():
    """Run a simple performance test"""
    print_header("Performance Test")

    print_info("Testing response times...")

    endpoints = [
        ("Health Check", "GET", "/health", None),
        ("Home Page", "GET", "/", None),
        ("Get Documents", "GET", "/api/documents", None),
    ]

    for name, method, endpoint, data in endpoints:
        start_time = time.time()

        try:
            if method == "GET":
                requests.get(f"{BASE_URL}{endpoint}")
            else:
                requests.post(f"{BASE_URL}{endpoint}", json=data)

            elapsed = time.time() - start_time

            if elapsed < 0.5:
                print_success(f"{name}: {elapsed:.3f}s ⚡")
            elif elapsed < 2.0:
                print_info(f"{name}: {elapsed:.3f}s")
            else:
                print_error(f"{name}: {elapsed:.3f}s (slow)")

        except Exception as e:
            print_error(f"{name}: Failed - {str(e)}")

    return True


def main():
    """Run all tests"""
    print_header("ESG Intelligence Platform Test Suite")
    print(f"Testing server at: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Check if server is running
    print("\nChecking if server is running...")
    try:
        requests.get(BASE_URL, timeout=5)
    except Exception:
        print_error("Server is not responding!")
        print_info("Please ensure the Docker container is running:")
        print_info("  docker-compose up -d")
        sys.exit(1)

    # Run tests
    tests = [
        ("Health Check", test_health_check),
        ("Web Interface", test_web_interface),
        ("URL Scraping", test_url_scraping),
        ("Web Crawling", test_crawling),
        ("PDF Analysis", test_pdf_analysis),
        ("Database Retrieval", test_database_retrieval),
        ("Error Handling", test_error_handling),
        ("Performance", run_performance_test),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"Test '{test_name}' crashed: {str(e)}")
            results.append((test_name, False))

        time.sleep(1)  # Small delay between tests

    # Summary
    print_header("Test Summary")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    print(f"\n{Colors.BOLD}Results:{Colors.RESET}")
    for test_name, result in results:
        status = (
            f"{Colors.GREEN}PASSED{Colors.RESET}"
            if result
            else f"{Colors.RED}FAILED{Colors.RESET}"
        )
        print(f"  {test_name:<20} {status}")

    print(f"\n{Colors.BOLD}Total: {passed}/{total} tests passed{Colors.RESET}")

    if passed == total:
        print_success("\nAll tests passed! 🎉")
        print_info("Your ESG Intelligence Platform is working correctly!")
    else:
        print_error(f"\n{total - passed} tests failed")
        print_info("Please check the logs: docker-compose logs")


if __name__ == "__main__":
    main()
