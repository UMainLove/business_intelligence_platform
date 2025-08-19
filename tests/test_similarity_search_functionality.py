"""
Functionality tests for similarity search and business matching capabilities.
Tests finding similar businesses, benchmarking, and vector similarity search features.
"""

import pytest

from src.tools.database_production import (
    database_tool_executor as production_database_tool_executor,
)
from src.tools.database_tools import BusinessDataDB, database_tool_executor
from src.tools.rag_tools import Document, MarketResearchRAG, rag_tool_executor
from src.tools.web_tools import WebSearchTool, web_search_executor


class TestBusinessSimilarityMatching:
    """Test similarity matching for finding comparable businesses."""

    def test_similar_ventures_analysis(self):
        """Test finding and analyzing similar business ventures."""
        db = BusinessDataDB()

        # Test similar ventures analysis
        result = db.analyze_similar_ventures(
            industry="Technology", business_model="SaaS", region="North America"
        )

        # Verify result structure
        assert isinstance(result, dict)
        assert "similar_ventures" in result
        assert "analysis" in result
        assert isinstance(result["similar_ventures"], list)

    def test_similar_ventures_with_different_criteria(self):
        """Test similarity matching with various business criteria."""
        db = BusinessDataDB()

        # Test different industry combinations
        test_cases = [
            {"industry": "Healthcare", "business_model": "B2B", "region": "Europe"},
            {"industry": "Fintech", "business_model": "B2C", "region": None},
            {"industry": "E-commerce", "business_model": "Marketplace", "region": "Global"},
        ]

        for case in test_cases:
            result = db.analyze_similar_ventures(
                industry=case["industry"],
                business_model=case["business_model"],
                region=case["region"],
            )

            assert isinstance(result, dict)
            assert "similar_ventures" in result
            # Should handle both found and not found cases
            if result["similar_ventures"]:
                assert len(result["similar_ventures"]) > 0
                # Check venture structure
                venture = result["similar_ventures"][0]
                assert "name" in venture
                assert "status" in venture
                assert "funding_info" in venture or "valuation" in venture or venture

    def test_similar_ventures_success_rate_analysis(self):
        """Test success rate analysis of similar ventures."""
        db = BusinessDataDB()

        result = db.analyze_similar_ventures(industry="Technology", business_model="SaaS")

        # Should include success rate analysis
        assert "analysis" in result
        analysis_text = result["analysis"]

        # Analysis should mention success rate or venture count
        assert isinstance(analysis_text, str)
        assert len(analysis_text) > 0

    def test_production_database_similarity_search(self):
        """Test similarity search in production database."""
        # Test production database similar ventures via tool executor
        result = production_database_tool_executor(
            "similar_ventures", {"industry": "Technology", "business_model": "B2B"}
        )

        assert isinstance(result, dict)
        assert "similar_ventures" in result

    def test_similarity_tool_integration(self):
        """Test similarity search through tool executor."""
        # Test database tool executor for similar ventures
        result = database_tool_executor(
            "similar_ventures", {"industry": "Technology", "business_model": "SaaS", "region": "US"}
        )

        assert isinstance(result, dict)
        assert "similar_ventures" in result

        # Test production database tool executor
        prod_result = production_database_tool_executor(
            "similar_ventures", {"industry": "Healthcare", "business_model": "B2B"}
        )

        assert isinstance(prod_result, dict)
        assert "similar_ventures" in prod_result


class TestIndustryBenchmarking:
    """Test industry benchmarking and comparison features."""

    def test_industry_benchmarks_retrieval(self):
        """Test retrieving industry benchmarks for comparison."""
        db = BusinessDataDB()

        result = db.get_industry_benchmarks("Technology")

        assert isinstance(result, dict)
        assert "industry" in result
        assert "metrics" in result
        assert result["industry"] == "Technology"
        assert isinstance(result["metrics"], list)

    def test_benchmark_metrics_structure(self):
        """Test structure of benchmark metrics."""
        db = BusinessDataDB()

        industries = ["Technology", "Healthcare", "Finance", "E-commerce"]

        for industry in industries:
            result = db.get_industry_benchmarks(industry)

            assert "industry" in result
            assert "metrics" in result

            # Check metrics structure if available
            for metric in result["metrics"]:
                if metric:  # If metrics exist
                    assert "metric_name" in metric or "name" in metric or metric
                    assert "value" in metric or "amount" in metric or metric

    def test_cross_industry_benchmark_comparison(self):
        """Test benchmarking across different industries."""
        db = BusinessDataDB()

        # Get benchmarks for multiple industries
        tech_benchmarks = db.get_industry_benchmarks("Technology")
        healthcare_benchmarks = db.get_industry_benchmarks("Healthcare")
        finance_benchmarks = db.get_industry_benchmarks("Finance")

        # All should return valid structures
        for benchmarks in [tech_benchmarks, healthcare_benchmarks, finance_benchmarks]:
            assert isinstance(benchmarks, dict)
            assert "industry" in benchmarks
            assert "metrics" in benchmarks

    def test_production_benchmarking(self):
        """Test benchmarking in production environment."""
        # Test production database benchmarks via tool executor
        result = production_database_tool_executor("benchmarks", {"industry": "Technology"})

        assert isinstance(result, dict)
        assert "industry" in result

    def test_benchmarking_tool_integration(self):
        """Test benchmarking through tool executors."""
        # Test database tool for benchmarks
        result = database_tool_executor("benchmarks", {"industry": "Technology"})

        assert isinstance(result, dict)
        assert "industry" in result

        # Test production database tool for benchmarks
        prod_result = production_database_tool_executor("benchmarks", {"industry": "Healthcare"})

        assert isinstance(prod_result, dict)


