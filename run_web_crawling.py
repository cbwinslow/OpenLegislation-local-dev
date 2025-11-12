#!/usr/bin/env python3
"""
Web Crawling Runner Script

Executes the web crawling crew to collect legislative data from government websites.
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "tools"))

from crewai_agents.specialized_crews.web_crawling import WebCrawlingCrew, WEBSITE_CONFIGS


def main():
    """Main execution function"""

    print("🚀 Starting Web Crawling Crew")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # Initialize the web crawling crew
        crew = WebCrawlingCrew()

        # Run crawling for all configured websites
        print(f"🌐 Crawling {len(WEBSITE_CONFIGS)} website configurations...")

        result = crew.crawl_all_sources(WEBSITE_CONFIGS)

        # Save results to file
        output_file = project_root / "crawling_results.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)

        print("✅ Crawling completed successfully!")
        print(f"📄 Results saved to: {output_file}")

        # Print summary
        if 'crew_result' in result:
            print("\n📊 Summary:")
            print(f"   Status: {result.get('status', 'unknown')}")
            print(f"   Timestamp: {result.get('timestamp', 'unknown')}")

    except Exception as e:
        print(f"❌ Error during crawling: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()