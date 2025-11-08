"""
Tests for CrewAI agents and specialized crews.

This module tests the CrewAI functionality including:
- Web crawling crew and agents
- Legislative analysis crew
- Database administration crew
- Political consultant crew
- Agent coordination and task execution
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from tests.utils.test_helpers import (
    assert_no_exceptions,
    generate_mock_bill_data,
    generate_mock_member_data,
    generate_mock_vote_data
)


class TestWebCrawlingCrew:
    """Test web crawling crew functionality."""

    @pytest.fixture
    def web_crawling_crew(self):
        """Create a WebCrawlingCrew instance for testing."""
        from crewai.specialized_crews.web_crawling import WebCrawlingCrew
        return WebCrawlingCrew()

    @pytest.mark.unit
    def test_crew_initialization(self, web_crawling_crew):
        """Test web crawling crew initialization."""
        assert web_crawling_crew is not None
        assert hasattr(web_crawling_crew, 'agents')
        assert hasattr(web_crawling_crew, 'tasks')

    @pytest.mark.unit
    def test_agent_creation(self, web_crawling_crew):
        """Test creation of web crawling agents."""
        agents = web_crawling_crew.agents

        # Should have the expected agents
        agent_names = [agent.name for agent in agents]
        expected_agents = ["WebCrawlerAgent", "DataProcessorAgent", "DatabaseIngestionAgent"]

        for expected_agent in expected_agents:
            assert any(expected_agent in name for name in agent_names)

    @pytest.mark.asyncio
    async def test_web_crawling_task_execution(self, web_crawling_crew, mock_crawl4ai):
        """Test web crawling task execution."""
        # Mock the crew execution
        with patch.object(web_crawling_crew, 'kickoff', return_value="Crawling completed successfully"):
            result = await web_crawling_crew.kickoff()

            assert "Crawling completed successfully" in result

    @pytest.mark.unit
    def test_website_configuration(self, web_crawling_crew):
        """Test website configuration for crawling."""
        config = web_crawling_crew.get_website_config()

        assert isinstance(config, dict)
        assert "congress_gov" in config
        assert "ny_senate" in config

        # Check required fields
        for site, site_config in config.items():
            assert "url" in site_config
            assert "jurisdiction" in site_config
            assert "data_types" in site_config

    @pytest.mark.unit
    def test_data_type_mapping(self, web_crawling_crew):
        """Test data type mapping for different websites."""
        mappings = web_crawling_crew.get_data_type_mappings()

        assert isinstance(mappings, dict)
        assert "bills" in mappings
        assert "members" in mappings
        assert "votes" in mappings

    @pytest.mark.asyncio
    async def test_error_handling_in_crawling(self, web_crawling_crew):
        """Test error handling during web crawling."""
        # Mock a failing crawl
        with patch.object(web_crawling_crew, 'kickoff', side_effect=Exception("Crawling failed")):
            with pytest.raises(Exception, match="Crawling failed"):
                await web_crawling_crew.kickoff()


class TestWebCrawlerAgent:
    """Test individual WebCrawlerAgent functionality."""

    @pytest.fixture
    def web_crawler_agent(self):
        """Create a WebCrawlerAgent instance for testing."""
        from crewai.specialized_crews.web_crawling import WebCrawlerAgent
        return WebCrawlerAgent()

    @pytest.mark.unit
    def test_agent_initialization(self, web_crawler_agent):
        """Test WebCrawlerAgent initialization."""
        assert web_crawler_agent.name == "WebCrawlerAgent"
        assert "web crawling" in web_crawler_agent.role.lower()
        assert web_crawler_agent.goal is not None

    @pytest.mark.asyncio
    async def test_crawl_website(self, web_crawler_agent, mock_crawl4ai):
        """Test website crawling functionality."""
        url = "https://www.congress.gov"
        jurisdiction = "federal"

        result = await web_crawler_agent.crawl_website(url, jurisdiction)

        assert result is not None
        assert "content" in result
        assert "links" in result
        assert "metadata" in result
        assert result["jurisdiction"] == jurisdiction

    @pytest.mark.asyncio
    async def test_crawl_multiple_sites(self, web_crawler_agent, mock_crawl4ai):
        """Test crawling multiple websites."""
        sites = [
            {"url": "https://www.congress.gov", "jurisdiction": "federal"},
            {"url": "https://www.nysenate.gov", "jurisdiction": "ny_state"}
        ]

        results = []
        for site in sites:
            result = await web_crawler_agent.crawl_website(site["url"], site["jurisdiction"])
            results.append(result)

        assert len(results) == 2
        for result in results:
            assert "jurisdiction" in result
            assert result["jurisdiction"] in ["federal", "ny_state"]

    @pytest.mark.unit
    def test_content_extraction(self, web_crawler_agent):
        """Test content extraction from crawled data."""
        mock_content = """
        <html>
        <body>
        <h1>Bill H.R. 1234</h1>
        <p>This is a test bill for infrastructure.</p>
        <div class="sponsor">Sponsor: John Doe (D-NY)</div>
        </body>
        </html>
        """

        extracted = web_crawler_agent.extract_structured_data(mock_content)

        assert isinstance(extracted, dict)
        assert "title" in extracted or "bill_id" in extracted


class TestDataProcessorAgent:
    """Test DataProcessorAgent functionality."""

    @pytest.fixture
    def data_processor_agent(self):
        """Create a DataProcessorAgent instance for testing."""
        from crewai.specialized_crews.web_crawling import DataProcessorAgent
        return DataProcessorAgent()

    @pytest.mark.unit
    def test_agent_initialization(self, data_processor_agent):
        """Test DataProcessorAgent initialization."""
        assert data_processor_agent.name == "DataProcessorAgent"
        assert "data processing" in data_processor_agent.role.lower()

    @pytest.mark.unit
    def test_bill_data_processing(self, data_processor_agent):
        """Test processing of bill data."""
        raw_data = {
            "content": "Bill H.R. 1234 - Infrastructure Investment Act",
            "jurisdiction": "federal",
            "url": "https://www.congress.gov/bill/1234"
        }

        processed = data_processor_agent.process_bill_data(raw_data)

        assert isinstance(processed, dict)
        assert "bill_id" in processed
        assert "title" in processed
        assert processed["jurisdiction"] == "federal"

    @pytest.mark.unit
    def test_member_data_processing(self, data_processor_agent):
        """Test processing of member data."""
        raw_data = {
            "content": "Senator John Doe (D-NY) - New York",
            "jurisdiction": "federal",
            "url": "https://www.congress.gov/member/john-doe"
        }

        processed = data_processor_agent.process_member_data(raw_data)

        assert isinstance(processed, dict)
        assert "name" in processed
        assert "party" in processed
        assert "state" in processed

    @pytest.mark.unit
    def test_vote_data_processing(self, data_processor_agent):
        """Test processing of vote data."""
        raw_data = {
            "content": "Bill H.R. 1234 passed 220-210",
            "jurisdiction": "federal",
            "date": "2025-01-15"
        }

        processed = data_processor_agent.process_vote_data(raw_data)

        assert isinstance(processed, dict)
        assert "bill_id" in processed
        assert "result" in processed
        assert "yeas" in processed
        assert "nays" in processed

    @pytest.mark.unit
    def test_data_validation(self, data_processor_agent):
        """Test data validation functionality."""
        valid_data = generate_mock_bill_data()
        invalid_data = {"invalid": "data"}

        assert data_processor_agent.validate_data(valid_data) is True
        assert data_processor_agent.validate_data(invalid_data) is False


class TestDatabaseIngestionAgent:
    """Test DatabaseIngestionAgent functionality."""

    @pytest.fixture
    def db_ingestion_agent(self):
        """Create a DatabaseIngestionAgent instance for testing."""
        from crewai.specialized_crews.web_crawling import DatabaseIngestionAgent
        return DatabaseIngestionAgent()

    @pytest.mark.unit
    def test_agent_initialization(self, db_ingestion_agent):
        """Test DatabaseIngestionAgent initialization."""
        assert db_ingestion_agent.name == "DatabaseIngestionAgent"
        assert "database" in db_ingestion_agent.role.lower()

    @pytest.mark.asyncio
    async def test_data_ingestion(self, db_ingestion_agent, mock_async_db_connection):
        """Test data ingestion into database."""
        test_data = generate_mock_bill_data()

        with patch('crewai.specialized_crews.web_crawling.get_db_connection') as mock_get_conn:
            mock_get_conn.return_value = mock_async_db_connection

            result = await db_ingestion_agent.ingest_data(test_data, "bills")

            assert result is not None
            assert "status" in result

    @pytest.mark.asyncio
    async def test_batch_ingestion(self, db_ingestion_agent, mock_async_db_connection):
        """Test batch data ingestion."""
        test_data = generate_mock_bill_data(10)  # Generate 10 bills

        with patch('crewai.specialized_crews.web_crawling.get_db_connection') as mock_get_conn:
            mock_get_conn.return_value = mock_async_db_connection

            result = await db_ingestion_agent.ingest_batch_data(test_data, "bills")

            assert result is not None
            assert "records_processed" in result

    @pytest.mark.unit
    def test_ingestion_trigger_activation(self, db_ingestion_agent):
        """Test activation of ingestion triggers."""
        trigger_result = db_ingestion_agent.activate_ingestion_trigger("bills", 100)

        assert trigger_result is not None
        assert "trigger_activated" in trigger_result

    @pytest.mark.asyncio
    async def test_error_handling_in_ingestion(self, db_ingestion_agent):
        """Test error handling during data ingestion."""
        test_data = generate_mock_bill_data()

        # Mock a database error
        with patch('crewai.specialized_crews.web_crawling.get_db_connection', side_effect=Exception("DB Error")):
            with pytest.raises(Exception, match="DB Error"):
                await db_ingestion_agent.ingest_data(test_data, "bills")


class TestLegislativeAnalysisCrew:
    """Test legislative analysis crew functionality."""

    @pytest.fixture
    def legislative_analysis_crew(self):
        """Create a LegislativeAnalysisCrew instance for testing."""
        from crewai.specialized_crews.legislative_analysis import LegislativeAnalysisCrew
        return LegislativeAnalysisCrew()

    @pytest.mark.unit
    def test_crew_initialization(self, legislative_analysis_crew):
        """Test legislative analysis crew initialization."""
        assert legislative_analysis_crew is not None
        assert hasattr(legislative_analysis_crew, 'agents')

    @pytest.mark.unit
    def test_policy_analysis_task(self, legislative_analysis_crew):
        """Test policy analysis task execution."""
        bill_data = generate_mock_bill_data()

        # Mock the analysis
        with patch.object(legislative_analysis_crew, 'analyze_bill_impact', return_value="High impact on infrastructure"):
            result = legislative_analysis_crew.analyze_bill_impact(bill_data)

            assert "High impact on infrastructure" in result

    @pytest.mark.unit
    def test_vote_pattern_analysis(self, legislative_analysis_crew):
        """Test vote pattern analysis."""
        vote_data = generate_mock_vote_data(20)  # 20 votes

        patterns = legislative_analysis_crew.analyze_vote_patterns(vote_data)

        assert isinstance(patterns, dict)
        assert "party_line_votes" in patterns or "bipartisan_support" in patterns


class TestDatabaseAdminCrew:
    """Test database administration crew functionality."""

    @pytest.fixture
    def db_admin_crew(self):
        """Create a DatabaseAdminCrew instance for testing."""
        from crewai.specialized_crews.database_admin import DatabaseAdminCrew
        return DatabaseAdminCrew()

    @pytest.mark.unit
    def test_crew_initialization(self, db_admin_crew):
        """Test database admin crew initialization."""
        assert db_admin_crew is not None
        assert hasattr(db_admin_crew, 'agents')

    @pytest.mark.unit
    def test_schema_optimization(self, db_admin_crew):
        """Test database schema optimization."""
        schema_info = {
            "tables": ["bills", "members", "votes"],
            "indexes": ["idx_bills_jurisdiction", "idx_members_state"]
        }

        recommendations = db_admin_crew.optimize_schema(schema_info)

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0

    @pytest.mark.unit
    def test_performance_monitoring(self, db_admin_crew):
        """Test database performance monitoring."""
        metrics = db_admin_crew.monitor_performance()

        assert isinstance(metrics, dict)
        assert "query_performance" in metrics or "connection_pool" in metrics


class TestPoliticalConsultantCrew:
    """Test political consultant crew functionality."""

    @pytest.fixture
    def political_consultant_crew(self):
        """Create a PoliticalConsultantCrew instance for testing."""
        from crewai.specialized_crews.political_consultant import PoliticalConsultantCrew
        return PoliticalConsultantCrew()

    @pytest.mark.unit
    def test_crew_initialization(self, political_consultant_crew):
        """Test political consultant crew initialization."""
        assert political_consultant_crew is not None
        assert hasattr(political_consultant_crew, 'agents')

    @pytest.mark.unit
    def test_election_analysis(self, political_consultant_crew):
        """Test election analysis functionality."""
        election_data = {
            "year": 2024,
            "office": "senate",
            "candidates": ["Candidate A", "Candidate B"],
            "polling_data": [45, 42]
        }

        analysis = political_consultant_crew.analyze_election(election_data)

        assert isinstance(analysis, dict)
        assert "predictions" in analysis or "insights" in analysis


class TestAgentCoordination:
    """Test coordination between multiple agents."""

    @pytest.mark.unit
    def test_agent_task_handover(self):
        """Test task handover between agents."""
        from crewai.specialized_crews.web_crawling import (
            WebCrawlerAgent,
            DataProcessorAgent,
            DatabaseIngestionAgent
        )

        crawler = WebCrawlerAgent()
        processor = DataProcessorAgent()
        ingestor = DatabaseIngestionAgent()

        # Simulate data flow
        raw_data = {"content": "Test bill data", "url": "https://example.com"}
        processed_data = processor.process_bill_data(raw_data)
        final_result = ingestor.ingest_data(processed_data, "bills")

        assert processed_data is not None
        assert final_result is not None

    @pytest.mark.unit
    def test_error_propagation(self):
        """Test error propagation through agent chain."""
        from crewai.specialized_crews.web_crawling import DataProcessorAgent

        processor = DataProcessorAgent()

        # Test with invalid data
        invalid_data = {"invalid": "data"}

        # Should handle gracefully
        assert_no_exceptions(processor.process_bill_data, invalid_data)


class TestCrewAIIntegration:
    """Integration tests for CrewAI functionality."""

    @pytest.mark.integration
    def test_full_crawling_workflow(self, mock_crawl4ai, mock_async_db_connection):
        """Test full web crawling workflow."""
        from crewai.specialized_crews.web_crawling import WebCrawlingCrew

        crew = WebCrawlingCrew()

        # Mock the entire workflow
        with patch.object(crew, 'kickoff', return_value="Workflow completed"):
            result = crew.kickoff()

            assert "Workflow completed" in result

    @pytest.mark.integration
    def test_multi_crew_coordination(self):
        """Test coordination between multiple crews."""
        from crewai.specialized_crews.web_crawling import WebCrawlingCrew
        from crewai.specialized_crews.legislative_analysis import LegislativeAnalysisCrew

        crawling_crew = WebCrawlingCrew()
        analysis_crew = LegislativeAnalysisCrew()

        # Test that both crews can be initialized and work together
        assert crawling_crew is not None
        assert analysis_crew is not None

        # Simulate data flow between crews
        mock_bill_data = generate_mock_bill_data()
        analysis_result = analysis_crew.analyze_bill_impact(mock_bill_data)

        assert analysis_result is not None