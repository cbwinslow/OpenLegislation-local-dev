"""
Web Crawling & Data Collection Crew for OpenLegislation

Specialized CrewAI crew for intelligent web crawling and legislative data collection.
Uses crawl4ai to extract bills, members, votes, and other legislative data from government websites.
"""

from crewai import Agent, Task, Crew, Process
from crewai_tools import SerperDevTool, ScrapeWebsiteTool
from typing import Dict, List, Any, Optional
import json
import os
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import re
import hashlib

# Add project paths
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # Project root
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))  # Tools directory

try:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
except ImportError:
    print("crawl4ai not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "crawl4ai"])
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

from decorators import (
    ingestion_performance, telemetry, performance_monitor,
    feature_flag, TelemetryCollector, PerformanceMonitor
)


class WebCrawlerAgent(Agent):
    """AI Agent specialized in intelligent web crawling for legislative data"""

    def __init__(self, **kwargs):
        super().__init__(
            role="Web Crawling Specialist",
            goal="Intelligently crawl government websites to extract legislative data including bills, members, votes, and committee information",
            backstory="""You are an expert web crawler with deep knowledge of government website structures,
            legislative data formats, and intelligent extraction techniques. You excel at navigating complex
            government portals, handling rate limits, and extracting structured data from unstructured web content.""",
            verbose=True,
            allow_delegation=True,
            tools=[ScrapeWebsiteTool()],
            **kwargs
        )

    def crawl_website(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Crawl a specific website for legislative data"""
        return asyncio.run(self._async_crawl_website(config))

    async def _async_crawl_website(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Async implementation of website crawling"""
        url = config.get('url')
        data_type = config.get('data_type', 'bills')
        jurisdiction = config.get('jurisdiction', 'unknown')

        print(f"🌐 Crawling {jurisdiction} {data_type} from {url}")

        # Configure browser
        browser_config = BrowserConfig(
            headless=True,
            verbose=False,
            extra_args=["--disable-web-security", "--disable-features=VizDisplayCompositor"]
        )

        # Configure crawler
        crawl_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            js_code=config.get('js_code', ''),
            wait_for=config.get('wait_for', 'body'),
            page_timeout=config.get('page_timeout', 30000),
            delay_before_return_html=config.get('delay', 2.0)
        )

        try:
            async with AsyncWebCrawler(config=browser_config) as crawler:
                result = await crawler.arun(
                    url=url,
                    config=crawl_config
                )

                if result.success:
                    # Extract data based on type
                    extracted_data = await self._extract_legislative_data(
                        result.html, data_type, jurisdiction, url
                    )

                    return {
                        'status': 'success',
                        'url': url,
                        'jurisdiction': jurisdiction,
                        'data_type': data_type,
                        'data': extracted_data,
                        'crawled_at': datetime.now().isoformat(),
                        'content_hash': hashlib.md5(result.html.encode()).hexdigest()
                    }
                else:
                    return {
                        'status': 'error',
                        'url': url,
                        'error': result.error_message,
                        'jurisdiction': jurisdiction,
                        'data_type': data_type
                    }

        except Exception as e:
            return {
                'status': 'error',
                'url': url,
                'error': str(e),
                'jurisdiction': jurisdiction,
                'data_type': data_type
            }

    async def _extract_legislative_data(self, html: str, data_type: str, jurisdiction: str, url: str) -> List[Dict]:
        """Extract legislative data from HTML based on data type"""

        extractors = {
            'bills': self._extract_bills,
            'members': self._extract_members,
            'votes': self._extract_votes,
            'committees': self._extract_committees,
            'hearings': self._extract_hearings
        }

        extractor = extractors.get(data_type, self._extract_generic)
        return await extractor(html, jurisdiction, url)

    async def _extract_bills(self, html: str, jurisdiction: str, url: str) -> List[Dict]:
        """Extract bill information from HTML"""

        bills = []

        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')

            # Federal Congress.gov pattern
            if 'congress.gov' in url:
                bill_items = soup.find_all('li', class_='item')
                for item in bill_items:
                    bill_link = item.find('a')
                    if bill_link:
                        bill_id = bill_link.get('href', '').split('/')[-1]
                        title_elem = item.find('h2') or item.find('span', class_='result-title')
                        title = title_elem.get_text(strip=True) if title_elem else ""

                        bills.append({
                            'bill_id': bill_id,
                            'title': title,
                            'source_url': f"https://www.congress.gov{bill_link['href']}",
                            'jurisdiction': jurisdiction,
                            'status': 'unknown',  # Would need more parsing
                            'introduced_date': 'unknown'
                        })

            # NY Senate pattern
            elif 'nysenate.gov' in url:
                bill_rows = soup.find_all('tr', class_='bill-row') or soup.find_all('div', class_='bill-item')
                for row in bill_rows:
                    bill_link = row.find('a')
                    if bill_link:
                        bill_id = bill_link.get_text(strip=True)
                        title_elem = row.find('td', class_='title') or row.find('div', class_='bill-title')
                        title = title_elem.get_text(strip=True) if title_elem else ""

                        bills.append({
                            'bill_id': bill_id,
                            'title': title,
                            'source_url': f"https://www.nysenate.gov{bill_link['href']}",
                            'jurisdiction': jurisdiction,
                            'status': 'unknown',
                            'introduced_date': 'unknown'
                        })

        except Exception as e:
            print(f"Error extracting bills: {e}")

        return bills

    async def _extract_members(self, html: str, jurisdiction: str, url: str) -> List[Dict]:
        """Extract member information from HTML"""

        members = []

        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')

            # Federal Congress.gov pattern
            if 'congress.gov' in url:
                member_cards = soup.find_all('div', class_='member-container')
                for card in member_cards:
                    name_elem = card.find('h3') or card.find('a', class_='member-name')
                    if name_elem:
                        name = name_elem.get_text(strip=True)
                        member_url = name_elem.get('href', '')

                        # Extract party and district from additional elements
                        party_elem = card.find('span', class_='party')
                        party = party_elem.get_text(strip=True) if party_elem else ""

                        district_elem = card.find('span', class_='district')
                        district = district_elem.get_text(strip=True) if district_elem else ""

                        members.append({
                            'member_id': name.lower().replace(' ', '_'),
                            'name': name,
                            'party': party,
                            'district': district,
                            'chamber': 'unknown',  # Would need more parsing
                            'source_url': f"https://www.congress.gov{member_url}",
                            'jurisdiction': jurisdiction
                        })

            # NY Senate pattern
            elif 'nysenate.gov' in url:
                senator_cards = soup.find_all('div', class_='senator-card') or soup.find_all('tr', class_='senator-row')
                for card in senator_cards:
                    name_elem = card.find('a', class_='senator-name') or card.find('td', class_='name')
                    if name_elem:
                        name = name_elem.get_text(strip=True)
                        senator_url = name_elem.get('href', '')

                        # Extract district
                        district_elem = card.find('span', class_='district') or card.find('td', class_='district')
                        district = district_elem.get_text(strip=True) if district_elem else ""

                        # Extract party
                        party_elem = card.find('span', class_='party') or card.find('td', class_='party')
                        party = party_elem.get_text(strip=True) if party_elem else ""

                        members.append({
                            'member_id': f"nys_{district.lower()}",
                            'name': name,
                            'party': party,
                            'district': district,
                            'chamber': 'senate',
                            'source_url': f"https://www.nysenate.gov{senator_url}",
                            'jurisdiction': jurisdiction
                        })

        except Exception as e:
            print(f"Error extracting members: {e}")

        return members

    async def _extract_votes(self, html: str, jurisdiction: str, url: str) -> List[Dict]:
        """Extract vote information from HTML"""

        votes = []

        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')

            # Look for vote tables or listings
            vote_items = soup.find_all('tr', class_='vote-row') or soup.find_all('div', class_='vote-item')

            for item in vote_items:
                # Extract vote details - this would need to be customized per site
                bill_elem = item.find('a', class_='bill-link') or item.find('td', class_='bill')
                bill_id = bill_elem.get_text(strip=True) if bill_elem else ""

                result_elem = item.find('span', class_='result') or item.find('td', class_='result')
                result = result_elem.get_text(strip=True) if result_elem else ""

                date_elem = item.find('span', class_='date') or item.find('td', class_='date')
                date = date_elem.get_text(strip=True) if date_elem else ""

                votes.append({
                    'vote_id': f"{bill_id}_{date.replace('/', '_')}",
                    'bill_id': bill_id,
                    'result': result,
                    'date': date,
                    'source_url': url,
                    'jurisdiction': jurisdiction
                })

        except Exception as e:
            print(f"Error extracting votes: {e}")

        return votes

    async def _extract_committees(self, html: str, jurisdiction: str, url: str) -> List[Dict]:
        """Extract committee information from HTML"""

        committees = []

        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')

            # Look for committee listings
            committee_items = soup.find_all('div', class_='committee-item') or soup.find_all('tr', class_='committee-row')

            for item in committee_items:
                name_elem = item.find('h3') or item.find('a', class_='committee-name')
                if name_elem:
                    name = name_elem.get_text(strip=True)
                    committee_url = name_elem.get('href', '')

                    committees.append({
                        'committee_id': name.lower().replace(' ', '_').replace('committee', '').strip('_'),
                        'name': name,
                        'source_url': committee_url if committee_url.startswith('http') else f"https://www.congress.gov{committee_url}",
                        'jurisdiction': jurisdiction,
                        'chamber': 'unknown'  # Would need more parsing
                    })

        except Exception as e:
            print(f"Error extracting committees: {e}")

        return committees

    async def _extract_hearings(self, html: str, jurisdiction: str, url: str) -> List[Dict]:
        """Extract hearing information from HTML"""

        hearings = []

        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')

            # Look for hearing listings
            hearing_items = soup.find_all('div', class_='hearing-item') or soup.find_all('tr', class_='hearing-row')

            for item in hearing_items:
                title_elem = item.find('h3') or item.find('a', class_='hearing-title')
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    hearing_url = title_elem.get('href', '')

                    # Extract date
                    date_elem = item.find('span', class_='date') or item.find('td', class_='date')
                    date = date_elem.get_text(strip=True) if date_elem else ""

                    hearings.append({
                        'hearing_id': title.lower().replace(' ', '_').replace(',', '').replace('.', ''),
                        'title': title,
                        'date': date,
                        'source_url': hearing_url if hearing_url.startswith('http') else f"https://www.congress.gov{hearing_url}",
                        'jurisdiction': jurisdiction
                    })

        except Exception as e:
            print(f"Error extracting hearings: {e}")

        return hearings

    async def _extract_generic(self, html: str, jurisdiction: str, url: str) -> List[Dict]:
        """Generic extraction for unknown data types"""

        # Return basic page information
        return [{
            'data_type': 'generic',
            'source_url': url,
            'jurisdiction': jurisdiction,
            'content_length': len(html),
            'title': 'Page content extracted'
        }]
        

class DataProcessorAgent(Agent):
    """AI Agent specialized in processing and structuring crawled legislative data"""

    def __init__(self, **kwargs):
        super().__init__(
            role="Data Processing Specialist",
            goal="Process and structure crawled legislative data for database insertion and trigger ingestion pipelines",
            backstory="""You are an expert data processor with deep knowledge of legislative data structures,
            database schemas, and ETL processes. You excel at cleaning, validating, and transforming
            web-scraped data into structured formats ready for ingestion.""",
            verbose=True,
            allow_delegation=True,
            **kwargs
        )

    def process_crawled_data(self, crawl_results: List[Dict]) -> Dict[str, Any]:
        """Process crawled data and prepare for database insertion"""
        processed_data = {
            'bills': [],
            'members': [],
            'votes': [],
            'committees': [],
            'hearings': [],
            'metadata': {
                'total_records': 0,
                'jurisdictions': set(),
                'data_types': set(),
                'processing_timestamp': datetime.now().isoformat()
            }
        }

        for result in crawl_results:
            if result['status'] != 'success':
                continue

            jurisdiction = result['jurisdiction']
            data_type = result['data_type']

            processed_data['metadata']['jurisdictions'].add(jurisdiction)
            processed_data['metadata']['data_types'].add(data_type)

            # Process each data item
            for item in result['data']:
                processed_item = self._standardize_data_item(item, data_type, jurisdiction)
                if processed_item:
                    processed_data[data_type].append(processed_item)
                    processed_data['metadata']['total_records'] += 1

        # Convert sets to lists for JSON serialization
        processed_data['metadata']['jurisdictions'] = list(processed_data['metadata']['jurisdictions'])
        processed_data['metadata']['data_types'] = list(processed_data['metadata']['data_types'])

        return processed_data

    def _standardize_data_item(self, item: Dict, data_type: str, jurisdiction: str) -> Optional[Dict]:
        """Standardize a data item to match database schema"""

        try:
            standardized = {
                'jurisdiction': jurisdiction,
                'data_type': data_type,
                'crawled_at': datetime.now().isoformat(),
                'source_url': item.get('source_url', ''),
                'raw_data': item
            }

            # Add type-specific standardization
            if data_type == 'bills':
                standardized.update({
                    'bill_id': item.get('bill_id', item.get('id', '')),
                    'title': item.get('title', ''),
                    'status': item.get('status', ''),
                    'introduced_date': item.get('introduced_date', item.get('date', ''))
                })
            elif data_type == 'members':
                standardized.update({
                    'member_id': item.get('member_id', item.get('id', '')),
                    'name': item.get('name', ''),
                    'party': item.get('party', ''),
                    'district': item.get('district', ''),
                    'chamber': item.get('chamber', '')
                })
            elif data_type == 'votes':
                standardized.update({
                    'vote_id': item.get('vote_id', item.get('id', '')),
                    'bill_id': item.get('bill_id', ''),
                    'result': item.get('result', ''),
                    'date': item.get('date', '')
                })

            return standardized

        except Exception as e:
            print(f"Error standardizing {data_type} item: {e}")
            return None


class DatabaseIngestionAgent(Agent):
    """AI Agent specialized in database operations and ingestion triggering"""

    def __init__(self, **kwargs):
        super().__init__(
            role="Database Ingestion Specialist",
            goal="Insert processed legislative data into database and trigger ingestion pipelines",
            backstory="""You are an expert database engineer with deep knowledge of PostgreSQL,
            data ingestion pipelines, and ETL processes. You excel at managing database transactions,
            triggering ingestion workflows, and ensuring data integrity.""",
            verbose=True,
            allow_delegation=True,
            **kwargs
        )

    def insert_crawled_data(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert processed data into database and trigger ingestion"""

        results = {
            'inserted_records': 0,
            'triggered_ingestion': False,
            'errors': [],
            'ingestion_jobs': []
        }

        try:
            # Import database connection utilities
            from tools.enhanced_ingestion_orchestrator import EnhancedIngestionOrchestrator

            orchestrator = EnhancedIngestionOrchestrator()
            with orchestrator.get_db_connection() as conn:
                with conn.cursor() as cursor:
                    # Insert data by type
                    for data_type, items in processed_data.items():
                        if data_type == 'metadata':
                            continue

                        table_name = f"crawled_{data_type}"
                        inserted = self._insert_data_batch(cursor, table_name, items)

                        results['inserted_records'] += inserted
                        print(f"Inserted {inserted} {data_type} records")

                    # Insert metadata
                    self._insert_metadata(cursor, processed_data['metadata'])

                    conn.commit()

            # Trigger ingestion pipelines
            results['ingestion_jobs'] = self._trigger_ingestion_pipelines(processed_data)
            results['triggered_ingestion'] = len(results['ingestion_jobs']) > 0

        except Exception as e:
            results['errors'].append(str(e))
            print(f"Database insertion error: {e}")

        return results

    def _insert_data_batch(self, cursor, table_name: str, items: List[Dict]) -> int:
        """Insert a batch of items into the database"""

        if not items:
            return 0

        # Create table if it doesn't exist
        self._ensure_table_exists(cursor, table_name, items[0])

        # Insert items
        inserted = 0
        for item in items:
            try:
                columns = ', '.join(item.keys())
                placeholders = ', '.join(['%s'] * len(item))
                values = list(item.values())

                query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                cursor.execute(query, values)
                inserted += 1

            except Exception as e:
                print(f"Error inserting item into {table_name}: {e}")
                continue

        return inserted

    def _ensure_table_exists(self, cursor, table_name: str, sample_item: Dict):
        """Ensure the table exists with proper schema"""

        # Create table with dynamic schema based on item structure
        columns = []
        for key, value in sample_item.items():
            if isinstance(value, str):
                columns.append(f"{key} TEXT")
            elif isinstance(value, int):
                columns.append(f"{key} INTEGER")
            elif isinstance(value, float):
                columns.append(f"{key} REAL")
            elif isinstance(value, bool):
                columns.append(f"{key} BOOLEAN")
            elif isinstance(value, dict) or isinstance(value, list):
                columns.append(f"{key} JSONB")
            else:
                columns.append(f"{key} TEXT")

        # Add standard columns
        columns.extend([
            "id SERIAL PRIMARY KEY",
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "processed BOOLEAN DEFAULT FALSE"
        ])

        create_query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            {', '.join(columns)}
        )
        """

        cursor.execute(create_query)

    def _insert_metadata(self, cursor, metadata: Dict):
        """Insert crawl metadata"""

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS crawl_metadata (
            id SERIAL PRIMARY KEY,
            crawl_timestamp TIMESTAMP,
            total_records INTEGER,
            jurisdictions JSONB,
            data_types JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute("""
        INSERT INTO crawl_metadata (crawl_timestamp, total_records, jurisdictions, data_types)
        VALUES (%s, %s, %s, %s)
        """, (
            metadata['processing_timestamp'],
            metadata['total_records'],
            json.dumps(metadata['jurisdictions']),
            json.dumps(metadata['data_types'])
        ))

    def _trigger_ingestion_pipelines(self, processed_data: Dict[str, Any]) -> List[str]:
        """Trigger appropriate ingestion scripts based on data types"""

        triggered_jobs = []

        # Check which data types have new data
        data_types = processed_data.get('metadata', {}).get('data_types', [])

        if 'bills' in data_types:
            # Trigger bill ingestion
            self._run_ingestion_script('bill_ingestion.py')
            triggered_jobs.append('bill_ingestion')

        if 'members' in data_types:
            # Trigger member ingestion
            self._run_ingestion_script('member_ingestion.py')
            triggered_jobs.append('member_ingestion')

        if 'votes' in data_types:
            # Trigger vote ingestion
            self._run_ingestion_script('vote_ingestion.py')
            triggered_jobs.append('vote_ingestion')

        return triggered_jobs

    def _run_ingestion_script(self, script_name: str):
        """Run an ingestion script"""

        script_path = Path(__file__).parent.parent.parent / "tools" / script_name

        if script_path.exists():
            try:
                import subprocess
                result = subprocess.run([
                    sys.executable, str(script_path)
                ], capture_output=True, text=True, timeout=300)

                if result.returncode == 0:
                    print(f"Successfully ran {script_name}")
                else:
                    print(f"Error running {script_name}: {result.stderr}")

            except Exception as e:
                print(f"Failed to run {script_name}: {e}")
        else:
            print(f"Ingestion script {script_name} not found")


class WebCrawlingCrew:
    """Crew for web crawling and data collection"""

    def __init__(self):
        self.crawler_agent = WebCrawlerAgent()
        self.processor_agent = DataProcessorAgent()
        self.ingestion_agent = DatabaseIngestionAgent()

    def create_crawling_crew(self, websites_config: List[Dict[str, Any]]) -> Crew:
        """Create a crew for crawling multiple websites"""

        # Create tasks for each website
        tasks = []

        for config in websites_config:
            crawl_task = Task(
                description=f"Crawl {config['jurisdiction']} {config['data_type']} from {config['url']}",
                agent=self.crawler_agent,
                expected_output="Crawled data with extracted legislative information",
                context=[config]
            )

            tasks.append(crawl_task)

        # Processing task
        process_task = Task(
            description="Process and structure all crawled legislative data",
            agent=self.processor_agent,
            expected_output="Structured data ready for database insertion",
            context=tasks  # Depends on all crawl tasks
        )

        # Database insertion task
        ingest_task = Task(
            description="Insert processed data into database and trigger ingestion pipelines",
            agent=self.ingestion_agent,
            expected_output="Data inserted and ingestion pipelines triggered",
            context=[process_task]
        )

        return Crew(
            agents=[self.crawler_agent, self.processor_agent, self.ingestion_agent],
            tasks=[*tasks, process_task, ingest_task],
            process=Process.sequential,
            verbose=True
        )

    def crawl_all_sources(self, websites_config: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Crawl all configured websites and process the data"""

        crew = self.create_crawling_crew(websites_config)
        result = crew.kickoff()

        return {
            'status': 'completed',
            'crew_result': result,
            'timestamp': datetime.now().isoformat()
        }


# Website configurations for different jurisdictions
WEBSITE_CONFIGS = [
    {
        'jurisdiction': 'federal',
        'data_type': 'bills',
        'url': 'https://www.congress.gov/search?q=%7B%22source%22%3A%22legislation%22%7D',
        'js_code': '''
            // Wait for bill listings to load
            await new Promise(resolve => setTimeout(resolve, 3000));
        ''',
        'wait_for': '.item',
        'page_timeout': 60000
    },
    {
        'jurisdiction': 'federal',
        'data_type': 'members',
        'url': 'https://www.congress.gov/members',
        'js_code': '''
            // Wait for member listings
            await new Promise(resolve => setTimeout(resolve, 2000));
        ''',
        'wait_for': '.member-container',
        'page_timeout': 45000
    },
    {
        'jurisdiction': 'nys',
        'data_type': 'bills',
        'url': 'https://www.nysenate.gov/search/legislation',
        'js_code': '''
            // Wait for NY Senate bill listings
            await new Promise(resolve => setTimeout(resolve, 2500));
        ''',
        'wait_for': '.bill-item',
        'page_timeout': 50000
    },
    {
        'jurisdiction': 'nys',
        'data_type': 'members',
        'url': 'https://www.nysenate.gov/senators-committees',
        'js_code': '''
            // Wait for senator listings
            await new Promise(resolve => setTimeout(resolve, 2000));
        ''',
        'wait_for': '.senator-card',
        'page_timeout': 40000
    }
]


if __name__ == "__main__":
    # Example usage
    crew = WebCrawlingCrew()

    # Run crawling for all configured websites
    result = crew.crawl_all_sources(WEBSITE_CONFIGS)

    print("Crawling completed!")
    print(json.dumps(result, indent=2))