"""
RAG (Retrieval-Augmented Generation) tools for market research.
"""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

# For production, you'd use proper vector DB like Pinecone, Chroma, or FAISS
# This is a simple in-memory implementation for demonstration


@dataclass
class Document:
    """Document for RAG system."""

    id: str
    title: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None


class MarketResearchRAG:
    """RAG system for market research and competitive analysis."""

    def __init__(self, storage_path: str = "data/rag"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.documents: List[Document] = []
        self.load_documents()

    def generate_id(self, content: str) -> str:
        """Generate unique ID for document using SHA-256."""
        return hashlib.sha256(content.encode()).hexdigest()[:12]

    def add_document(self, title: str, content: str, metadata: Dict[str, Any] = None) -> str:
        """Add a document to the RAG system."""
        doc_id = self.generate_id(content)
        doc = Document(id=doc_id, title=title, content=content, metadata=metadata or {})
        self.documents.append(doc)
        self.save_documents()
        return doc_id

    def search(self, query: str, top_k: int = 5) -> List[Document]:
        """
        Simple keyword-based search.
        In production, use vector similarity search with embeddings.
        """
        query_terms = query.lower().split()
        scores = []

        for doc in self.documents:
            score = 0
            doc_text = (doc.title + " " + doc.content).lower()

            for term in query_terms:
                score += doc_text.count(term)

            if score > 0:
                scores.append((score, doc))

        # Sort by score and return top_k
        scores.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scores[:top_k]]

    def save_documents(self):
        """Persist documents to disk using JSON."""
        save_path = self.storage_path / "documents.json"
        # Convert documents to serializable format
        serializable_docs = []
        for doc in self.documents:
            serializable_docs.append(
                {"id": doc.id, "content": doc.content, "metadata": doc.metadata}
            )

        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(serializable_docs, f, indent=2, ensure_ascii=False)

    def load_documents(self):
        """Load documents from disk using JSON."""
        save_path = self.storage_path / "documents.json"
        if save_path.exists():
            with open(save_path, "r", encoding="utf-8") as f:
                docs_data = json.load(f)
                self.documents = [
                    Document(id=doc["id"], content=doc["content"], metadata=doc["metadata"])
                    for doc in docs_data
                ]

    def add_market_research(self, industry: str, data: Dict[str, Any]) -> str:
        """Add market research data."""
        content = json.dumps(data, indent=2)
        metadata = {
            "type": "market_research",
            "industry": industry,
            "date": data.get("date", ""),
            "source": data.get("source", ""),
        }
        return self.add_document(
            title=f"Market Research: {industry}", content=content, metadata=metadata
        )

    def add_competitor_analysis(self, company: str, analysis: Dict[str, Any]) -> str:
        """Add competitor analysis."""
        content = json.dumps(analysis, indent=2)
        metadata = {
            "type": "competitor_analysis",
            "company": company,
            "date": analysis.get("date", ""),
            "market_cap": analysis.get("market_cap", ""),
        }
        return self.add_document(
            title=f"Competitor Analysis: {company}", content=content, metadata=metadata
        )

    def add_industry_report(self, title: str, report: str, metadata: Dict[str, Any] = None) -> str:
        """Add industry report."""
        meta = metadata or {}
        meta["type"] = "industry_report"
        return self.add_document(title=title, content=report, metadata=meta)

    def get_market_insights(self, query: str) -> Dict[str, Any]:
        """Get market insights based on query."""
        relevant_docs = self.search(query, top_k=3)

        insights = {
            "query": query,
            "sources": [],
            "key_findings": [],
            "market_data": {},
            "competitors": [],
        }

        for doc in relevant_docs:
            insights["sources"].append(
                {"title": doc.title, "type": doc.metadata.get("type", "unknown")}
            )

            # Extract specific insights based on document type
            if doc.metadata.get("type") == "market_research":
                try:
                    data = json.loads(doc.content)
                    insights["market_data"].update(data)
                except BaseException:
                    pass

            elif doc.metadata.get("type") == "competitor_analysis":
                insights["competitors"].append(doc.metadata.get("company", "Unknown"))

        return insights


# Pre-populate with sample market data


def initialize_sample_data(rag: MarketResearchRAG):
    """Initialize RAG with sample market research data."""

    # Sample market research data
    rag.add_market_research(
        "SaaS",
        {
            "market_size": "$195 billion (2023)",
            "growth_rate": "18% CAGR",
            "key_trends": ["AI integration", "Vertical SaaS", "Low-code/No-code platforms"],
            "date": "2024",
            "source": "Industry Report",
        },
    )

    rag.add_market_research(
        "E-commerce",
        {
            "market_size": "$6.3 trillion (2023)",
            "growth_rate": "9.7% CAGR",
            "key_trends": ["Social commerce", "Sustainable shopping", "AR/VR experiences"],
            "date": "2024",
            "source": "Market Analysis",
        },
    )

    # Sample competitor analysis
    rag.add_competitor_analysis(
        "Shopify",
        {
            "market_cap": "$90 billion",
            "revenue": "$7.06 billion (2023)",
            "strengths": ["Platform ecosystem", "Developer friendly", "Multi-channel"],
            "weaknesses": ["High competition", "Dependency on SMBs"],
            "date": "2024",
        },
    )


def create_rag_tool_spec():
    """Create tool specification for AG2 integration."""
    return {
        "name": "market_research_rag",
        "description": "Search and retrieve market research, competitor analysis, and industry reports",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["search", "add_research", "add_competitor", "get_insights"],
                    "description": "The RAG action to perform",
                },
                "params": {"type": "object", "description": "Parameters specific to the action"},
            },
            "required": ["action", "params"],
        },
    }


def rag_tool_executor(action: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute RAG tool operations for AG2."""
    rag = MarketResearchRAG()

    # Initialize with sample data if empty
    if not rag.documents:
        initialize_sample_data(rag)

    if action == "search":
        results = rag.search(params["query"], params.get("top_k", 5))
        return {
            "results": [
                {
                    "title": doc.title,
                    "content": doc.content[:500],  # Truncate for response
                    "metadata": doc.metadata,
                }
                for doc in results
            ]
        }

    elif action == "add_research":
        doc_id = rag.add_market_research(params["industry"], params["data"])
        return {"success": True, "document_id": doc_id}

    elif action == "add_competitor":
        doc_id = rag.add_competitor_analysis(params["company"], params["analysis"])
        return {"success": True, "document_id": doc_id}

    elif action == "get_insights":
        return rag.get_market_insights(params["query"])

    else:
        return {"error": f"Unknown action: {action}"}
