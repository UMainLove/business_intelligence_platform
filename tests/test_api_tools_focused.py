"""
Focused tests for api_tools.py to achieve 95%+ coverage.
"""

from datetime import datetime
from unittest.mock import patch

from src.tools.api_tools import ExternalAPITool, api_tool_executor, create_api_tool_spec


class TestExternalAPITool:
    """Test ExternalAPITool class."""

    def test_initialization(self):
        """Test ExternalAPITool initialization."""
        api_tool = ExternalAPITool()

        assert api_tool.api_configs is not None
        assert "crunchbase" in api_tool.api_configs
        assert "clearbit" in api_tool.api_configs
        assert "alpha_vantage" in api_tool.api_configs

        # Check structure of api configs
        assert "base_url" in api_tool.api_configs["crunchbase"]
        assert "api_key" in api_tool.api_configs["crunchbase"]

    def test_search_company_crunchbase(self):
        """Test search_company_crunchbase method."""
        api_tool = ExternalAPITool()

        company_name = "TestCompany"
        result = api_tool.search_company_crunchbase(company_name)

        assert isinstance(result, dict)
        assert result["company"] == company_name
        assert result["api_source"] == "crunchbase"
        assert "data" in result
        assert "retrieved_at" in result
        assert result["api_status"] == "success"

        # Check data structure
        data = result["data"]
        assert "founded" in data
        assert "headquarters" in data
        assert "employees" in data
        assert "industry" in data
        assert "funding_rounds" in data
        assert "total_funding" in data
        assert "valuation" in data
        assert "status" in data
        assert "description" in data
        assert "website" in data
        assert "competitors" in data

        # Check funding rounds structure
        assert len(data["funding_rounds"]) == 2
        round1 = data["funding_rounds"][0]
        assert "round" in round1
        assert "amount" in round1
        assert "date" in round1
        assert "investors" in round1

    def test_get_market_data_alpha_vantage(self):
        """Test get_market_data_alpha_vantage method."""
        api_tool = ExternalAPITool()

        symbol = "AAPL"
        result = api_tool.get_market_data_alpha_vantage(symbol)

        assert isinstance(result, dict)
        assert result["symbol"] == symbol
        assert result["api_source"] == "alpha_vantage"
        assert "data" in result
        assert result["api_status"] == "success"

        # Check data structure
        data = result["data"]
        assert "current_price" in data
        assert "change" in data
        assert "volume" in data
        assert "market_cap" in data
        assert "pe_ratio" in data
        assert "dividend_yield" in data
        assert "52_week_high" in data
        assert "52_week_low" in data
        assert "analyst_rating" in data
        assert "price_target" in data

    def test_enrich_company_clearbit(self):
        """Test enrich_company_clearbit method."""
        api_tool = ExternalAPITool()

        domain = "example.com"
        result = api_tool.enrich_company_clearbit(domain)

        assert isinstance(result, dict)
        assert result["domain"] == domain
        assert result["api_source"] == "clearbit"
        assert "data" in result
        assert result["api_status"] == "success"

        # Check data structure
        data = result["data"]
        assert "name" in data
        assert "description" in data
        assert "employees" in data
        assert "annual_revenue" in data
        assert "industry" in data
        assert "sub_industry" in data
        assert "location" in data
        assert "founded" in data
        assert "technologies" in data
        assert "social_media" in data
        assert "tags" in data
        assert "phone" in data
        assert "email_pattern" in data

        # Check social media structure
        social = data["social_media"]
        assert "twitter" in social
        assert "linkedin" in social

    def test_search_patents(self):
        """Test search_patents method."""
        api_tool = ExternalAPITool()

        company_name = "TechCorp"
        keywords = ["machine learning", "AI"]
        result = api_tool.search_patents(company_name, keywords)

        assert isinstance(result, dict)
        assert result["company"] == company_name
        assert result["keywords"] == keywords
        assert result["api_source"] == "uspto"
        assert "data" in result
        assert result["api_status"] == "success"

        # Check data structure
        data = result["data"]
        assert "total_patents" in data
        assert "active_patents" in data
        assert "pending_applications" in data
        assert "patents" in data
        assert "patent_categories" in data
        assert "innovation_score" in data

        # Check patents structure
        patents = data["patents"]
        assert len(patents) == 2
        patent1 = patents[0]
        assert "patent_number" in patent1
        assert "title" in patent1
        assert "filing_date" in patent1
        assert "issue_date" in patent1
        assert "status" in patent1
        assert "inventors" in patent1

    def test_search_patents_without_keywords(self):
        """Test search_patents method without keywords."""
        api_tool = ExternalAPITool()

        company_name = "TechCorp"
        result = api_tool.search_patents(company_name)

        assert isinstance(result, dict)
        assert result["company"] == company_name
        assert result["keywords"] == []  # Should default to empty list

    def test_get_industry_regulations(self):
        """Test get_industry_regulations method."""
        api_tool = ExternalAPITool()

        industry = "FinTech"
        region = "EU"
        result = api_tool.get_industry_regulations(industry, region)

        assert isinstance(result, dict)
        assert result["industry"] == industry
        assert result["region"] == region
        assert result["api_source"] == "regulatory_database"
        assert "data" in result
        assert result["api_status"] == "success"

        # Check data structure
        data = result["data"]
        assert "primary_regulations" in data
        assert "licensing_requirements" in data
        assert "compliance_checklist" in data
        assert "regulatory_risk_score" in data

        # Check regulations structure
        regulations = data["primary_regulations"]
        assert len(regulations) == 2
        reg1 = regulations[0]
        assert "regulation" in reg1
        assert "description" in reg1
        assert "applicability" in reg1
        assert "compliance_cost" in reg1
        assert "penalties" in reg1
        assert "implementation_timeline" in reg1

    def test_get_industry_regulations_default_region(self):
        """Test get_industry_regulations with default region."""
        api_tool = ExternalAPITool()

        industry = "Software"
        result = api_tool.get_industry_regulations(industry)

        assert result["region"] == "US"  # Should default to US

    def test_get_funding_intelligence(self):
        """Test get_funding_intelligence method."""
        api_tool = ExternalAPITool()

        industry = "SaaS"
        stage = "Series B"
        result = api_tool.get_funding_intelligence(industry, stage)

        assert isinstance(result, dict)
        assert result["industry"] == industry
        assert result["stage"] == stage
        assert result["api_source"] == "funding_database"
        assert "data" in result
        assert result["api_status"] == "success"

        # Check data structure
        data = result["data"]
        assert "market_activity" in data
        assert "active_investors" in data
        assert "funding_trends" in data
        assert "valuation_multiples" in data

        # Check market activity structure
        market = data["market_activity"]
        assert "total_deals_ytd" in market
        assert "total_funding_ytd" in market
        assert "avg_deal_size" in market
        assert "median_valuation" in market
        assert "success_rate" in market

        # Check investors structure
        investors = data["active_investors"]
        assert len(investors) == 2
        investor1 = investors[0]
        assert "name" in investor1
        assert "type" in investor1
        assert "focus" in investor1
        assert "check_size" in investor1
        assert "portfolio_companies" in investor1
        assert "recent_investments" in investor1
        assert "contact" in investor1

    def test_get_funding_intelligence_default_stage(self):
        """Test get_funding_intelligence with default stage."""
        api_tool = ExternalAPITool()

        industry = "AI"
        result = api_tool.get_funding_intelligence(industry)

        assert result["stage"] == "Series A"  # Should default to Series A

    @patch("time.sleep")
    def test_batch_api_call(self, mock_sleep):
        """Test batch_api_call method."""
        api_tool = ExternalAPITool()

        requests_data = [
            {"api_type": "company_search", "params": {"company_name": "TestCorp"}},
            {"api_type": "market_data", "params": {"symbol": "TEST"}},
            {"api_type": "company_enrich", "params": {"domain": "test.com"}},
            {
                "api_type": "patent_search",
                "params": {"company_name": "PatentCorp", "keywords": ["AI"]},
            },
            {"api_type": "regulations", "params": {"industry": "Tech", "region": "EU"}},
            {"api_type": "funding_intel", "params": {"industry": "SaaS", "stage": "Seed"}},
        ]

        results = api_tool.batch_api_call(requests_data)

        assert isinstance(results, list)
        assert len(results) == 6

        # Check each result type
        assert results[0]["api_source"] == "crunchbase"
        assert results[1]["api_source"] == "alpha_vantage"
        assert results[2]["api_source"] == "clearbit"
        assert results[3]["api_source"] == "uspto"
        assert results[4]["api_source"] == "regulatory_database"
        assert results[5]["api_source"] == "funding_database"

        # Verify sleep was called for rate limiting
        assert mock_sleep.call_count == 6
        mock_sleep.assert_called_with(0.1)

    @patch("time.sleep")
    def test_batch_api_call_unknown_type(self, mock_sleep):
        """Test batch_api_call with unknown API type."""
        api_tool = ExternalAPITool()

        requests_data = [{"api_type": "unknown_api", "params": {}}]

        results = api_tool.batch_api_call(requests_data)

        assert len(results) == 1
        assert "error" in results[0]
        assert "Unknown API type: unknown_api" in results[0]["error"]

    @patch("time.sleep")
    def test_batch_api_call_missing_params(self, mock_sleep):
        """Test batch_api_call with missing params."""
        api_tool = ExternalAPITool()

        requests_data = [
            {
                "api_type": "company_search"
                # Missing params
            }
        ]

        results = api_tool.batch_api_call(requests_data)

        assert len(results) == 1
        # Should handle missing params gracefully
        assert results[0]["api_source"] == "crunchbase"