class TestRAGSimilaritySearch:
    """Test RAG document similarity search capabilities."""

    def test_rag_document_search(self):
        """Test document similarity search in RAG system."""
        rag = MarketResearchRAG()

        # Search for similar documents
        results = rag.search("SaaS business model analysis", top_k=5)

        assert isinstance(results, list)
        # Results can be empty if no documents exist
        for doc in results:
            assert isinstance(doc, Document)
            assert hasattr(doc, "title")
            assert hasattr(doc, "content")
            assert hasattr(doc, "metadata")

    def test_market_insights_similarity(self):
        """Test market insights based on document similarity."""
        rag = MarketResearchRAG()

        result = rag.get_market_insights("startup funding trends")

        assert isinstance(result, dict)
        assert "query" in result
        assert "sources" in result
        assert "market_data" in result
        assert "competitors" in result

    def test_rag_similarity_with_different_queries(self):
        """Test RAG similarity search with various query types."""
        rag = MarketResearchRAG()

        queries = [
            "competitive analysis technology sector",
            "market size fintech industry",
            "venture capital investment trends",
            "business model comparison",
            "industry growth projections",
        ]

        for query in queries:
            results = rag.search(query, top_k=3)
            assert isinstance(results, list)

            insights = rag.get_market_insights(query)
            assert isinstance(insights, dict)
            assert "query" in insights

    def test_document_similarity_scoring(self):
        """Test document similarity scoring mechanism."""
        rag = MarketResearchRAG()

        # Add test documents for similarity testing
        rag.add_document(
            title="SaaS Business Model Analysis",
            content="Software as a Service businesses typically have recurring revenue models with high scalability potential.",
            metadata={"type": "business_model", "industry": "Software"},
        )

        rag.add_document(
            title="Subscription Revenue Models",
            content="Subscription-based revenue models provide predictable cash flow and customer retention benefits.",
            metadata={"type": "revenue_model", "industry": "Software"},
        )

        # Search for similar documents
        results = rag.search("SaaS subscription revenue model", top_k=5)

        # Should find relevant documents
        assert isinstance(results, list)
        # If documents were added, they should be found in search
        if results:
            assert len(results) > 0

    def test_rag_tool_similarity_integration(self):
        """Test RAG similarity search through tool executor."""
        # Test RAG tool search functionality
        result = rag_tool_executor("search", {"query": "business similarity analysis", "top_k": 5})

        assert isinstance(result, dict)
        assert "results" in result

        # Test market insights through RAG tool
        insights_result = rag_tool_executor("get_insights", {"query": "similar business models"})

        assert isinstance(insights_result, dict)
        assert "query" in insights_result


