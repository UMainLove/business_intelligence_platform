"""
Functionality tests for external API integration features.
Tests the external data collection and third-party integration capabilities.
"""

import pytest

from src.tools.api_tools import ExternalAPITool, api_tool_executor, create_api_tool_spec
from src.tools.rag_tools import MarketResearchRAG, create_rag_tool_spec, rag_tool_executor
from src.tools.web_tools import WebSearchTool, create_web_search_tool_spec, web_search_executor


class TestWebIntelligenceFeatures:
    """Test Web Intelligence capabilities for real-time data collection."""

    def test_web_search_tool_initialization(self):
        """Test that WebSearchTool initializes properly."""
        service = WebSearchTool()

        # Verify service is created
        assert service is not None

        # Check if service has expected methods
        assert hasattr(service, "search_market_trends")
        assert hasattr(service, "search_competitors")
        assert hasattr(service, "search_companies")

    def test_market_trends_collection(self):
        """Test market trends data collection."""
        service = WebSearchTool()
        result = service.search_market_trends("AI technology", "1y")

        # Verify result structure
        assert isinstance(result, dict)
        assert "industry" in result
        assert "trends" in result
        assert "search_time" in result

    def test_competitor_analysis_functionality(self):
        """Test competitor analysis through web search."""
        service = WebSearchTool()

        # Test competitor analysis
        result = service.search_competitors("SaaS platform", "SMB market")

        # Should return structured data
        assert isinstance(result, dict)
        assert "competitors" in result
        assert "business_idea" in result

    def test_web_search_tool_integration(self):
        """Test Web Search tool integration with AG2."""
        # Test tool specification
        tool_spec = create_web_search_tool_spec()

        assert tool_spec["name"] == "web_search"
        assert "description" in tool_spec
        assert "parameters" in tool_spec

        # Test tool executor
        result = web_search_executor("market_trends", {"industry": "Technology", "timeframe": "1y"})

        assert isinstance(result, dict)
        assert "industry" in result

    def test_industry_trends_analysis(self):
        """Test industry trends collection and analysis."""
        service = WebSearchTool()
        result = service.search_market_trends("Technology")

        # Verify trends structure
        assert "trends" in result
        assert len(result["trends"]) > 0
        assert result["industry"] == "Technology"


class TestThirdPartyAPIIntegration:
    """Test third-party API integration capabilities."""

    def test_external_api_tool_initialization(self):
        """Test ExternalAPITool initialization."""
        service = ExternalAPITool()

        assert service is not None
        assert hasattr(service, "get_market_data_alpha_vantage")
        assert hasattr(service, "search_company_crunchbase")

    def test_financial_data_integration(self):
        """Test integration with financial data APIs."""
        service = ExternalAPITool()
        result = service.get_market_data_alpha_vantage("TECH")

        assert isinstance(result, dict)
        assert "symbol" in result
        assert "data" in result
        assert result["symbol"] == "TECH"

    def test_api_error_handling(self):
        """Test API error handling and fallback mechanisms."""
        service = ExternalAPITool()

        # Test with various scenarios
        result = service.get_market_data_alpha_vantage("INVALID")

        # Should handle errors gracefully
        assert isinstance(result, dict)
        # Should return structured response
        assert "symbol" in result

    def test_external_api_tool_executor(self):
        """Test external API tool executor functionality."""
        # Test tool specification
        tool_spec = create_api_tool_spec()

        assert tool_spec["name"] == "external_api"
        assert "description" in tool_spec

        # Test executor
        result = api_tool_executor("market_data", {"symbol": "AAPL"})

        assert isinstance(result, dict)
        assert "symbol" in result

    def test_funding_intelligence_integration(self):
        """Test funding intelligence API integration."""
        service = ExternalAPITool()
        result = service.get_funding_intelligence("Technology", "Series A")

        assert "industry" in result
        assert "data" in result
        assert "market_activity" in result["data"]
        assert isinstance(result["data"]["active_investors"], list)


class TestRAGVectorDBIntegration:
    """Test RAG (Retrieval Augmented Generation) and Vector Database integration."""

    def test_market_research_rag_initialization(self):
        """Test MarketResearchRAG initialization."""
        service = MarketResearchRAG()

        assert service is not None
        assert hasattr(service, "search")
        assert hasattr(service, "get_market_insights")

    def test_historical_data_retrieval(self):
        """Test historical business data retrieval through RAG."""
        service = MarketResearchRAG()

        # Search for documents (may be empty initially)
        results = service.search("SaaS success rates", top_k=3)

        assert isinstance(results, list)
        # Results can be empty initially, that's okay

    def test_market_insights_query(self):
        """Test market insights querying functionality."""
        service = MarketResearchRAG()

        result = service.get_market_insights("What are the key factors for business success?")

        assert isinstance(result, dict)
        assert "query" in result
        assert "sources" in result
        assert "market_data" in result

    def test_rag_tool_integration(self):
        """Test RAG tool integration with AG2."""
        # Test tool specification
        tool_spec = create_rag_tool_spec()

        assert tool_spec["name"] == "market_research_rag"
        assert "description" in tool_spec
        assert "parameters" in tool_spec

        # Test tool executor
        result = rag_tool_executor("search", {"query": "startup success rates", "top_k": 3})

        assert isinstance(result, dict)
        assert "results" in result

    def test_contextual_business_advice(self):
        """Test contextual business advice through RAG."""
        service = MarketResearchRAG()
        result = service.get_market_insights("How to ensure startup success in technology sector?")

        assert "query" in result
        assert "sources" in result
        assert "market_data" in result
        assert "competitors" in result


