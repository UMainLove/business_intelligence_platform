"""
Synthetic tests for RAG and document tools without external dependencies.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from src.tools.document_tools import DocumentGenerator
from src.tools.rag_tools import (
    Document,
    MarketResearchRAG,
    initialize_sample_data,
    rag_tool_executor,
)


class TestDocument:
    """Test Document dataclass."""

    def test_document_creation(self):
        """Test creating a Document instance."""
        doc = Document(
            id="test123",
            title="Test Document",
            content="Test content",
            metadata={"type": "test", "date": "2024-01-01"},
            embedding=[0.1, 0.2, 0.3],
        )

        assert doc.id == "test123"
        assert doc.title == "Test Document"
        assert doc.content == "Test content"
        assert doc.metadata["type"] == "test"
        assert doc.embedding == [0.1, 0.2, 0.3]

    def test_document_creation_no_embedding(self):
        """Test creating a Document without embedding."""
        doc = Document(
            id="test123", title="Test Document", content="Test content", metadata={"type": "test"}
        )

        assert doc.embedding is None


class TestMarketResearchRAG:
    """Test MarketResearchRAG with synthetic data."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.rag = MarketResearchRAG(self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_generate_id(self):
        """Test document ID generation."""
        content = "Test content for ID generation"
        doc_id = self.rag.generate_id(content)

        assert isinstance(doc_id, str)
        assert len(doc_id) == 12  # First 12 chars of SHA-256

        # Same content should generate same ID
        doc_id2 = self.rag.generate_id(content)
        assert doc_id == doc_id2

    def test_add_document(self):
        """Test adding a document."""
        doc_id = self.rag.add_document(
            title="Test Doc", content="Test content", metadata={"type": "test"}
        )

        assert isinstance(doc_id, str)
        assert len(self.rag.documents) == 1
        assert self.rag.documents[0].title == "Test Doc"
        assert self.rag.documents[0].content == "Test content"

    def test_search_basic(self):
        """Test basic keyword search."""
        # Add test documents
        self.rag.add_document(
            "AI Research", "Artificial intelligence and machine learning", {"type": "research"}
        )
        self.rag.add_document(
            "Market Analysis", "E-commerce market trends and growth", {"type": "market"}
        )
        self.rag.add_document(
            "Tech Report", "Artificial intelligence applications in business", {"type": "tech"}
        )

        # Search for AI-related content
        results = self.rag.search("artificial intelligence", top_k=2)

        assert len(results) == 2
        assert all("artificial intelligence" in doc.content.lower() for doc in results)

    def test_search_no_results(self):
        """Test search with no matching results."""
        self.rag.add_document("Test Doc", "Some content", {"type": "test"})

        results = self.rag.search("nonexistent keyword")
        assert len(results) == 0

    def test_save_and_load_documents(self):
        """Test document persistence."""
        # Add a document
        self.rag.add_document("Test Doc", "Test content", {"type": "test"})

        # Create new RAG instance with same storage path
        new_rag = MarketResearchRAG(self.temp_dir)

        # Should load the existing document
        assert len(new_rag.documents) == 1
        assert new_rag.documents[0].content == "Test content"

    def test_add_market_research(self):
        """Test adding market research data."""
        data = {
            "market_size": "$100B",
            "growth_rate": "20%",
            "date": "2024-01-01",
            "source": "Test Source",
        }

        doc_id = self.rag.add_market_research("AI", data)

        assert isinstance(doc_id, str)
        assert len(self.rag.documents) == 1
        assert self.rag.documents[0].title == "Market Research: AI"
        assert self.rag.documents[0].metadata["type"] == "market_research"
        assert self.rag.documents[0].metadata["industry"] == "AI"

    def test_add_competitor_analysis(self):
        """Test adding competitor analysis."""
        analysis = {
            "market_cap": "$10B",
            "strengths": ["Innovation", "Market share"],
            "date": "2024-01-01",
        }

        doc_id = self.rag.add_competitor_analysis("TechCorp", analysis)

        assert isinstance(doc_id, str)
        assert len(self.rag.documents) == 1
        assert self.rag.documents[0].title == "Competitor Analysis: TechCorp"
        assert self.rag.documents[0].metadata["type"] == "competitor_analysis"
        assert self.rag.documents[0].metadata["company"] == "TechCorp"

    def test_add_industry_report(self):
        """Test adding industry report."""
        doc_id = self.rag.add_industry_report(
            "AI Industry Report 2024",
            "Comprehensive analysis of AI industry trends",
            {"source": "Industry Analytics", "year": 2024},
        )

        assert isinstance(doc_id, str)
        assert len(self.rag.documents) == 1
        assert self.rag.documents[0].metadata["type"] == "industry_report"
        assert self.rag.documents[0].metadata["year"] == 2024

    def test_get_market_insights(self):
        """Test getting market insights."""
        # Add test data
        market_data = {"market_size": "$100B", "trends": ["AI growth"]}
        self.rag.add_market_research("AI", market_data)
        self.rag.add_competitor_analysis("TechCorp", {"strengths": ["Innovation"]})

        insights = self.rag.get_market_insights("AI technology")

        assert "query" in insights
        assert "sources" in insights
        assert "market_data" in insights
        assert "competitors" in insights
        assert insights["query"] == "AI technology"