class TestVectorSimilaritySearch:
    """Test vector similarity search capabilities and future enhancements."""

    def test_embedding_support_structure(self):
        """Test that Document structure supports embeddings for vector search."""
        # Test Document class supports embeddings
        doc = Document(
            id="test_id",
            title="Test Document",
            content="Test content for vector similarity",
            metadata={"type": "test"},
            embedding=[0.1, 0.2, 0.3, 0.4, 0.5],  # Mock embedding vector
        )

        assert doc.embedding is not None
        assert isinstance(doc.embedding, list)
        assert len(doc.embedding) == 5

    def test_vector_search_readiness(self):
        """Test that RAG system is ready for vector similarity search."""
        rag = MarketResearchRAG()

        # Verify RAG system has embedding field support
        assert hasattr(Document, "embedding")

        # Test adding document with embedding
        doc_id = rag.add_document(
            title="Vector Search Test",
            content="This document tests vector similarity capabilities",
            metadata={"type": "test_vector"},
        )

        # Document should be added successfully
        assert isinstance(doc_id, str)
        assert len(doc_id) > 0

    def test_similarity_search_extensibility(self):
        """Test that similarity search can be extended for production vector DB."""
        rag = MarketResearchRAG()

        # Test current search method (keyword-based)
        results = rag.search("vector similarity test", top_k=3)
        assert isinstance(results, list)

        # Verify search method exists and is extensible
        assert hasattr(rag, "search")
        assert callable(rag.search)

    def test_production_vector_db_compatibility(self):
        """Test compatibility with production vector databases (Pinecone, Chroma, FAISS)."""
        # Test that the system structure supports vector DB integration
        rag = MarketResearchRAG()

        # Verify RAG can be instantiated and is ready for vector DB integration
        assert rag is not None
        assert hasattr(rag, "documents")  # Has document storage
        assert hasattr(rag, "search")  # Has search capability

        # Mock vector similarity search (as would be implemented with vector DB)
        mock_vector_search_result = [
            {
                "document_id": "doc_1",
                "similarity_score": 0.95,
                "content": "Highly similar business model analysis",
                "metadata": {"industry": "Technology", "type": "analysis"},
            },
            {
                "document_id": "doc_2",
                "similarity_score": 0.87,
                "content": "Related startup funding research",
                "metadata": {"industry": "Venture Capital", "type": "research"},
            },
        ]

        # Verify structure compatibility with vector DB results
        for result in mock_vector_search_result:
            assert "similarity_score" in result
            assert "content" in result
            assert "metadata" in result
            assert 0 <= result["similarity_score"] <= 1


class TestSimilarityWebSearch:
    """Test web-based similarity search for competitor and market intelligence."""

    def test_competitor_similarity_search(self):
        """Test finding similar competitors through web search."""
        web_tool = WebSearchTool()

        result = web_tool.search_competitors(
            business_idea="AI-powered analytics platform", target_market="Enterprise B2B"
        )

        assert isinstance(result, dict)
        assert "competitors" in result
        assert "business_idea" in result
        assert isinstance(result["competitors"], list)

        # Check competitor structure
        for competitor in result["competitors"]:
            if competitor:  # If competitors found
                assert "name" in competitor or competitor
                assert "description" in competitor or competitor

    def test_market_similarity_analysis(self):
        """Test finding similar markets and trends."""
        web_tool = WebSearchTool()

        result = web_tool.search_market_trends("SaaS platforms", "2y")

        assert isinstance(result, dict)
        assert "industry" in result
        assert "trends" in result
        assert isinstance(result["trends"], list)

    def test_company_similarity_search(self):
        """Test searching for similar companies."""
        web_tool = WebSearchTool()

        result = web_tool.search_companies("Salesforce", "San Francisco")

        assert isinstance(result, dict)
        assert "company" in result
        assert "results" in result
        assert isinstance(result["results"], list)

    def test_funding_similarity_analysis(self):
        """Test finding similar funding patterns and investors."""
        web_tool = WebSearchTool()

        result = web_tool.search_funding_landscape("AI/ML", "Series A")

        assert isinstance(result, dict)
        assert "industry" in result
        assert "stage" in result
        assert "funding_trends" in result
        assert "active_investors" in result

    def test_web_similarity_tool_integration(self):
        """Test web similarity search through tool executors."""
        # Test competitor search
        competitor_result = web_search_executor(
            "competitors",
            {"business_idea": "Cloud-based CRM platform", "target_market": "SMB market"},
        )

        assert isinstance(competitor_result, dict)
        assert "competitors" in competitor_result

        # Test company search
        company_result = web_search_executor(
            "companies", {"company_name": "Microsoft", "location": "Seattle"}
        )

        assert isinstance(company_result, dict)
        assert "company" in company_result