class TestAPIToolSpec:
    """Test API tool specification."""

    def test_create_api_tool_spec(self):
        """Test create_api_tool_spec function."""
        spec = create_api_tool_spec()

        assert isinstance(spec, dict)
        assert "name" in spec
        assert "description" in spec
        assert "parameters" in spec

        assert spec["name"] == "external_api"

        # Check parameters structure
        params = spec["parameters"]
        assert params["type"] == "object"
        assert "properties" in params
        assert "required" in params

        properties = params["properties"]
        assert "api_type" in properties
        assert "params" in properties

        # Check api_type enum
        api_type = properties["api_type"]
        assert api_type["type"] == "string"
        assert "enum" in api_type
        expected_types = [
            "company_search",
            "market_data",
            "company_enrich",
            "patent_search",
            "regulations",
            "funding_intel",
            "batch",
        ]
        assert api_type["enum"] == expected_types

        # Check required fields
        assert params["required"] == ["api_type", "params"]


class TestAPIToolExecutor:
    """Test api_tool_executor function."""

    def test_company_search_executor(self):
        """Test api_tool_executor for company search."""
        result = api_tool_executor("company_search", {"company_name": "TestCorp"})

        assert isinstance(result, dict)
        assert result["api_source"] == "crunchbase"
        assert result["company"] == "TestCorp"

    def test_market_data_executor(self):
        """Test api_tool_executor for market data."""
        result = api_tool_executor("market_data", {"symbol": "MSFT"})

        assert isinstance(result, dict)
        assert result["api_source"] == "alpha_vantage"
        assert result["symbol"] == "MSFT"

    def test_company_enrich_executor(self):
        """Test api_tool_executor for company enrichment."""
        result = api_tool_executor("company_enrich", {"domain": "microsoft.com"})

        assert isinstance(result, dict)
        assert result["api_source"] == "clearbit"
        assert result["domain"] == "microsoft.com"

    def test_patent_search_executor(self):
        """Test api_tool_executor for patent search."""
        result = api_tool_executor(
            "patent_search", {"company_name": "Apple", "keywords": ["iPhone", "iOS"]}
        )

        assert isinstance(result, dict)
        assert result["api_source"] == "uspto"
        assert result["company"] == "Apple"
        assert result["keywords"] == ["iPhone", "iOS"]

    def test_patent_search_executor_no_keywords(self):
        """Test api_tool_executor for patent search without keywords."""
        result = api_tool_executor("patent_search", {"company_name": "Google"})

        assert isinstance(result, dict)
        assert result["api_source"] == "uspto"
        assert result["company"] == "Google"
        assert result["keywords"] == []

    def test_regulations_executor(self):
        """Test api_tool_executor for regulations."""
        result = api_tool_executor("regulations", {"industry": "Healthcare", "region": "EU"})

        assert isinstance(result, dict)
        assert result["api_source"] == "regulatory_database"
        assert result["industry"] == "Healthcare"
        assert result["region"] == "EU"

    def test_regulations_executor_default_region(self):
        """Test api_tool_executor for regulations with default region."""
        result = api_tool_executor("regulations", {"industry": "Finance"})

        assert isinstance(result, dict)
        assert result["region"] == "US"

    def test_funding_intel_executor(self):
        """Test api_tool_executor for funding intelligence."""
        result = api_tool_executor("funding_intel", {"industry": "Crypto", "stage": "Series C"})

        assert isinstance(result, dict)
        assert result["api_source"] == "funding_database"
        assert result["industry"] == "Crypto"
        assert result["stage"] == "Series C"

    def test_funding_intel_executor_default_stage(self):
        """Test api_tool_executor for funding intelligence with default stage."""
        result = api_tool_executor("funding_intel", {"industry": "Biotech"})

        assert isinstance(result, dict)
        assert result["stage"] == "Series A"

    @patch("time.sleep")
    def test_batch_executor(self, mock_sleep):
        """Test api_tool_executor for batch operations."""
        batch_requests = [
            {"api_type": "company_search", "params": {"company_name": "BatchCorp1"}},
            {"api_type": "market_data", "params": {"symbol": "BATCH"}},
        ]

        result = api_tool_executor("batch", {"requests": batch_requests})

        assert isinstance(result, dict)
        assert "batch_results" in result
        batch_results = result["batch_results"]
        assert len(batch_results) == 2
        assert batch_results[0]["api_source"] == "crunchbase"
        assert batch_results[1]["api_source"] == "alpha_vantage"

    def test_unknown_api_type_executor(self):
        """Test api_tool_executor with unknown API type."""
        result = api_tool_executor("unknown_type", {})

        assert isinstance(result, dict)
        assert "error" in result
        assert "Unknown API type: unknown_type" in result["error"]


