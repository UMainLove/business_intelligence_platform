"""
Focused tests for web_tools.py to achieve 95%+ coverage.
"""

from datetime import datetime

from src.tools.web_tools import WebSearchTool, create_web_search_tool_spec, web_search_executor


class TestWebSearchTool:
    """Test WebSearchTool class."""

    def test_initialization(self):
        """Test WebSearchTool initialization."""
        search_tool = WebSearchTool()

        assert search_tool.search_history is not None
        assert isinstance(search_tool.search_history, list)
        assert len(search_tool.search_history) == 0

    def test_search_companies(self):
        """Test search_companies method."""
        search_tool = WebSearchTool()

        company_name = "TechCorp"
        location = "San Francisco"
        result = search_tool.search_companies(company_name, location)

        assert isinstance(result, dict)
        assert result["company"] == company_name
        assert result["location"] == location
        assert "results" in result
        assert "search_time" in result
        assert result["query_type"] == "company_search"

        # Check results structure
        results = result["results"]
        assert len(results) == 2

        result1 = results[0]
        assert "title" in result1
        assert "snippet" in result1
        assert "url" in result1
        assert "type" in result1
        assert company_name in result1["title"]
        assert result1["type"] == "company_profile"

        result2 = results[1]
        assert result2["type"] == "financial_data"

        # Check search history updated
        assert len(search_tool.search_history) == 1
        assert search_tool.search_history[0] == result

    def test_search_companies_no_location(self):
        """Test search_companies without location."""
        search_tool = WebSearchTool()

        result = search_tool.search_companies("TestCompany")

        assert result["company"] == "TestCompany"
        assert result["location"] == ""

    def test_search_market_trends(self):
        """Test search_market_trends method."""
        search_tool = WebSearchTool()

        industry = "FinTech"
        timeframe = "2y"
        result = search_tool.search_market_trends(industry, timeframe)

        assert isinstance(result, dict)
        assert result["industry"] == industry
        assert result["timeframe"] == timeframe
        assert "trends" in result
        assert "market_size" in result
        assert "growth_rate" in result
        assert "search_time" in result

        # Check trends structure
        trends = result["trends"]
        assert len(trends) == 3

        trend1 = trends[0]
        assert "trend" in trend1
        assert "impact" in trend1
        assert "description" in trend1
        assert "source" in trend1
        assert industry in trend1["description"]

        # Check different impact levels
        impacts = [trend["impact"] for trend in trends]
        assert "High" in impacts
        assert "Medium" in impacts

        # Check search history updated
        assert len(search_tool.search_history) == 1

    def test_search_market_trends_default_timeframe(self):
        """Test search_market_trends with default timeframe."""
        search_tool = WebSearchTool()

        result = search_tool.search_market_trends("SaaS")

        assert result["timeframe"] == "1y"

    def test_search_competitors(self):
        """Test search_competitors method."""
        search_tool = WebSearchTool()

        business_idea = "AI Analytics Platform"
        target_market = "Enterprise B2B"
        result = search_tool.search_competitors(business_idea, target_market)

        assert isinstance(result, dict)
        assert result["business_idea"] == business_idea
        assert result["target_market"] == target_market
        assert "competitors" in result
        assert "market_concentration" in result
        assert "barriers_to_entry" in result
        assert "search_time" in result

        # Check competitors structure
        competitors = result["competitors"]
        assert len(competitors) == 2

        competitor1 = competitors[0]
        assert "name" in competitor1
        assert "description" in competitor1
        assert "market_share" in competitor1
        assert "strengths" in competitor1
        assert "weaknesses" in competitor1
        assert "funding" in competitor1
        assert "url" in competitor1

        assert competitor1["name"] == "Competitor A"
        assert isinstance(competitor1["strengths"], list)
        assert isinstance(competitor1["weaknesses"], list)
        assert len(competitor1["strengths"]) > 0
        assert len(competitor1["weaknesses"]) > 0

        competitor2 = competitors[1]
        assert competitor2["name"] == "Competitor B"

        # Check market analysis
        assert isinstance(result["market_concentration"], str)
        assert isinstance(result["barriers_to_entry"], list)
        assert len(result["barriers_to_entry"]) > 0

        # Check search history updated
        assert len(search_tool.search_history) == 1

    def test_search_regulations(self):
        """Test search_regulations method."""
        search_tool = WebSearchTool()

        industry = "Healthcare"
        region = "EU"
        result = search_tool.search_regulations(industry, region)

        assert isinstance(result, dict)
        assert result["industry"] == industry
        assert result["region"] == region
        assert "regulations" in result
        assert "compliance_checklist" in result
        assert "search_time" in result

        # Check regulations structure
        regulations = result["regulations"]
        assert len(regulations) == 2

        regulation1 = regulations[0]
        assert "regulation" in regulation1
        assert "description" in regulation1
        assert "compliance_level" in regulation1
        assert "penalties" in regulation1
        assert "implementation_date" in regulation1

        assert regulation1["regulation"] == "Data Protection Regulation"
        assert regulation1["compliance_level"] == "Mandatory"
        assert industry in regulation1["description"]

        regulation2 = regulations[1]
        assert regulation2["regulation"] == "Industry-Specific Licensing"
        assert "cost" in regulation2
        assert "renewal_period" in regulation2

        # Check compliance checklist
        checklist = result["compliance_checklist"]
        assert isinstance(checklist, list)
        assert len(checklist) > 0
        assert all(isinstance(item, str) for item in checklist)

        # Check search history updated
        assert len(search_tool.search_history) == 1

    def test_search_funding_landscape(self):
        """Test search_funding_landscape method."""
        search_tool = WebSearchTool()

        industry = "Crypto"
        stage = "Series A"
        result = search_tool.search_funding_landscape(industry, stage)

        assert isinstance(result, dict)
        assert result["industry"] == industry
        assert result["stage"] == stage
        assert "funding_trends" in result
        assert "active_investors" in result
        assert "funding_advice" in result
        assert "search_time" in result

        # Check funding trends structure
        funding_trends = result["funding_trends"]
        assert len(funding_trends) == 1

        trend = funding_trends[0]
        assert "year" in trend
        assert "total_funding" in trend
        assert "deal_count" in trend
        assert "average_deal_size" in trend
        assert "top_investors" in trend

        assert trend["year"] == "2024"
        assert isinstance(trend["top_investors"], list)
        assert len(trend["top_investors"]) == 3

        # Check active investors structure
        investors = result["active_investors"]
        assert len(investors) == 1

        investor = investors[0]
        assert "name" in investor
        assert "focus" in investor
        assert "check_size" in investor
        assert "stage_preference" in investor
        assert "portfolio_companies" in investor

        assert investor["name"] == "Tech Ventures"
        assert industry in investor["focus"]
        assert investor["stage_preference"] == stage

        # Check funding advice
        advice = result["funding_advice"]
        assert isinstance(advice, list)
        assert len(advice) == 3
        for item in advice:
            assert isinstance(item, str)
            assert len(item) > 0

        # Check search history updated
        assert len(search_tool.search_history) == 1

    def test_get_search_history_empty(self):
        """Test get_search_history when empty."""
        search_tool = WebSearchTool()

        history = search_tool.get_search_history()

        assert isinstance(history, list)
        assert len(history) == 0

    def test_get_search_history_with_data(self):
        """Test get_search_history with search data."""
        search_tool = WebSearchTool()

        # Perform several searches
        search_tool.search_companies("Company1")
        search_tool.search_market_trends("Industry1")
        search_tool.search_competitors("Idea1", "Market1")

        history = search_tool.get_search_history()

        assert len(history) == 3
        assert history[0]["query_type"] == "company_search"
        assert history[1]["industry"] == "Industry1"
        assert history[2]["business_idea"] == "Idea1"

    def test_get_search_history_limit(self):
        """Test get_search_history respects 10-item limit."""
        search_tool = WebSearchTool()

        # Perform more than 10 searches
        for i in range(15):
            search_tool.search_companies(f"Company{i}")

        history = search_tool.get_search_history()

        assert len(history) == 10
        # Should return the last 10 searches
        assert history[0]["company"] == "Company5"  # 15 - 10 = 5
        assert history[9]["company"] == "Company14"

    def test_search_time_format(self):
        """Test that search_time is properly formatted."""
        search_tool = WebSearchTool()

        result = search_tool.search_companies("TestCompany")
        search_time = result["search_time"]

        # Should be ISO format datetime string
        assert isinstance(search_time, str)
        # Should be parseable as datetime
        parsed_dt = datetime.fromisoformat(
            search_time.replace("Z", "+00:00") if search_time.endswith("Z") else search_time
        )
        assert isinstance(parsed_dt, datetime)

    def test_multiple_searches_history_order(self):
        """Test that multiple searches maintain correct order in history."""
        search_tool = WebSearchTool()

        # Perform searches in specific order
        result1 = search_tool.search_companies("FirstCompany")
        result2 = search_tool.search_market_trends("SecondIndustry")
        result3 = search_tool.search_competitors("ThirdIdea", "ThirdMarket")

        history = search_tool.get_search_history()

        assert len(history) == 3
        assert history[0] == result1
        assert history[1] == result2
        assert history[2] == result3


