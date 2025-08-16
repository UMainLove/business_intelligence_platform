"""
Comprehensive synthetic tests for sequential_validation.py to achieve 95%+ coverage.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
import json
from typing import Dict, Any

from src.workflows.sequential_validation import (
    SequentialValidationWorkflow,
    ValidationPhase,
    PhaseResult
)


class TestValidationPhase:
    """Test ValidationPhase data class."""

    def test_validation_phase_creation(self):
        """Test creating a ValidationPhase."""
        phase = ValidationPhase(
            name="Market Research",
            description="Analyze market opportunity",
            validator=lambda x: {"valid": True},
            weight=0.25
        )
        
        assert phase.name == "Market Research"
        assert phase.description == "Analyze market opportunity"
        assert phase.weight == 0.25
        assert callable(phase.validator)

    def test_validation_phase_defaults(self):
        """Test ValidationPhase with default values."""
        phase = ValidationPhase(
            name="Test Phase",
            description="Test description",
            validator=lambda x: {"valid": True}
        )
        
        # Default weight should be 1.0
        assert phase.weight == 1.0


class TestPhaseResult:
    """Test PhaseResult data class."""

    def test_phase_result_creation(self):
        """Test creating a PhaseResult."""
        result = PhaseResult(
            phase_name="Financial Analysis",
            passed=True,
            score=0.85,
            findings={"revenue": "Strong potential"},
            recommendations=["Focus on B2B market"]
        )
        
        assert result.phase_name == "Financial Analysis"
        assert result.passed is True
        assert result.score == 0.85
        assert result.findings == {"revenue": "Strong potential"}
        assert result.recommendations == ["Focus on B2B market"]

    def test_phase_result_failed(self):
        """Test PhaseResult for failed validation."""
        result = PhaseResult(
            phase_name="Legal Review",
            passed=False,
            score=0.3,
            findings={"compliance": "Major issues"},
            recommendations=["Seek legal counsel"]
        )
        
        assert result.passed is False
        assert result.score == 0.3


class TestValidationReport:
    """Test ValidationReport data class."""

    def test_validation_report_creation(self):
        """Test creating a ValidationReport."""
        phase_results = [
            PhaseResult("Market", True, 0.9, {}, []),
            PhaseResult("Financial", True, 0.8, {}, [])
        ]
        
        report = ValidationReport(
            overall_score=0.85,
            passed=True,
            phase_results=phase_results,
            executive_summary="Strong business case",
            next_steps=["Proceed to implementation"]
        )
        
        assert report.overall_score == 0.85
        assert report.passed is True
        assert len(report.phase_results) == 2
        assert report.executive_summary == "Strong business case"
        assert report.next_steps == ["Proceed to implementation"]

    def test_validation_report_to_dict(self):
        """Test converting ValidationReport to dictionary."""
        phase_results = [
            PhaseResult("Market", True, 0.9, {"size": "Large"}, ["Expand"])
        ]
        
        report = ValidationReport(
            overall_score=0.9,
            passed=True,
            phase_results=phase_results,
            executive_summary="Excellent opportunity",
            next_steps=["Launch"]
        )
        
        # ValidationReport should be convertible to dict
        assert hasattr(report, '__dict__')
        report_dict = vars(report)
        assert 'overall_score' in report_dict
        assert 'phase_results' in report_dict


class TestSequentialValidationWorkflow:
    """Test SequentialValidationWorkflow class."""

    def test_workflow_initialization(self):
        """Test workflow initialization."""
        business_data = {
            "idea": "AI Platform",
            "market": "B2B SaaS",
            "revenue_model": "Subscription"
        }
        
        workflow = SequentialValidationWorkflow(business_data)
        
        assert workflow.business_data == business_data
        assert workflow.phases is not None
        assert len(workflow.phases) > 0

    @patch('src.workflows.sequential_validation.ConversableAgent')
    def test_create_validator_agent(self, mock_agent_class):
        """Test creating a validator agent."""
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent
        
        workflow = SequentialValidationWorkflow({"idea": "Test"})
        
        agent = workflow._create_validator_agent(
            name="MarketValidator",
            system_message="Validate market"
        )
        
        assert agent == mock_agent
        mock_agent_class.assert_called_once()

    def test_define_validation_phases(self):
        """Test defining validation phases."""
        workflow = SequentialValidationWorkflow({"idea": "Test"})
        
        phases = workflow._define_validation_phases()
        
        assert isinstance(phases, list)
        assert len(phases) == 7  # Should have 7 phases
        
        phase_names = [p.name for p in phases]
        assert "Market Research" in phase_names
        assert "Financial Modeling" in phase_names
        assert "Legal & Regulatory" in phase_names
        assert "Technical Feasibility" in phase_names
        assert "Competitive Analysis" in phase_names
        assert "Risk Assessment" in phase_names
        assert "Strategic Planning" in phase_names

    @patch('src.workflows.sequential_validation.ConversableAgent')
    def test_validate_market_research(self, mock_agent_class):
        """Test market research validation phase."""
        mock_agent = Mock()
        mock_reply = json.dumps({
            "tam": "$10B",
            "sam": "$1B",
            "som": "$100M",
            "growth_rate": "25%",
            "validation_passed": True,
            "confidence_score": 0.85
        })
        mock_agent.generate_reply.return_value = mock_reply
        mock_agent_class.return_value = mock_agent
        
        workflow = SequentialValidationWorkflow({"idea": "Test", "market": "B2B"})
        
        result = workflow._validate_market_research({"idea": "Test"})
        
        assert result["validation_passed"] is True
        assert result["confidence_score"] == 0.85
        assert result["tam"] == "$10B"

    @patch('src.workflows.sequential_validation.ConversableAgent')
    def test_validate_financial_modeling(self, mock_agent_class):
        """Test financial modeling validation phase."""
        mock_agent = Mock()
        mock_reply = json.dumps({
            "revenue_projections": "$1M Year 1",
            "unit_economics": "LTV:CAC = 3:1",
            "break_even": "Month 18",
            "validation_passed": True,
            "confidence_score": 0.75
        })
        mock_agent.generate_reply.return_value = mock_reply
        mock_agent_class.return_value = mock_agent
        
        workflow = SequentialValidationWorkflow({"idea": "Test"})
        
        result = workflow._validate_financial_modeling({"idea": "Test"})
        
        assert result["validation_passed"] is True
        assert result["confidence_score"] == 0.75
        assert "break_even" in result

    @patch('src.workflows.sequential_validation.ConversableAgent')
    def test_validate_legal_regulatory(self, mock_agent_class):
        """Test legal and regulatory validation phase."""
        mock_agent = Mock()
        mock_reply = json.dumps({
            "compliance_requirements": ["GDPR", "SOC2"],
            "legal_risks": "Low",
            "validation_passed": True,
            "confidence_score": 0.9
        })
        mock_agent.generate_reply.return_value = mock_reply
        mock_agent_class.return_value = mock_agent
        
        workflow = SequentialValidationWorkflow({"idea": "Test"})
        
        result = workflow._validate_legal_regulatory({"idea": "Test"})
        
        assert result["validation_passed"] is True
        assert result["legal_risks"] == "Low"

    @patch('src.workflows.sequential_validation.ConversableAgent')
    def test_validate_technical_feasibility(self, mock_agent_class):
        """Test technical feasibility validation phase."""
        mock_agent = Mock()
        mock_reply = json.dumps({
            "technical_requirements": "Standard cloud infrastructure",
            "development_complexity": "Medium",
            "validation_passed": True,
            "confidence_score": 0.8
        })
        mock_agent.generate_reply.return_value = mock_reply
        mock_agent_class.return_value = mock_agent
        
        workflow = SequentialValidationWorkflow({"idea": "Test"})
        
        result = workflow._validate_technical_feasibility({"idea": "Test"})
        
        assert result["validation_passed"] is True
        assert result["development_complexity"] == "Medium"

    @patch('src.workflows.sequential_validation.ConversableAgent')
    def test_validate_competitive_analysis(self, mock_agent_class):
        """Test competitive analysis validation phase."""
        mock_agent = Mock()
        mock_reply = json.dumps({
            "competitors": ["Company A", "Company B"],
            "differentiation": "Strong AI capabilities",
            "validation_passed": True,
            "confidence_score": 0.7
        })
        mock_agent.generate_reply.return_value = mock_reply
        mock_agent_class.return_value = mock_agent
        
        workflow = SequentialValidationWorkflow({"idea": "Test"})
        
        result = workflow._validate_competitive_analysis({"idea": "Test"})
        
        assert result["validation_passed"] is True
        assert len(result["competitors"]) == 2

    @patch('src.workflows.sequential_validation.ConversableAgent')
    def test_validate_risk_assessment(self, mock_agent_class):
        """Test risk assessment validation phase."""
        mock_agent = Mock()
        mock_reply = json.dumps({
            "key_risks": ["Market timing", "Funding"],
            "risk_mitigation": "Phased approach",
            "validation_passed": True,
            "confidence_score": 0.65
        })
        mock_agent.generate_reply.return_value = mock_reply
        mock_agent_class.return_value = mock_agent
        
        workflow = SequentialValidationWorkflow({"idea": "Test"})
        
        result = workflow._validate_risk_assessment({"idea": "Test"})
        
        assert result["validation_passed"] is True
        assert "Market timing" in result["key_risks"]

    @patch('src.workflows.sequential_validation.ConversableAgent')
    def test_validate_strategic_planning(self, mock_agent_class):
        """Test strategic planning validation phase."""
        mock_agent = Mock()
        mock_reply = json.dumps({
            "go_to_market": "Direct sales + partnerships",
            "milestones": ["MVP in Q1", "Launch in Q2"],
            "validation_passed": True,
            "confidence_score": 0.8
        })
        mock_agent.generate_reply.return_value = mock_reply
        mock_agent_class.return_value = mock_agent
        
        workflow = SequentialValidationWorkflow({"idea": "Test"})
        
        result = workflow._validate_strategic_planning({"idea": "Test"})
        
        assert result["validation_passed"] is True
        assert len(result["milestones"]) == 2

    def test_calculate_overall_score(self):
        """Test calculating overall validation score."""
        workflow = SequentialValidationWorkflow({"idea": "Test"})
        
        phase_results = [
            PhaseResult("Phase1", True, 0.9, {}, []),
            PhaseResult("Phase2", True, 0.8, {}, []),
            PhaseResult("Phase3", False, 0.4, {}, [])
        ]
        
        # Mock phases with weights
        workflow.phases = [
            ValidationPhase("Phase1", "", lambda x: {}, 1.0),
            ValidationPhase("Phase2", "", lambda x: {}, 1.0),
            ValidationPhase("Phase3", "", lambda x: {}, 1.0)
        ]
        
        score = workflow._calculate_overall_score(phase_results)
        
        # Average of 0.9, 0.8, 0.4 = 0.7
        assert score == pytest.approx(0.7, rel=0.01)

    def test_generate_executive_summary(self):
        """Test generating executive summary."""
        workflow = SequentialValidationWorkflow({"idea": "AI Platform"})
        
        phase_results = [
            PhaseResult("Market Research", True, 0.9, 
                       {"tam": "$10B"}, ["Focus on enterprise"]),
            PhaseResult("Financial Modeling", True, 0.8,
                       {"break_even": "Month 18"}, ["Optimize pricing"])
        ]
        
        summary = workflow._generate_executive_summary(phase_results, 0.85)
        
        assert isinstance(summary, str)
        assert len(summary) > 0
        assert "validation" in summary.lower() or "score" in summary.lower()

    def test_generate_next_steps(self):
        """Test generating next steps."""
        workflow = SequentialValidationWorkflow({"idea": "Test"})
        
        phase_results = [
            PhaseResult("Market", True, 0.9, {}, ["Research competitors"]),
            PhaseResult("Financial", True, 0.8, {}, ["Refine pricing model"])
        ]
        
        next_steps = workflow._generate_next_steps(phase_results, 0.85)
        
        assert isinstance(next_steps, list)
        assert len(next_steps) > 0

    @patch('src.workflows.sequential_validation.logger')
    def test_run_validation_with_logging(self, mock_logger):
        """Test running validation with logging."""
        workflow = SequentialValidationWorkflow({"idea": "Test"})
        
        # Mock all validation methods
        with patch.object(workflow, '_validate_market_research') as mock_market:
            with patch.object(workflow, '_validate_financial_modeling') as mock_financial:
                mock_market.return_value = {"validation_passed": True, "confidence_score": 0.9}
                mock_financial.return_value = {"validation_passed": True, "confidence_score": 0.8}
                
                # Mock other phases to return simple results
                workflow.phases = workflow.phases[:2]  # Only use first 2 phases
                
                report = workflow.run_validation()
                
                # Should log phase execution
                assert mock_logger.info.called
                assert isinstance(report, ValidationReport)

    def test_run_validation_with_failure(self):
        """Test validation with failed phases."""
        workflow = SequentialValidationWorkflow({"idea": "Test"})
        
        # Mock validation to fail
        with patch.object(workflow, '_validate_market_research') as mock_market:
            mock_market.return_value = {"validation_passed": False, "confidence_score": 0.3}
            
            # Only run one phase
            workflow.phases = workflow.phases[:1]
            
            report = workflow.run_validation()
            
            assert report.overall_score < 0.5
            assert len(report.phase_results) == 1
            assert report.phase_results[0].passed is False

    def test_validation_with_json_parse_error(self):
        """Test handling JSON parse errors in validation."""
        workflow = SequentialValidationWorkflow({"idea": "Test"})
        
        with patch('src.workflows.sequential_validation.ConversableAgent') as mock_agent_class:
            mock_agent = Mock()
            mock_agent.generate_reply.return_value = "Invalid JSON"
            mock_agent_class.return_value = mock_agent
            
            result = workflow._validate_market_research({"idea": "Test"})
            
            # Should return error result
            assert result["validation_passed"] is False
            assert "error" in result

    def test_workflow_with_empty_business_data(self):
        """Test workflow with empty business data."""
        workflow = SequentialValidationWorkflow({})
        
        assert workflow.business_data == {}
        assert len(workflow.phases) == 7

    def test_phase_weight_calculation(self):
        """Test that phase weights are properly considered."""
        workflow = SequentialValidationWorkflow({"idea": "Test"})
        
        # Create phases with different weights
        phase_results = [
            PhaseResult("High Weight", True, 1.0, {}, []),
            PhaseResult("Low Weight", False, 0.0, {}, [])
        ]
        
        workflow.phases = [
            ValidationPhase("High Weight", "", lambda x: {}, weight=0.9),
            ValidationPhase("Low Weight", "", lambda x: {}, weight=0.1)
        ]
        
        score = workflow._calculate_overall_score(phase_results)
        
        # Weighted average: (1.0 * 0.9 + 0.0 * 0.1) / 1.0 = 0.9
        assert score == pytest.approx(0.9, rel=0.01)

    def test_validation_report_serialization(self):
        """Test that ValidationReport can be serialized."""
        phase_results = [
            PhaseResult("Test", True, 0.8, {"key": "value"}, ["recommendation"])
        ]
        
        report = ValidationReport(
            overall_score=0.8,
            passed=True,
            phase_results=phase_results,
            executive_summary="Summary",
            next_steps=["Step 1"]
        )
        
        # Should be serializable to dict
        report_dict = {
            "overall_score": report.overall_score,
            "passed": report.passed,
            "executive_summary": report.executive_summary,
            "next_steps": report.next_steps,
            "phase_results": [
                {
                    "phase_name": pr.phase_name,
                    "passed": pr.passed,
                    "score": pr.score,
                    "findings": pr.findings,
                    "recommendations": pr.recommendations
                }
                for pr in report.phase_results
            ]
        }
        
        assert report_dict["overall_score"] == 0.8
        assert len(report_dict["phase_results"]) == 1


class TestValidationIntegration:
    """Test complete validation workflow integration."""

    @patch('src.workflows.sequential_validation.ConversableAgent')
    def test_full_validation_workflow(self, mock_agent_class):
        """Test complete validation workflow from start to finish."""
        # Setup mock agent
        mock_agent = Mock()
        
        # Mock different responses for different phases
        responses = [
            json.dumps({"validation_passed": True, "confidence_score": 0.9, "tam": "$10B"}),
            json.dumps({"validation_passed": True, "confidence_score": 0.85, "break_even": "Month 18"}),
            json.dumps({"validation_passed": True, "confidence_score": 0.8, "legal_risks": "Low"}),
            json.dumps({"validation_passed": True, "confidence_score": 0.75, "complexity": "Medium"}),
            json.dumps({"validation_passed": True, "confidence_score": 0.7, "competitors": []}),
            json.dumps({"validation_passed": False, "confidence_score": 0.4, "key_risks": ["High"]}),
            json.dumps({"validation_passed": True, "confidence_score": 0.8, "milestones": []})
        ]
        
        mock_agent.generate_reply.side_effect = responses
        mock_agent_class.return_value = mock_agent
        
        # Run workflow
        business_data = {
            "idea": "AI-powered analytics platform",
            "market": "B2B SaaS",
            "target_customers": "Enterprise",
            "revenue_model": "Subscription"
        }
        
        workflow = SequentialValidationWorkflow(business_data)
        report = workflow.run_validation()
        
        # Verify report
        assert isinstance(report, ValidationReport)
        assert len(report.phase_results) == 7
        assert report.overall_score > 0
        assert isinstance(report.executive_summary, str)
        assert isinstance(report.next_steps, list)
        
        # Check that one phase failed
        failed_phases = [pr for pr in report.phase_results if not pr.passed]
        assert len(failed_phases) == 1

    def test_validation_with_exception_handling(self):
        """Test that exceptions are handled gracefully."""
        workflow = SequentialValidationWorkflow({"idea": "Test"})
        
        # Mock a phase to raise an exception
        with patch.object(workflow, '_validate_market_research') as mock_validate:
            mock_validate.side_effect = Exception("Network error")
            
            # Only test first phase
            workflow.phases = workflow.phases[:1]
            
            report = workflow.run_validation()
            
            # Should still return a report, but with error
            assert isinstance(report, ValidationReport)
            assert report.phase_results[0].passed is False
            assert "error" in report.phase_results[0].findings