class TestInitializeSampleData:
    """Test sample data initialization."""

    def test_initialize_sample_data(self):
        """Test sample data initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            rag = MarketResearchRAG(temp_dir)

            # Should start empty
            assert len(rag.documents) == 0

            initialize_sample_data(rag)

            # Should now have sample documents
            assert len(rag.documents) > 0

            # Check for expected document types
            doc_types = {doc.metadata.get("type") for doc in rag.documents}
            assert "market_research" in doc_types
            assert "competitor_analysis" in doc_types


class TestRAGToolExecutor:
    """Test RAG tool executor."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("src.tools.rag_tools.MarketResearchRAG")
    def test_search_action(self, mock_rag_class):
        """Test search action through executor."""
        # Mock the RAG instance
        mock_rag = Mock()
        mock_doc = Mock()
        mock_doc.title = "Test Doc"
        mock_doc.content = "Test content"
        mock_doc.metadata = {"type": "test"}
        mock_rag.search.return_value = [mock_doc]
        mock_rag.documents = [mock_doc]  # Not empty, so no sample data init
        mock_rag_class.return_value = mock_rag

        result = rag_tool_executor("search", {"query": "test", "top_k": 5})

        assert "results" in result
        assert len(result["results"]) == 1
        assert result["results"][0]["title"] == "Test Doc"

    @patch("src.tools.rag_tools.MarketResearchRAG")
    def test_add_research_action(self, mock_rag_class):
        """Test add_research action through executor."""
        mock_rag = Mock()
        mock_rag.add_market_research.return_value = "test123"
        mock_rag.documents = ["dummy"]  # Not empty
        mock_rag_class.return_value = mock_rag

        result = rag_tool_executor(
            "add_research", {"industry": "AI", "data": {"market_size": "$100B"}}
        )

        assert result["success"] is True
        assert result["document_id"] == "test123"

    @patch("src.tools.rag_tools.MarketResearchRAG")
    def test_unknown_action(self, mock_rag_class):
        """Test unknown action handling."""
        mock_rag = Mock()
        mock_rag.documents = ["dummy"]
        mock_rag_class.return_value = mock_rag

        result = rag_tool_executor("unknown_action", {})

        assert "error" in result
        assert "Unknown action" in result["error"]