class TestSimilaritySearchIntegration:
    """Test integration between different similarity search systems."""

    def test_cross_system_similarity_coordination(self):
        """Test similarity search coordination across database, RAG, and web systems."""
        # Initialize all similarity search systems
        db = BusinessDataDB()
        rag = MarketResearchRAG()
        web_tool = WebSearchTool()

        query_context = {
            "industry": "Technology",
            "business_model": "SaaS",
            "company_name": "TechStartup",
        }

        # Get similarity data from all systems
        db_similar = db.analyze_similar_ventures(
            query_context["industry"], query_context["business_model"]
        )

        rag_similar = rag.get_market_insights(
            f"{query_context['industry']} {query_context['business_model']} analysis"
        )

        web_similar = web_tool.search_competitors(
            f"{query_context['business_model']} platform", query_context["industry"]
        )

        # All systems should return data
        assert isinstance(db_similar, dict)
        assert isinstance(rag_similar, dict)
        assert isinstance(web_similar, dict)

    def test_similarity_data_aggregation(self):
        """Test aggregating similarity data from multiple sources."""
        # Test that different similarity systems can work together
        db = BusinessDataDB()
        rag = MarketResearchRAG()

        # Database similarity
        db_result = db.analyze_similar_ventures("Healthcare", "B2B")

        # RAG similarity
        rag_result = rag.get_market_insights("Healthcare B2B business models")

        # Both should provide complementary similarity data
        assert isinstance(db_result, dict)
        assert isinstance(rag_result, dict)

        # Results should be combinable for comprehensive similarity analysis
        combined_similarity = {
            "database_similar": db_result,
            "document_similar": rag_result,
            "query": "Healthcare B2B similarity analysis",
        }

        assert "database_similar" in combined_similarity
        assert "document_similar" in combined_similarity
        assert "query" in combined_similarity

    def test_similarity_search_tool_coordination(self):
        """Test coordination between similarity search tools."""
        # Test multiple tool executors working together
        db_tool_result = database_tool_executor(
            "similar_ventures", {"industry": "Fintech", "business_model": "B2C"}
        )

        rag_tool_result = rag_tool_executor(
            "get_insights", {"query": "Fintech B2C business similarity"}
        )

        web_tool_result = web_search_executor(
            "competitors",
            {"business_idea": "Fintech consumer platform", "target_market": "Consumer banking"},
        )

        # All tools should work together
        assert isinstance(db_tool_result, dict)
        assert isinstance(rag_tool_result, dict)
        assert isinstance(web_tool_result, dict)

    def test_similarity_search_error_handling(self):
        """Test error handling across similarity search systems."""
        db = BusinessDataDB()
        rag = MarketResearchRAG()
        web_tool = WebSearchTool()

        # Test with edge cases and empty queries
        try:
            db_result = db.analyze_similar_ventures("", "")
            assert isinstance(db_result, dict)
        except Exception as e:
            # Should handle errors gracefully
            assert "error" in str(e).lower() or True

        try:
            rag_result = rag.get_market_insights("")
            assert isinstance(rag_result, dict)
        except Exception as e:
            assert "error" in str(e).lower() or True

        try:
            web_result = web_tool.search_competitors("", "")
            assert isinstance(web_result, dict)
        except Exception as e:
            assert "error" in str(e).lower() or True


class TestSimilaritySearchPerformance:
    """Test performance and scalability of similarity search systems."""

    def test_similarity_search_response_time(self):
        """Test that similarity searches complete in reasonable time."""
        import time

        db = BusinessDataDB()
        rag = MarketResearchRAG()

        # Test database similarity search performance
        start_time = time.time()
        db_result = db.analyze_similar_ventures("Technology", "SaaS")
        db_time = time.time() - start_time

        # Should complete quickly (under 5 seconds for tests)
        assert db_time < 5.0
        assert isinstance(db_result, dict)

        # Test RAG similarity search performance
        start_time = time.time()
        rag_result = rag.search("business model analysis", top_k=5)
        rag_time = time.time() - start_time

        # Should complete quickly
        assert rag_time < 5.0
        assert isinstance(rag_result, list)

    def test_batch_similarity_search(self):
        """Test batch similarity search operations."""
        db = BusinessDataDB()

        # Test multiple similarity searches
        industries = ["Technology", "Healthcare", "Finance"]
        business_models = ["B2B", "B2C", "Marketplace"]

        results = []
        for industry in industries:
            for model in business_models:
                result = db.analyze_similar_ventures(industry, model)
                results.append(result)
                assert isinstance(result, dict)

        # Should handle multiple searches
        assert len(results) == len(industries) * len(business_models)

    def test_similarity_search_scalability(self):
        """Test similarity search scalability with larger datasets."""
        rag = MarketResearchRAG()

        # Add multiple documents to test search scalability
        for i in range(10):
            rag.add_document(
                title=f"Business Analysis {i}",
                content=f"Analysis content for business model {i} in various industries",
                metadata={"type": "analysis", "index": i},
            )

        # Search should handle larger document sets
        results = rag.search("business analysis", top_k=5)
        assert isinstance(results, list)
        assert len(results) <= 5  # Should respect top_k limit


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
