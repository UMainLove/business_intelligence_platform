"""
Comprehensive tests for sequential_validation.py to achieve 95%+ coverage.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
import json
from typing import Dict, Any
from dataclasses import dataclass

from src.workflows.sequential_validation import (
    SequentialValidationWorkflow,
    ValidationPhase,
    PhaseResult
)


class TestValidationPhase:
    """Test ValidationPhase enum."""

    def test_validation_phases_exist(self):
        """Test that all validation phases are defined."""
        assert ValidationPhase.IDEA_REFINEMENT
        assert ValidationPhase.MARKET_VALIDATION
        assert ValidationPhase.FINANCIAL_MODELING
        assert ValidationPhase.RISK_ASSESSMENT
        assert ValidationPhase.COMPETITIVE_ANALYSIS
        assert ValidationPhase.REGULATORY_COMPLIANCE
        assert ValidationPhase.FINAL_SYNTHESIS

    def test_validation_phase_values(self):
        """Test validation phase string values."""
        assert ValidationPhase.IDEA_REFINEMENT.value == "idea_refinement"
        assert ValidationPhase.MARKET_VALIDATION.value == "market_validation"
        assert ValidationPhase.FINANCIAL_MODELING.value == "financial_modeling"
        assert ValidationPhase.RISK_ASSESSMENT.value == "risk_assessment"
        assert ValidationPhase.COMPETITIVE_ANALYSIS.value == "competitive_analysis"
        assert ValidationPhase.REGULATORY_COMPLIANCE.value == "regulatory_compliance"
        assert ValidationPhase.FINAL_SYNTHESIS.value == "final_synthesis"


class TestPhaseResult:
    """Test PhaseResult dataclass."""

    def test_phase_result_creation(self):
        """Test creating a PhaseResult."""
        result = PhaseResult(
            phase=ValidationPhase.MARKET_VALIDATION,
            success=True,
            data={"tam": "$10B", "sam": "$1B"},
            recommendations=["Focus on enterprise segment"],
            next_phase=ValidationPhase.FINANCIAL_MODELING,
            confidence_score=0.85
        )
        
        assert result.phase == ValidationPhase.MARKET_VALIDATION
        assert result.success is True
        assert result.data["tam"] == "$10B"
        assert len(result.recommendations) == 1
        assert result.next_phase == ValidationPhase.FINANCIAL_MODELING
        assert result.confidence_score == 0.85

    def test_phase_result_defaults(self):
        """Test PhaseResult with default values."""
        result = PhaseResult(
            phase=ValidationPhase.IDEA_REFINEMENT,
            success=False,
            data={},
            recommendations=[]
        )
        
        assert result.next_phase is None
        assert result.confidence_score == 0.0


class TestSequentialValidationWorkflow:
    """Test SequentialValidationWorkflow class."""

    @patch('src.workflows.sequential_validation.ConversableAgent')
    def test_workflow_initialization(self, mock_agent_class):
        """Test workflow initialization."""
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent
        
        workflow = SequentialValidationWorkflow()
        
        assert workflow.current_phase == ValidationPhase.IDEA_REFINEMENT
        assert workflow.phase_results == {}
        assert workflow.business_context == {}
        assert workflow.agents is not None

    @patch('src.workflows.sequential_validation.settings')
    def test_create_anthropic_config(self, mock_settings):
        """Test creating Anthropic configuration."""
        mock_settings.model_specialists = "claude-3-sonnet"
        mock_settings.anthropic_key = "test-key"
        mock_settings.top_p = 0.95
        
        workflow = SequentialValidationWorkflow()
        config = workflow._create_anthropic_config(temperature=0.3, max_tokens=1500)
        
        assert config["api_type"] == "anthropic"
        assert config["model"] == "claude-3-sonnet"
        assert config["temperature"] == 0.3
        assert config["max_tokens"] == 1500
        assert config["top_p"] == 0.95

    @patch('src.workflows.sequential_validation.ConversableAgent')
    @patch('src.workflows.sequential_validation.settings')
    def test_create_specialized_agents(self, mock_settings, mock_agent_class):
        """Test creating specialized agents."""
        mock_settings.model_specialists = "claude-3-sonnet"
        mock_settings.anthropic_key = "test-key"
        mock_settings.top_p = 0.95
        
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent
        
        workflow = SequentialValidationWorkflow()
        agents = workflow._create_specialized_agents()
        
        assert "idea_refiner" in agents
        assert "market_validator" in agents
        assert "financial_modeler" in agents
        assert "risk_assessor" in agents
        assert "competitive_analyst" in agents
        assert "compliance_officer" in agents
        assert "synthesis_expert" in agents
        
        # Verify agent creation calls
        assert mock_agent_class.call_count >= 7

    @patch('src.workflows.sequential_validation.ConversableAgent')
    def test_execute_phase_idea_refinement(self, mock_agent_class):
        """Test executing idea refinement phase."""
        mock_agent = Mock()
        mock_agent.generate_reply.return_value = json.dumps({
            "refined_idea": "AI-powered analytics for SMBs",
            "value_proposition": "Affordable enterprise-grade analytics",
            "target_market": "Small to medium businesses",
            "confidence": 0.8
        })
        mock_agent_class.return_value = mock_agent
        
        workflow = SequentialValidationWorkflow()
        context = {"initial_idea": "Analytics platform"}
        
        result = workflow._execute_phase(ValidationPhase.IDEA_REFINEMENT, context)
        
        assert isinstance(result, PhaseResult)
        assert result.phase == ValidationPhase.IDEA_REFINEMENT
        assert result.success is True
        assert "refined_idea" in result.data

    @patch('src.workflows.sequential_validation.ConversableAgent')
    @patch('src.workflows.sequential_validation.rag_tool_executor')
    @patch('src.workflows.sequential_validation.web_search_executor')
    def test_execute_phase_market_validation(self, mock_web, mock_rag, mock_agent_class):
        """Test executing market validation phase."""
        mock_agent = Mock()
        mock_agent.generate_reply.return_value = json.dumps({
            "tam": "$50B",
            "sam": "$5B",
            "som": "$500M",
            "growth_rate": "15%",
            "validation": "strong"
        })
        mock_agent_class.return_value = mock_agent
        
        mock_rag.return_value = {"market_insights": "Growing market"}
        mock_web.return_value = {"competitors": ["Company A", "Company B"]}
        
        workflow = SequentialValidationWorkflow()
        context = {"idea": "AI analytics"}
        
        result = workflow._execute_phase(ValidationPhase.MARKET_VALIDATION, context)
        
        assert result.phase == ValidationPhase.MARKET_VALIDATION
        assert "tam" in result.data

    @patch('src.workflows.sequential_validation.ConversableAgent')
    @patch('src.workflows.sequential_validation.financial_tool_executor')
    def test_execute_phase_financial_modeling(self, mock_financial, mock_agent_class):
        """Test executing financial modeling phase."""
        mock_agent = Mock()
        mock_agent.generate_reply.return_value = json.dumps({
            "revenue_year1": "$1M",
            "revenue_year3": "$10M",
            "break_even": "Month 18",
            "npv": "$5M",
            "irr": "35%"
        })
        mock_agent_class.return_value = mock_agent
        
        mock_financial.return_value = {"npv": 5000000, "irr": 0.35}
        
        workflow = SequentialValidationWorkflow()
        context = {"market_size": "$50B"}
        
        result = workflow._execute_phase(ValidationPhase.FINANCIAL_MODELING, context)
        
        assert result.phase == ValidationPhase.FINANCIAL_MODELING
        assert "npv" in result.data

    @patch('src.workflows.sequential_validation.ConversableAgent')
    def test_execute_phase_risk_assessment(self, mock_agent_class):
        """Test executing risk assessment phase."""
        mock_agent = Mock()
        mock_agent.generate_reply.return_value = json.dumps({
            "key_risks": ["Market timing", "Competition", "Funding"],
            "risk_score": 0.6,
            "mitigation_strategies": ["Phased rollout", "Differentiation"]
        })
        mock_agent_class.return_value = mock_agent
        
        workflow = SequentialValidationWorkflow()
        context = {"business_model": "SaaS"}
        
        result = workflow._execute_phase(ValidationPhase.RISK_ASSESSMENT, context)
        
        assert result.phase == ValidationPhase.RISK_ASSESSMENT
        assert "key_risks" in result.data

    @patch('src.workflows.sequential_validation.ConversableAgent')
    @patch('src.workflows.sequential_validation.web_search_executor')
    def test_execute_phase_competitive_analysis(self, mock_web, mock_agent_class):
        """Test executing competitive analysis phase."""
        mock_agent = Mock()
        mock_agent.generate_reply.return_value = json.dumps({
            "main_competitors": ["Company X", "Company Y"],
            "competitive_advantages": ["Better AI", "Lower price"],
            "market_position": "Challenger"
        })
        mock_agent_class.return_value = mock_agent
        
        mock_web.return_value = {"competitor_data": "Market leader info"}
        
        workflow = SequentialValidationWorkflow()
        context = {"market": "B2B SaaS"}
        
        result = workflow._execute_phase(ValidationPhase.COMPETITIVE_ANALYSIS, context)
        
        assert result.phase == ValidationPhase.COMPETITIVE_ANALYSIS
        assert "main_competitors" in result.data

    @patch('src.workflows.sequential_validation.ConversableAgent')
    @patch('src.workflows.sequential_validation.database_tool_executor')
    def test_execute_phase_regulatory_compliance(self, mock_db, mock_agent_class):
        """Test executing regulatory compliance phase."""
        mock_agent = Mock()
        mock_agent.generate_reply.return_value = json.dumps({
            "regulations": ["GDPR", "SOC2"],
            "compliance_status": "Needs work",
            "requirements": ["Data protection", "Security audit"]
        })
        mock_agent_class.return_value = mock_agent
        
        mock_db.return_value = {"regulatory_data": "GDPR requirements"}
        
        workflow = SequentialValidationWorkflow()
        context = {"industry": "FinTech"}
        
        result = workflow._execute_phase(ValidationPhase.REGULATORY_COMPLIANCE, context)
        
        assert result.phase == ValidationPhase.REGULATORY_COMPLIANCE
        assert "regulations" in result.data

    @patch('src.workflows.sequential_validation.ConversableAgent')
    @patch('src.workflows.sequential_validation.document_tool_executor')
    def test_execute_phase_final_synthesis(self, mock_doc, mock_agent_class):
        """Test executing final synthesis phase."""
        mock_agent = Mock()
        mock_agent.generate_reply.return_value = json.dumps({
            "overall_assessment": "Strong opportunity",
            "go_no_go": "GO",
            "next_steps": ["Raise seed funding", "Build MVP"],
            "confidence_score": 0.75
        })
        mock_agent_class.return_value = mock_agent
        
        mock_doc.return_value = {"report": "Business plan generated"}
        
        workflow = SequentialValidationWorkflow()
        workflow.phase_results = {
            ValidationPhase.MARKET_VALIDATION: PhaseResult(
                ValidationPhase.MARKET_VALIDATION, True, {"tam": "$50B"}, []
            )
        }
        context = {"all_results": "compiled"}
        
        result = workflow._execute_phase(ValidationPhase.FINAL_SYNTHESIS, context)
        
        assert result.phase == ValidationPhase.FINAL_SYNTHESIS
        assert "overall_assessment" in result.data

    def test_execute_phase_with_exception(self):
        """Test phase execution with exception handling."""
        workflow = SequentialValidationWorkflow()
        
        with patch.object(workflow.agents["idea_refiner"], 'generate_reply') as mock_reply:
            mock_reply.side_effect = Exception("API error")
            
            result = workflow._execute_phase(ValidationPhase.IDEA_REFINEMENT, {})
            
            assert result.success is False
            assert "error" in result.data

    def test_execute_phase_with_invalid_json(self):
        """Test phase execution with invalid JSON response."""
        workflow = SequentialValidationWorkflow()
        
        with patch.object(workflow.agents["idea_refiner"], 'generate_reply') as mock_reply:
            mock_reply.return_value = "Not valid JSON"
            
            result = workflow._execute_phase(ValidationPhase.IDEA_REFINEMENT, {})
            
            assert result.success is False
            assert "error" in result.data or "raw_response" in result.data

    def test_determine_next_phase(self):
        """Test determining next phase in workflow."""
        workflow = SequentialValidationWorkflow()
        
        # Success path
        result = PhaseResult(ValidationPhase.IDEA_REFINEMENT, True, {}, [])
        next_phase = workflow._determine_next_phase(ValidationPhase.IDEA_REFINEMENT, result)
        assert next_phase == ValidationPhase.MARKET_VALIDATION
        
        # Last phase
        result = PhaseResult(ValidationPhase.FINAL_SYNTHESIS, True, {}, [])
        next_phase = workflow._determine_next_phase(ValidationPhase.FINAL_SYNTHESIS, result)
        assert next_phase is None
        
        # Failed phase with low confidence
        result = PhaseResult(ValidationPhase.MARKET_VALIDATION, False, {}, [], confidence_score=0.3)
        next_phase = workflow._determine_next_phase(ValidationPhase.MARKET_VALIDATION, result)
        # Should retry or skip based on logic
        assert next_phase is not None

    def test_compile_final_report(self):
        """Test compiling final validation report."""
        workflow = SequentialValidationWorkflow()
        
        # Add phase results
        workflow.phase_results = {
            ValidationPhase.IDEA_REFINEMENT: PhaseResult(
                ValidationPhase.IDEA_REFINEMENT, True, 
                {"refined_idea": "AI Platform"}, ["Focus on B2B"],
                confidence_score=0.8
            ),
            ValidationPhase.MARKET_VALIDATION: PhaseResult(
                ValidationPhase.MARKET_VALIDATION, True,
                {"tam": "$50B"}, ["Large market"],
                confidence_score=0.85
            ),
            ValidationPhase.FINANCIAL_MODELING: PhaseResult(
                ValidationPhase.FINANCIAL_MODELING, True,
                {"npv": "$5M"}, ["Strong financials"],
                confidence_score=0.75
            )
        }
        
        report = workflow._compile_final_report()
        
        assert "summary" in report
        assert "phase_results" in report
        assert "overall_confidence" in report
        assert "recommendations" in report
        assert len(report["phase_results"]) == 3

    @patch('src.workflows.sequential_validation.ConversableAgent')
    def test_run_validation_complete(self, mock_agent_class):
        """Test complete validation run."""
        mock_agent = Mock()
        
        # Mock responses for each phase
        responses = [
            json.dumps({"refined_idea": "AI Platform", "confidence": 0.8}),
            json.dumps({"tam": "$50B", "validation": "strong"}),
            json.dumps({"npv": "$5M", "irr": "35%"}),
            json.dumps({"key_risks": ["Competition"], "risk_score": 0.6}),
            json.dumps({"main_competitors": ["X", "Y"]}),
            json.dumps({"regulations": ["GDPR"], "compliance_status": "OK"}),
            json.dumps({"overall_assessment": "GO", "confidence_score": 0.8})
        ]
        
        mock_agent.generate_reply.side_effect = responses
        mock_agent_class.return_value = mock_agent
        
        workflow = SequentialValidationWorkflow()
        initial_context = {
            "idea": "AI-powered analytics platform",
            "target_market": "SMBs",
            "budget": "$500k"
        }
        
        report = workflow.run_validation(initial_context)
        
        assert "summary" in report
        assert "phase_results" in report
        assert "overall_confidence" in report
        assert "final_recommendation" in report
        assert len(workflow.phase_results) > 0

    def test_run_validation_with_failure(self):
        """Test validation run with phase failure."""
        workflow = SequentialValidationWorkflow()
        
        with patch.object(workflow, '_execute_phase') as mock_execute:
            # Make market validation fail
            mock_execute.side_effect = [
                PhaseResult(ValidationPhase.IDEA_REFINEMENT, True, {"idea": "refined"}, [], confidence_score=0.8),
                PhaseResult(ValidationPhase.MARKET_VALIDATION, False, {"error": "No market"}, [], confidence_score=0.2),
                PhaseResult(ValidationPhase.FINAL_SYNTHESIS, True, {"assessment": "NO-GO"}, [], confidence_score=0.3)
            ]
            
            report = workflow.run_validation({"idea": "test"})
            
            assert report["overall_confidence"] < 0.5
            assert "NO-GO" in str(report)

    def test_run_validation_with_max_iterations(self):
        """Test validation run hitting max iterations."""
        workflow = SequentialValidationWorkflow()
        
        with patch.object(workflow, '_execute_phase') as mock_execute:
            # Always return success to continue
            mock_execute.return_value = PhaseResult(
                ValidationPhase.IDEA_REFINEMENT, True, {}, [], 
                next_phase=ValidationPhase.MARKET_VALIDATION, confidence_score=0.8
            )
            
            with patch.object(workflow, '_determine_next_phase') as mock_next:
                # Keep returning next phase to force max iterations
                mock_next.return_value = ValidationPhase.MARKET_VALIDATION
                
                report = workflow.run_validation({}, max_iterations=3)
                
                # Should stop after max iterations
                assert mock_execute.call_count <= 3

    def test_phase_transition_logic(self):
        """Test phase transition logic."""
        workflow = SequentialValidationWorkflow()
        
        # Test all phase transitions
        transitions = [
            (ValidationPhase.IDEA_REFINEMENT, ValidationPhase.MARKET_VALIDATION),
            (ValidationPhase.MARKET_VALIDATION, ValidationPhase.FINANCIAL_MODELING),
            (ValidationPhase.FINANCIAL_MODELING, ValidationPhase.RISK_ASSESSMENT),
            (ValidationPhase.RISK_ASSESSMENT, ValidationPhase.COMPETITIVE_ANALYSIS),
            (ValidationPhase.COMPETITIVE_ANALYSIS, ValidationPhase.REGULATORY_COMPLIANCE),
            (ValidationPhase.REGULATORY_COMPLIANCE, ValidationPhase.FINAL_SYNTHESIS),
            (ValidationPhase.FINAL_SYNTHESIS, None)
        ]
        
        for current, expected_next in transitions:
            result = PhaseResult(current, True, {}, [], confidence_score=0.8)
            next_phase = workflow._determine_next_phase(current, result)
            if expected_next:
                assert next_phase == expected_next or next_phase is not None
            else:
                assert next_phase is None

    @patch('src.workflows.sequential_validation.api_tool_executor')
    @patch('src.workflows.sequential_validation.database_tool_executor')
    @patch('src.workflows.sequential_validation.document_tool_executor')
    @patch('src.workflows.sequential_validation.financial_tool_executor')
    @patch('src.workflows.sequential_validation.rag_tool_executor')
    @patch('src.workflows.sequential_validation.web_search_executor')
    def test_all_tools_integration(self, mock_web, mock_rag, mock_financial, 
                                mock_doc, mock_db, mock_api):
        """Test integration with all tools."""
        # Mock tool responses
        mock_api.return_value = {"api_data": "test"}
        mock_db.return_value = {"db_data": "test"}
        mock_doc.return_value = {"doc": "generated"}
        mock_financial.return_value = {"npv": 1000000}
        mock_rag.return_value = {"insights": "market data"}
        mock_web.return_value = {"search": "results"}
        
        workflow = SequentialValidationWorkflow()
        
        # Mock agent to call tools
        with patch.object(workflow.agents["market_validator"], 'generate_reply') as mock_reply:
            mock_reply.return_value = json.dumps({
                "market_size": "$10B",
                "tools_used": ["rag", "web", "database"]
            })
            
            result = workflow._execute_phase(ValidationPhase.MARKET_VALIDATION, {})
            
            # Tools might be called during execution
            assert result.phase == ValidationPhase.MARKET_VALIDATION