class TestDocumentGenerator:
    """Test DocumentGenerator with synthetic data."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.doc_gen = DocumentGenerator(self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_document_generator_creation(self):
        """Test DocumentGenerator initialization."""
        assert self.doc_gen.output_dir.exists()
        assert str(self.doc_gen.output_dir) == self.temp_dir

    def test_generate_market_analysis_report(self):
        """Test market analysis report generation."""
        market_data = {
            "industry": "AI Technology",
            "market_size": "$100B",
            "growth_rate": "25%",
            "trends": [
                {"name": "GenAI", "description": "Generative AI adoption"},
                {"name": "AutoML", "description": "Automated machine learning"},
            ],
            "competitors": [
                {"name": "TechCorp", "description": "Leading AI company"},
                {"name": "InnovateAI", "description": "AI startup leader"},
            ],
            "opportunities": "Huge growth potential",
            "challenges": "Regulatory concerns",
            "recommendations": "Focus on enterprise solutions",
        }

        result = self.doc_gen.generate_market_analysis_report(market_data)

        assert result["document_type"] == "market_analysis"
        assert "filename" in result
        assert result["filename"].startswith("market_analysis_")  # Secure hashed filename
        assert result["filename"].endswith(".md")
        assert result["original_identifier"] == "AI Technology"  # Original preserved for testing
        assert "content" in result
        assert "AI Technology" in result["content"]
        assert "GenAI" in result["content"]
        assert "TechCorp" in result["content"]

    def test_generate_financial_model(self):
        """Test financial model generation."""
        financial_data = {
            "business_name": "AI Startup",
            "revenue_projections": {"1": 100000, "2": 150000, "3": 225000},
            "metrics": {"profit_margin": 25.5, "burn_rate": 50000, "customer_count": 150},
            "assumptions": "Conservative growth estimates",
            "funding_requirements": "$500K seed round needed",
        }

        result = self.doc_gen.generate_financial_model(financial_data)

        assert result["document_type"] == "financial_model"
        assert result["filename"].startswith("financial_model_")  # Secure hashed filename
        assert result["original_identifier"] == "AI Startup"  # Original preserved for testing
        assert "AI Startup" in result["content"]
        assert "Year 1:** $100,000" in result["content"]
        assert "Conservative growth estimates" in result["content"]

    def test_generate_risk_assessment(self):
        """Test risk assessment generation."""
        risk_data = {
            "business_name": "Tech Venture",
            "market_risks": [
                {
                    "name": "Market Risk",
                    "impact": "High",
                    "probability": "Medium",
                    "description": "Market saturation concerns",
                }
            ],
            "technology_risks": [
                {
                    "name": "Technical Risk",
                    "impact": "Medium",
                    "probability": "Low",
                    "description": "Technology implementation challenges",
                }
            ],
            "mitigation_strategies": "Diversification and contingency planning",
            "executive_summary": "Moderate risk level assessment",
        }

        result = self.doc_gen.generate_risk_assessment(risk_data)

        assert result["document_type"] == "risk_assessment"
        assert "Tech Venture" in result["content"]
        assert "Market Risk" in result["content"]
        assert "Market saturation concerns" in result["content"]
        assert "Diversification and contingency planning" in result["content"]

    def test_generate_business_plan(self):
        """Test business plan generation."""
        plan_data = {
            "name": "InnovateTech",  # Use 'name' not 'business_name'
            "executive_summary": "Revolutionary AI platform",
            "market_analysis": "Large addressable market",
            "products_services": "AI-powered analytics platform",
            "marketing_strategy": "Digital marketing and partnerships",
            "operations_plan": "Remote-first team structure",
            "financial_projections": "Profitable by year 3",
            "funding_request": "$1M Series A",
            "appendices": "Technical specifications attached",
        }

        result = self.doc_gen.generate_business_plan(plan_data)

        assert result["document_type"] == "business_plan"
        assert "InnovateTech" in result["content"]
        assert "Revolutionary AI platform" in result["content"]
        assert "Large addressable market" in result["content"]

    def test_file_creation(self):
        """Test that files are actually created."""
        market_data = {"industry": "Test Industry"}
        result = self.doc_gen.generate_market_analysis_report(market_data)

        file_path = Path(result["file_path"])
        assert file_path.exists()
        assert file_path.is_file()

        # Read file content
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "Test Industry" in content

    def test_word_count(self):
        """Test word count calculation."""
        market_data = {"industry": "Test", "market_size": "Large"}
        result = self.doc_gen.generate_market_analysis_report(market_data)

        assert "word_count" in result
        assert isinstance(result["word_count"], int)
        assert result["word_count"] > 0