class TestIntegration:
    """Test integration scenarios."""

    @patch("time.sleep")
    def test_full_api_workflow(self, mock_sleep):
        """Test complete API workflow."""
        api_tool = ExternalAPITool()

        # Test a realistic workflow
        company_name = "InnovationCorp"

        # 1. Search company information
        company_data = api_tool.search_company_crunchbase(company_name)
        assert company_data["company"] == company_name

        # 2. Get market data for a related symbol
        market_data = api_tool.get_market_data_alpha_vantage("INNOV")
        assert market_data["symbol"] == "INNOV"

        # 3. Enrich with Clearbit data
        domain = "innovationcorp.com"
        enriched_data = api_tool.enrich_company_clearbit(domain)
        assert enriched_data["domain"] == domain

        # 4. Search patents
        patent_data = api_tool.search_patents(company_name, ["innovation", "technology"])
        assert patent_data["company"] == company_name

        # 5. Get industry regulations
        reg_data = api_tool.get_industry_regulations("Technology", "US")
        assert reg_data["industry"] == "Technology"

        # 6. Get funding intelligence
        funding_data = api_tool.get_funding_intelligence("Software", "Series B")
        assert funding_data["industry"] == "Software"

        # All operations should return success
        assert company_data["api_status"] == "success"
        assert market_data["api_status"] == "success"
        assert enriched_data["api_status"] == "success"
        assert patent_data["api_status"] == "success"
        assert reg_data["api_status"] == "success"
        assert funding_data["api_status"] == "success"

    def test_api_tool_executor_integration(self):
        """Test api_tool_executor with all API types."""
        # Test all supported API types
        test_cases = [
            ("company_search", {"company_name": "TestCorp"}),
            ("market_data", {"symbol": "TEST"}),
            ("company_enrich", {"domain": "test.com"}),
            ("patent_search", {"company_name": "PatentCorp"}),
            ("regulations", {"industry": "Tech"}),
            ("funding_intel", {"industry": "SaaS"}),
        ]

        for api_type, params in test_cases:
            result = api_tool_executor(api_type, params)
            assert isinstance(result, dict)
            assert "api_status" in result
            assert result["api_status"] == "success"

    def test_datetime_formats(self):
        """Test that datetime fields are properly formatted."""
        api_tool = ExternalAPITool()

        result = api_tool.search_company_crunchbase("TestCorp")
        retrieved_at = result["retrieved_at"]

        # Should be ISO format datetime string
        assert isinstance(retrieved_at, str)
        # Should be parseable as datetime
        parsed_dt = datetime.fromisoformat(
            retrieved_at.replace("Z", "+00:00") if retrieved_at.endswith("Z") else retrieved_at
        )
        assert isinstance(parsed_dt, datetime)

    def test_error_handling_edge_cases(self):
        """Test edge cases and error handling."""
        api_tool = ExternalAPITool()

        # Test with empty strings
        result1 = api_tool.search_company_crunchbase("")
        assert result1["company"] == ""

        result2 = api_tool.get_market_data_alpha_vantage("")
        assert result2["symbol"] == ""

        result3 = api_tool.enrich_company_clearbit("")
        assert result3["domain"] == ""

        # All should still return valid responses
        assert result1["api_status"] == "success"
        assert result2["api_status"] == "success"
        assert result3["api_status"] == "success"
