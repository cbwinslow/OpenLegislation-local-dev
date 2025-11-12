#!/usr/bin/env python3
"""
Simple Web Crawling Test Script

Tests the core web crawling functionality without CrewAI framework.
"""

import sys
import os
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
    print("✅ crawl4ai imported successfully")
except ImportError as e:
    print(f"❌ crawl4ai import failed: {e}")
    print("Installing crawl4ai...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "crawl4ai"])
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode


async def test_crawl_website(url: str, jurisdiction: str = "test") -> Dict:
    """Test crawling a single website"""

    print(f"🌐 Testing crawl of {jurisdiction} website: {url}")

    # Configure browser
    browser_config = BrowserConfig(
        headless=True,
        verbose=False,
        extra_args=["--disable-web-security", "--disable-features=VizDisplayCompositor"]
    )

    # Configure crawler
    crawl_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        wait_for='body',
        page_timeout=30000,
        delay_before_return_html=2.0
    )

    try:
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=url, config=crawl_config)

            if result.success:
                print(f"✅ Successfully crawled {url}")
                print(f"   Content length: {len(result.html)} characters")

                # Basic extraction test
                extracted_data = await extract_test_data(result.html, jurisdiction, url)

                return {
                    'status': 'success',
                    'url': url,
                    'jurisdiction': jurisdiction,
                    'content_length': len(result.html),
                    'data': extracted_data,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                print(f"❌ Failed to crawl {url}: {result.error_message}")
                return {
                    'status': 'error',
                    'url': url,
                    'error': result.error_message,
                    'jurisdiction': jurisdiction
                }

    except Exception as e:
        print(f"❌ Exception during crawl: {e}")
        return {
            'status': 'error',
            'url': url,
            'error': str(e),
            'jurisdiction': jurisdiction
        }


async def extract_test_data(html: str, jurisdiction: str, url: str) -> List[Dict]:
    """Extract basic test data from HTML"""

    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        # Extract basic page info
        title = soup.title.get_text(strip=True) if soup.title else "No title"

        # Look for links that might be bills or legislative content
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            text = a.get_text(strip=True)
            if any(keyword in text.lower() for keyword in ['bill', 'legislation', 'act', 'resolution']):
                links.append({
                    'url': href if href.startswith('http') else f"https://www.congress.gov{href}",
                    'text': text,
                    'type': 'potential_bill'
                })

        return [{
            'title': title,
            'links_found': len(links),
            'sample_links': links[:5],  # First 5 links
            'jurisdiction': jurisdiction,
            'source_url': url
        }]

    except Exception as e:
        print(f"Error extracting test data: {e}")
        return [{
            'error': str(e),
            'jurisdiction': jurisdiction,
            'source_url': url
        }]


async def main():
    """Main test function"""

    print("🚀 Starting Web Crawling Test")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Test websites
    test_sites = [
        {
            'url': 'https://www.congress.gov/search?q=%7B%22source%22%3A%22legislation%22%7D',
            'jurisdiction': 'federal'
        },
        {
            'url': 'https://www.nysenate.gov/search/legislation',
            'jurisdiction': 'nys'
        }
    ]

    results = []

    for site in test_sites:
        result = await test_crawl_website(site['url'], site['jurisdiction'])
        results.append(result)
        print()  # Empty line between results

    # Save results
    output_file = project_root / "crawling_test_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print("✅ Test completed!")
    print(f"📄 Results saved to: {output_file}")

    # Summary
    successful = sum(1 for r in results if r['status'] == 'success')
    print(f"\n📊 Summary: {successful}/{len(results)} sites crawled successfully")


if __name__ == "__main__":
    asyncio.run(main())