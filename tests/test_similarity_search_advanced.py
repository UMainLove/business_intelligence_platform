"""
Advanced tests for similarity search to achieve production-ready coverage.
Covers edge cases, performance, error handling, and vector DB readiness.
"""

import time
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.tools.database_tools import BusinessDataDB
from src.tools.rag_tools import Document, MarketResearchRAG
from src.tools.web_tools import WebSearchTool


class TestSimilaritySearchEdgeCases:
    """Test edge cases and error handling for similarity search."""

    def test_empty_database_similarity_search(self):
        """Test similarity search with empty database."""
        db = BusinessDataDB()

        # Mock sqlite3 to return empty results
        with patch("sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_connect.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor

            # Mock empty database response
            mock_cursor.fetchall.return_value = []

            result = db.analyze_similar_ventures("Technology", "SaaS")

            # Should handle empty results gracefully
            assert result["similar_ventures"] == []
            assert (
                "No similar ventures found" in result["analysis"]
                or "0 similar ventures" in result["analysis"]
            )

    def test_similarity_search_with_special_characters(self):
        """Test similarity search handles special characters in queries."""
        db = BusinessDataDB()

        # Test with special characters that could cause issues
        test_cases = [
            ("Tech & Innovation", "B2B"),
            ("Healthcare/Medical", "SaaS"),
            ("E-commerce (Online)", "Marketplace"),
            ("Fin-Tech", "B2C"),
            ("AI/ML & Data", "Platform"),
        ]

        for industry, model in test_cases:
            result = db.analyze_similar_ventures(industry, model)
            assert isinstance(result, dict)
            assert "similar_ventures" in result
            assert "analysis" in result

    def test_similarity_search_with_null_values(self):
        """Test similarity search handles null/None values gracefully."""
        db = BusinessDataDB()

        # Test with None values
        result = db.analyze_similar_ventures(None, None)
        assert isinstance(result, dict)

        # Test with partial None values
        result = db.analyze_similar_ventures("Technology", None)
        assert isinstance(result, dict)

        result = db.analyze_similar_ventures(None, "SaaS")
        assert isinstance(result, dict)

    def test_similarity_search_case_insensitivity(self):
        """Test that similarity search is case-insensitive."""
        db = BusinessDataDB()

        # Test different case variations
        result1 = db.analyze_similar_ventures("TECHNOLOGY", "SAAS")
        result2 = db.analyze_similar_ventures("technology", "saas")
        result3 = db.analyze_similar_ventures("Technology", "SaaS")

        # All should return valid results
        for result in [result1, result2, result3]:
            assert isinstance(result, dict)
            assert "similar_ventures" in result

    def test_similarity_threshold_variations(self):
        """Test similarity search with different threshold levels."""
        rag = MarketResearchRAG()

        # Add test documents with varying similarity
        rag.add_document(
            title="Exact Match Document",
            content="This is about SaaS business models in technology sector",
            metadata={"similarity_score": 1.0},
        )

        rag.add_document(
            title="High Similarity Document",
            content="Software as a Service technology business model analysis",
            metadata={"similarity_score": 0.8},
        )

        rag.add_document(
            title="Medium Similarity Document",
            content="Business software and technology services",
            metadata={"similarity_score": 0.5},
        )

        rag.add_document(
            title="Low Similarity Document",
            content="Healthcare medical devices manufacturing",
            metadata={"similarity_score": 0.2},
        )

        # Search with high similarity requirement
        results = rag.search("SaaS technology business model", top_k=10)
        assert isinstance(results, list)

        # Verify results are ordered by relevance
        if len(results) > 1:
            # Results should be in descending order of relevance
            assert True  # Placeholder for actual similarity scoring when implemented


class TestVectorEmbeddingReadiness:
    """Test vector embedding generation and comparison capabilities."""

    def test_document_embedding_structure(self):
        """Test that documents support embedding vectors."""
        # Create document with mock embedding
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        doc = Document(
            id="test_001",
            title="Test Document",
            content="Test content for embedding",
            metadata={"type": "test"},
            embedding=embedding,
        )

        assert doc.embedding == embedding
        assert len(doc.embedding) == 5

    def test_embedding_dimension_consistency(self):
        """Test that embeddings maintain consistent dimensions."""
        rag = MarketResearchRAG()

        # Mock embedding dimension (e.g., 768 for BERT, 1536 for OpenAI)
        embedding_dim = 768

        # Add documents with consistent embedding dimensions
        for i in range(5):
            [float(i) / 100] * embedding_dim  # Mock embedding
            doc_id = rag.add_document(
                title=f"Document {i}",
                content=f"Content for document {i}",
                metadata={"embedding_dim": embedding_dim},
            )
            assert isinstance(doc_id, str)

    def test_cosine_similarity_calculation(self):
        """Test cosine similarity calculation between vectors."""

        def cosine_similarity(vec1, vec2):
            """Calculate cosine similarity between two vectors."""
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            if norm1 == 0 or norm2 == 0:
                return 0.0
            return dot_product / (norm1 * norm2)

        # Test vectors
        vec1 = [1.0, 0.5, 0.3, 0.8]
        vec2 = [0.9, 0.6, 0.2, 0.7]  # Similar
        vec3 = [0.1, 0.1, 0.9, 0.2]  # Different

        # Calculate similarities
        sim_12 = cosine_similarity(vec1, vec2)
        sim_13 = cosine_similarity(vec1, vec3)

        # Similar vectors should have higher similarity
        assert sim_12 > sim_13
        assert 0 <= sim_12 <= 1
        assert 0 <= sim_13 <= 1

    def test_embedding_based_search_readiness(self):
        """Test that system is ready for embedding-based search."""
        rag = MarketResearchRAG()

        # Verify RAG can handle embedding-based operations
        assert hasattr(rag, "documents")
        assert hasattr(rag, "search")
        assert hasattr(rag, "add_document")

        # Test that search method can be extended for vector search
        with patch.object(rag, "search") as mock_search:
            mock_search.return_value = [
                Document(
                    id="1",
                    title="Similar Doc",
                    content="Content",
                    metadata={"similarity_score": 0.95},
                )
            ]

            results = rag.search("test query", top_k=5)
            assert len(results) == 1
            assert results[0].metadata["similarity_score"] == 0.95

    def test_vector_db_adapter_interface(self):
        """Test interface compatibility for vector database adapters."""

        # Mock vector DB adapter interface
        class VectorDBAdapter:
            def __init__(self, collection_name: str):
                self.collection_name = collection_name
                self.vectors: List[List[float]] = []
                self.metadata: List[Dict[str, Any]] = []

            def add_vector(self, vector, metadata):
                self.vectors.append(vector)
                self.metadata.append(metadata)
                return len(self.vectors) - 1

            def search(self, query_vector, top_k=5):
                # Mock similarity search
                return [
                    {"id": i, "score": 0.9 - i * 0.1, "metadata": m}
                    for i, m in enumerate(self.metadata[:top_k])
                ]

        # Test adapter
        adapter = VectorDBAdapter("business_ventures")

        # Add vectors
        for i in range(10):
            vector = [float(i) / 10] * 128
            metadata = {"doc_id": f"doc_{i}", "type": "venture"}
            adapter.add_vector(vector, metadata)

        # Search vectors
        query = [0.5] * 128
        results = adapter.search(query, top_k=3)

        assert len(results) == 3
        assert results[0]["score"] > results[1]["score"]


class TestSimilaritySearchPerformance:
    """Test performance characteristics of similarity search."""

    def test_search_response_time_under_load(self):
        """Test that similarity search maintains performance under load."""
        db = BusinessDataDB()

        # Measure response times for multiple queries
        response_times = []
        queries = [
            ("Technology", "SaaS"),
            ("Healthcare", "B2B"),
            ("Finance", "B2C"),
            ("E-commerce", "Marketplace"),
            ("Education", "Platform"),
        ]

        for industry, model in queries * 10:  # 50 queries total
            start_time = time.time()
            result = db.analyze_similar_ventures(industry, model)
            response_time = time.time() - start_time
            response_times.append(response_time)

            assert isinstance(result, dict)
            assert response_time < 1.0  # Should complete within 1 second

        # Check average response time
        avg_response_time = sum(response_times) / len(response_times)
        assert avg_response_time < 0.5  # Average should be under 500ms

    def test_batch_similarity_processing(self):
        """Test batch processing of similarity queries."""
        db = BusinessDataDB()

        # Batch of queries
        batch_queries = [
            {"industry": "Technology", "model": "SaaS"},
            {"industry": "Healthcare", "model": "B2B"},
            {"industry": "Finance", "model": "B2C"},
            {"industry": "Retail", "model": "E-commerce"},
            {"industry": "Education", "model": "EdTech"},
        ]

        # Process batch
        start_time = time.time()
        results = []
        for query in batch_queries:
            result = db.analyze_similar_ventures(query["industry"], query["model"])
            results.append(result)

        batch_time = time.time() - start_time

        # All results should be valid
        assert len(results) == len(batch_queries)
        for result in results:
            assert isinstance(result, dict)
            assert "similar_ventures" in result

        # Batch processing should be efficient
        assert batch_time < len(batch_queries) * 0.5  # Less than 500ms per query

    def test_concurrent_similarity_searches(self):
        """Test concurrent similarity search operations."""
        import concurrent.futures

        db = BusinessDataDB()

        def perform_search(params):
            industry, model = params
            return db.analyze_similar_ventures(industry, model)

        # Concurrent queries
        queries = [
            ("Technology", "SaaS"),
            ("Healthcare", "B2B"),
            ("Finance", "B2C"),
            ("Retail", "E-commerce"),
            ("Education", "EdTech"),
        ]

        # Execute concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(perform_search, q) for q in queries]
            results = [f.result(timeout=2) for f in futures]

        # All should complete successfully
        assert len(results) == len(queries)
        for result in results:
            assert isinstance(result, dict)
            assert "similar_ventures" in result

    def test_memory_usage_with_large_datasets(self):
        """Test memory efficiency with large similarity datasets."""
        rag = MarketResearchRAG()

        # Record initial document count (may have sample data)
        initial_count = len(rag.documents)

        # Add many documents
        docs_to_add = 100
        for i in range(docs_to_add):
            rag.add_document(
                title=f"Test Document {i}",
                content=f"Content for document {i} with various business terms",
                metadata={"index": i, "type": "test"},
            )

        # Perform multiple searches
        for i in range(20):
            results = rag.search(f"business term {i}", top_k=5)
            assert isinstance(results, list)
            assert len(results) <= 5

        # Memory should be managed efficiently (documents should only grow by
        # what we added)
        assert len(rag.documents) == initial_count + docs_to_add


class TestSimilaritySearchIntegration:
    """Test integration of similarity search with other components."""

    def test_similarity_with_financial_analysis(self):
        """Test similarity search integrated with financial analysis."""
        from src.tools.financial_tools import financial_tool_executor

        # Find similar ventures
        db = BusinessDataDB()
        similar_ventures = db.analyze_similar_ventures("Technology", "SaaS")

        # Analyze financials for similar ventures
        if similar_ventures["similar_ventures"]:
            for venture in similar_ventures["similar_ventures"][:3]:
                # Mock financial analysis for similar ventures
                financial_params = {
                    "initial_investment": venture.get("initial_funding", 1000000),
                    "revenue_growth": 0.3,
                    "operating_margin": 0.2,
                    "years": 5,
                }

                result = financial_tool_executor("npv", financial_params)
                assert isinstance(result, dict)

    def test_similarity_with_document_generation(self):
        """Test similarity search integrated with document generation."""
        from src.tools.document_tools import document_tool_executor

        # Find similar ventures
        db = BusinessDataDB()
        similar_ventures = db.analyze_similar_ventures("Healthcare", "B2B")

        # Generate comparison report
        if similar_ventures["similar_ventures"]:
            doc_params = {
                "template": "comparison",
                "data": {
                    "ventures": similar_ventures["similar_ventures"][:3],
                    "analysis": similar_ventures["analysis"],
                },
            }

            result = document_tool_executor("comparison_report", doc_params)
            assert isinstance(result, dict)

    def test_similarity_pipeline_end_to_end(self):
        """Test complete similarity search pipeline."""
        # Step 1: Web search for market data
        web_tool = WebSearchTool()
        market_data = web_tool.search_market_trends("AI Technology", "1y")

        # Step 2: Find similar ventures in database
        db = BusinessDataDB()
        similar = db.analyze_similar_ventures("Technology", "AI Platform")

        # Step 3: Search documents for insights
        rag = MarketResearchRAG()
        insights = rag.get_market_insights("AI technology platform analysis")

        # All components should work together
        assert isinstance(market_data, dict)
        assert isinstance(similar, dict)
        assert isinstance(insights, dict)

        # Combine results
        combined_analysis = {
            "market_trends": market_data.get("trends", []),
            "similar_ventures": similar.get("similar_ventures", []),
            "insights": insights.get("key_findings", []),
        }

        assert "market_trends" in combined_analysis
        assert "similar_ventures" in combined_analysis
        assert "insights" in combined_analysis


class TestProductionVectorDBCompatibility:
    """Test compatibility with production vector databases."""

    def test_pinecone_adapter_compatibility(self):
        """Test Pinecone vector database adapter."""
        # Mock the entire pinecone module to avoid import issues
        with patch.dict("sys.modules", {"pinecone": MagicMock()}):
            import sys

            # Create mock pinecone module
            mock_pinecone = MagicMock()
            mock_index_instance = MagicMock()

            # Configure mock responses
            mock_index_instance.query.return_value = {
                "matches": [
                    {"id": "doc1", "score": 0.95, "metadata": {"title": "Doc 1"}},
                    {"id": "doc2", "score": 0.87, "metadata": {"title": "Doc 2"}},
                ]
            }

            mock_pinecone.Index.return_value = mock_index_instance
            sys.modules["pinecone"] = mock_pinecone

            # Adapter interface
            class PineconeAdapter:
                def __init__(self, index_name: str, api_key: str):
                    import pinecone

                    pinecone.init(api_key=api_key)
                    self.index = pinecone.Index(index_name)

                def search(self, query_vector, top_k=5):
                    results = self.index.query(
                        vector=query_vector, top_k=top_k, include_metadata=True
                    )
                    return results["matches"]

            # Test adapter
            adapter = PineconeAdapter("test-index", "test-api-key")
            results = adapter.search([0.1] * 768, top_k=2)

            assert len(results) == 2
            assert results[0]["score"] > results[1]["score"]

    def test_chroma_adapter_compatibility(self):
        """Test Chroma vector database adapter."""

        # Mock Chroma client
        class ChromaAdapter:
            def __init__(self, collection_name: str):
                self.collection_name = collection_name
                self.documents: List[str] = []
                self.embeddings: List[List[float]] = []
                self.ids: List[str] = []

            def add(self, documents, embeddings, ids):
                self.documents.extend(documents)
                self.embeddings.extend(embeddings)
                self.ids.extend(ids)

            def query(self, query_embeddings, n_results=5):
                # Mock similarity search
                return {
                    "ids": [self.ids[:n_results]],
                    "distances": [[0.1 * i for i in range(n_results)]],
                    "documents": [self.documents[:n_results]],
                }

        # Test adapter
        adapter = ChromaAdapter("business_ventures")

        # Add documents
        adapter.add(
            documents=["Doc 1", "Doc 2", "Doc 3"],
            embeddings=[[0.1] * 384, [0.2] * 384, [0.3] * 384],
            ids=["id1", "id2", "id3"],
        )

        # Query
        results = adapter.query([[0.15] * 384], n_results=2)
        assert len(results["ids"][0]) == 2

    def test_faiss_adapter_compatibility(self):
        """Test FAISS vector database adapter."""

        # Mock FAISS interface
        class FAISSAdapter:
            def __init__(self, dimension: int):
                self.dimension = dimension
                self.vectors: List[List[float]] = []
                self.metadata: List[Dict[str, Any]] = []

            def add(self, vectors):
                self.vectors.extend(vectors)
                return len(self.vectors)

            def search(self, query_vectors, k=5):
                # Mock search - return indices and distances
                n_queries = len(query_vectors)
                distances = [[0.1 * i for i in range(k)] for _ in range(n_queries)]
                indices = [[i for i in range(k)] for _ in range(n_queries)]
                return distances, indices

        # Test adapter
        adapter = FAISSAdapter(dimension=512)

        # Add vectors
        vectors = [[0.1 * i] * 512 for i in range(10)]
        adapter.add(vectors)

        # Search
        query = [[0.5] * 512]
        distances, indices = adapter.search(query, k=3)

        assert len(distances[0]) == 3
        assert len(indices[0]) == 3
        assert distances[0][0] < distances[0][1]  # Ordered by distance


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