class TestWebSearchToolSpec:
    """Test web search tool specification."""

    def test_create_web_search_tool_spec(self):
        """Test create_web_search_tool_spec function."""
        spec = create_web_search_tool_spec()

        assert isinstance(spec, dict)
        assert "name" in spec
        assert "description" in spec
        assert "parameters" in spec

        assert spec["name"] == "web_search"

        # Check parameters structure
        params = spec["parameters"]
        assert params["type"] == "object"
        assert "properties" in params
        assert "required" in params

        properties = params["properties"]
        assert "search_type" in properties
        assert "params" in properties

        # Check search_type enum
        search_type = properties["search_type"]
        assert search_type["type"] == "string"
        assert "enum" in search_type
        expected_types = ["companies", "market_trends", "competitors", "regulations", "funding"]
        assert search_type["enum"] == expected_types

        # Check required fields
        assert params["required"] == ["search_type", "params"]


class TestWebSearchExecutor:
    """Test web_search_executor function."""

    def test_companies_search_executor(self):
        """Test web_search_executor for companies search."""
        result = web_search_executor(
            "companies", {"company_name": "ExecutorTestCorp", "location": "New York"}
        )

        assert isinstance(result, dict)
        assert result["company"] == "ExecutorTestCorp"
        assert result["location"] == "New York"
        assert result["query_type"] == "company_search"

    def test_companies_search_executor_no_location(self):
        """Test web_search_executor for companies search without location."""
        result = web_search_executor("companies", {"company_name": "NoLocationCorp"})

        assert result["company"] == "NoLocationCorp"
        assert result["location"] == ""

    def test_market_trends_executor(self):
        """Test web_search_executor for market trends."""
        result = web_search_executor(
            "market_trends", {"industry": "ExecutorIndustry", "timeframe": "3y"}
        )

        assert result["industry"] == "ExecutorIndustry"
        assert result["timeframe"] == "3y"
        assert "trends" in result

    def test_market_trends_executor_default_timeframe(self):
        """Test web_search_executor for market trends with default timeframe."""
        result = web_search_executor("market_trends", {"industry": "DefaultIndustry"})

        assert result["industry"] == "DefaultIndustry"
        assert result["timeframe"] == "1y"

    def test_competitors_search_executor(self):
        """Test web_search_executor for competitors search."""
        result = web_search_executor(
            "competitors", {"business_idea": "ExecutorIdea", "target_market": "ExecutorMarket"}
        )

        assert result["business_idea"] == "ExecutorIdea"
        assert result["target_market"] == "ExecutorMarket"
        assert "competitors" in result

    def test_regulations_search_executor(self):
        """Test web_search_executor for regulations search."""
        result = web_search_executor(
            "regulations", {"industry": "ExecutorRegIndustry", "region": "ExecutorRegion"}
        )

        assert result["industry"] == "ExecutorRegIndustry"
        assert result["region"] == "ExecutorRegion"
        assert "regulations" in result

    def test_funding_search_executor(self):
        """Test web_search_executor for funding search."""
        result = web_search_executor(
            "funding", {"industry": "ExecutorFundingIndustry", "stage": "ExecutorStage"}
        )

        assert result["industry"] == "ExecutorFundingIndustry"
        assert result["stage"] == "ExecutorStage"
        assert "funding_trends" in result

    def test_unknown_search_type_executor(self):
        """Test web_search_executor with unknown search type."""
        result = web_search_executor("unknown_type", {})

        assert "error" in result
        assert "Unknown search type: unknown_type" in result["error"]