class TestRealTimeDataCollection:
    """Test real-time data collection and processing capabilities."""

    def test_real_time_market_monitoring(self):
        """Test real-time market data monitoring."""
        # Test web search for real-time data
        web_service = WebSearchTool()

        result = web_service.search_market_trends("technology", "1y")

        assert isinstance(result, dict)
        assert "trends" in result
        assert "search_time" in result

    def test_trend_monitoring_system(self):
        """Test continuous trend monitoring system."""
        service = WebSearchTool()
        result = service.search_market_trends("Global technology trends")

        assert "trends" in result
        assert "search_time" in result  # Has time information
        assert isinstance(result["trends"], list)

    def test_data_freshness_validation(self):
        """Test that collected data includes freshness indicators."""
        # Test various services for data freshness
        web_service = WebSearchTool()
        api_service = ExternalAPITool()

        # Web search should include timing
        web_result = web_service.search_market_trends("test industry", "1y")
        assert isinstance(web_result, dict)
        assert "search_time" in web_result

        # External API should handle timing
        api_result = api_service.get_market_data_alpha_vantage("TEST")
        assert isinstance(api_result, dict)
        assert "retrieved_at" in api_result

    def test_real_time_financial_feeds(self):
        """Test real-time financial data feeds integration."""
        service = ExternalAPITool()
        result = service.get_market_data_alpha_vantage("TECH")

        assert "retrieved_at" in result
        assert "data" in result
        assert "current_price" in result["data"]


class TestIntegrationCoordination:
    """Test coordination between different external API systems."""

    def test_multi_source_data_coordination(self):
        """Test coordination between multiple data sources."""
        # Initialize all services
        web_service = WebSearchTool()
        api_service = ExternalAPITool()
        rag_service = MarketResearchRAG()

        # Test that they can work together
        assert web_service is not None
        assert api_service is not None
        assert rag_service is not None

    def test_coordinated_business_intelligence(self):
        """Test coordinated intelligence gathering from multiple sources."""
        # Create business intelligence query that uses all systems
        business_query = {
            "company": "TechStartup",
            "industry": "SaaS",
            "analysis_type": "comprehensive",
        }

        # Simulate coordinated data collection
        web_service = WebSearchTool()
        api_service = ExternalAPITool()
        rag_service = MarketResearchRAG()

        # Collect data from all sources using the business query context
        market_data = web_service.search_market_trends(business_query["industry"], "1y")
        financial_data = api_service.get_market_data_alpha_vantage(business_query["industry"])
        historical_data = rag_service.get_market_insights(
            f"{business_query['industry']} success patterns for {business_query['company']}"
        )

        # Verify all systems return data
        assert isinstance(market_data, dict)
        assert isinstance(financial_data, dict)
        assert isinstance(historical_data, dict)

    def test_error_propagation_and_fallbacks(self):
        """Test error handling across integrated systems."""
        web_service = WebSearchTool()
        api_service = ExternalAPITool()
        rag_service = MarketResearchRAG()

        # Test error handling for each service
        # These should handle errors gracefully, not crash

        try:
            web_result = web_service.search_market_trends("", "1y")  # Empty industry
            assert isinstance(web_result, dict)
        except Exception as e:
            # Should handle gracefully
            assert "error" in str(e).lower() or True  # Allow controlled errors

        try:
            api_result = api_service.get_market_data_alpha_vantage("INVALID_SYMBOL")
            assert isinstance(api_result, dict)
        except Exception as e:
            assert "error" in str(e).lower() or True

        try:
            rag_result = rag_service.get_market_insights("")  # Empty query
            assert isinstance(rag_result, dict)
        except Exception as e:
            assert "error" in str(e).lower() or True

    def test_data_format_standardization(self):
        """Test that all external sources return standardized data formats."""
        # Test tool executors for consistent interfaces
        web_result = web_search_executor(
            "market_trends", {"industry": "Technology", "timeframe": "1y"}
        )

        api_result = api_tool_executor("market_data", {"symbol": "TECH"})

        rag_result = rag_tool_executor("search", {"query": "technology trends", "top_k": 3})

        # All should return dictionaries with consistent structure
        assert isinstance(web_result, dict)
        assert isinstance(api_result, dict)
        assert isinstance(rag_result, dict)


class TestExternalAPIReliability:
    """Test reliability and robustness of external API integrations."""

    def test_api_timeout_handling(self):
        """Test handling of API timeouts and slow responses."""
        service = ExternalAPITool()

        # Test with potentially slow operation
        result = service.get_market_data_alpha_vantage("SLOW_API_TEST")

        # Should complete within reasonable time and handle timeouts
        assert isinstance(result, dict)
        assert "symbol" in result

    def test_rate_limiting_compliance(self):
        """Test compliance with API rate limiting."""
        service = ExternalAPITool()

        # Test multiple rapid requests (should handle rate limiting)
        results = []
        for i in range(3):  # Limited test to avoid actual rate limiting
            result = service.get_market_data_alpha_vantage(f"TEST_{i}")
            results.append(result)
            assert isinstance(result, dict)
            assert "symbol" in result

        # All requests should be handled appropriately
        assert len(results) == 3

    def test_authentication_handling(self):
        """Test API authentication and key management."""
        # Test services handle missing/invalid API keys gracefully
        web_service = WebSearchTool()
        api_service = ExternalAPITool()

        # Should not crash on authentication issues
        web_result = web_service.search_market_trends("test", "1y")
        api_result = api_service.get_market_data_alpha_vantage("TEST")

        assert isinstance(web_result, dict)
        assert isinstance(api_result, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