class TestIntegration:
    """Test integration scenarios."""

    def test_full_web_search_workflow(self):
        """Test complete web search workflow."""
        search_tool = WebSearchTool()

        # 1. Search for company information
        company_result = search_tool.search_companies("WorkflowCorp", "Silicon Valley")
        assert company_result["company"] == "WorkflowCorp"

        # 2. Search market trends for the industry
        trends_result = search_tool.search_market_trends("Tech", "2y")
        assert trends_result["industry"] == "Tech"

        # 3. Analyze competitors
        competitors_result = search_tool.search_competitors("AI Platform", "Enterprise")
        assert competitors_result["business_idea"] == "AI Platform"

        # 4. Check regulations
        regulations_result = search_tool.search_regulations("Tech", "US")
        assert regulations_result["industry"] == "Tech"

        # 5. Research funding landscape
        funding_result = search_tool.search_funding_landscape("Tech", "Series B")
        assert funding_result["industry"] == "Tech"

        # Check search history contains all searches
        history = search_tool.get_search_history()
        assert len(history) == 5

        # Verify all searches are tracked
        search_types = []
        for search in history:
            if "query_type" in search:
                search_types.append(search["query_type"])
            elif "trends" in search:
                search_types.append("market_trends")
            elif "competitors" in search:
                search_types.append("competitors")
            elif "regulations" in search:
                search_types.append("regulations")
            elif "funding_trends" in search:
                search_types.append("funding")

        assert "company_search" in search_types

    def test_executor_integration(self):
        """Test web_search_executor integration with all search types."""
        # Test all supported search types
        test_cases = [
            ("companies", {"company_name": "TestCorp"}),
            ("market_trends", {"industry": "TestIndustry"}),
            ("competitors", {"business_idea": "TestIdea", "target_market": "TestMarket"}),
            ("regulations", {"industry": "TestRegIndustry", "region": "TestRegion"}),
            ("funding", {"industry": "TestFundIndustry", "stage": "TestStage"}),
        ]

        for search_type, params in test_cases:
            result = web_search_executor(search_type, params)
            assert isinstance(result, dict)
            assert "search_time" in result

            # Verify no errors
            assert "error" not in result

    def test_search_result_consistency(self):
        """Test that search results are consistent across calls."""
        search_tool = WebSearchTool()

        # Same search should return similar structure
        result1 = search_tool.search_companies("ConsistencyTest")
        result2 = search_tool.search_companies("ConsistencyTest")

        # Structure should be the same
        assert result1.keys() == result2.keys()
        assert len(result1["results"]) == len(result2["results"])
        assert result1["query_type"] == result2["query_type"]

        # Content should reference the same company
        assert result1["company"] == result2["company"]

    def test_data_structure_validation(self):
        """Test that all search methods return properly structured data."""
        search_tool = WebSearchTool()

        # Test all search methods
        results = [
            search_tool.search_companies("ValidationCorp"),
            search_tool.search_market_trends("ValidationIndustry"),
            search_tool.search_competitors("ValidationIdea", "ValidationMarket"),
            search_tool.search_regulations("ValidationRegIndustry", "ValidationRegion"),
            search_tool.search_funding_landscape("ValidationFundIndustry", "ValidationStage"),
        ]

        for result in results:
            assert isinstance(result, dict)
            assert "search_time" in result

            # Search time should be valid ISO format
            search_time = result["search_time"]
            parsed_dt = datetime.fromisoformat(
                search_time.replace("Z", "+00:00") if search_time.endswith("Z") else search_time
            )
            assert isinstance(parsed_dt, datetime)

    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        search_tool = WebSearchTool()

        # Test with empty strings
        result1 = search_tool.search_companies("")
        assert result1["company"] == ""

        result2 = search_tool.search_market_trends("")
        assert result2["industry"] == ""

        # Test with very long strings
        long_string = "x" * 1000
        result3 = search_tool.search_companies(long_string)
        assert result3["company"] == long_string

        # All should still return valid responses
        for result in [result1, result2, result3]:
            assert isinstance(result, dict)
            assert "search_time" in result

    def test_performance_multiple_searches(self):
        """Test performance with multiple rapid searches."""
        search_tool = WebSearchTool()

        # Perform many searches rapidly
        for i in range(20):
            result = search_tool.search_companies(f"PerfTest{i}")
            assert result["company"] == f"PerfTest{i}"

        # History should be limited to last 10
        history = search_tool.get_search_history()
        assert len(history) == 10

        # Should contain the last 10 searches
        for i, search in enumerate(history):
            expected_company = f"PerfTest{i + 10}"  # Last 10: PerfTest10 to PerfTest19
            assert search["company"] == expected_company

    def test_concurrent_access_simulation(self):
        """Test simulated concurrent access patterns."""
        search_tool = WebSearchTool()

        # Simulate interleaved search types
        searches = [
            ("companies", "ConcurrentCorp1"),
            ("market_trends", "ConcurrentIndustry1"),
            ("companies", "ConcurrentCorp2"),
            ("competitors", "ConcurrentIdea1"),
            ("companies", "ConcurrentCorp3"),
        ]

        results = []
        for search_type, param in searches:
            if search_type == "companies":
                result = search_tool.search_companies(param)
            elif search_type == "market_trends":
                result = search_tool.search_market_trends(param)
            elif search_type == "competitors":
                result = search_tool.search_competitors(param, "TestMarket")

            results.append(result)

        # All searches should complete successfully
        assert len(results) == 5

        # History should contain all searches
        history = search_tool.get_search_history()
        assert len(history) == 5
