"""
Comprehensive synthetic tests for sequential_validation.py to achieve 95%+ coverage.
"""

from unittest.mock import Mock, patch

from src.workflows.sequential_validation import (
    PhaseResult,
    SequentialValidationWorkflow,
    ValidationPhase,
)


class TestValidationPhase:
    """Test ValidationPhase enum."""

    def test_validation_phase_enum_values(self):
        """Test ValidationPhase enum values."""
        assert ValidationPhase.IDEA_REFINEMENT.value == "idea_refinement"
        assert ValidationPhase.MARKET_VALIDATION.value == "market_validation"
        assert ValidationPhase.FINANCIAL_MODELING.value == "financial_modeling"
        assert ValidationPhase.RISK_ASSESSMENT.value == "risk_assessment"
        assert ValidationPhase.COMPETITIVE_ANALYSIS.value == "competitive_analysis"
        assert ValidationPhase.REGULATORY_COMPLIANCE.value == "regulatory_compliance"
        assert ValidationPhase.FINAL_SYNTHESIS.value == "final_synthesis"

    def test_validation_phase_count(self):
        """Test that ValidationPhase has expected number of values."""
        phases = list(ValidationPhase)
        assert len(phases) == 7


class TestPhaseResult:
    """Test PhaseResult dataclass."""

    def test_phase_result_creation(self):
        """Test creating a PhaseResult."""
        result = PhaseResult(
            phase=ValidationPhase.MARKET_VALIDATION,
            success=True,
            data={"market_size": "$1B"},
            recommendations=["Conduct user interviews"],
            next_phase=ValidationPhase.FINANCIAL_MODELING,
            confidence_score=0.85,
        )

        assert result.phase == ValidationPhase.MARKET_VALIDATION
        assert result.success is True
        assert result.data == {"market_size": "$1B"}
        assert result.recommendations == ["Conduct user interviews"]
        assert result.next_phase == ValidationPhase.FINANCIAL_MODELING
        assert result.confidence_score == 0.85

    def test_phase_result_failed(self):
        """Test PhaseResult for failed validation."""
        result = PhaseResult(
            phase=ValidationPhase.RISK_ASSESSMENT,
            success=False,
            data={"error": "Insufficient data"},
            recommendations=["Gather more information"],
        )

        assert result.success is False
        assert result.data == {"error": "Insufficient data"}
        assert result.next_phase is None
        assert result.confidence_score == 0.0


class TestSequentialValidationWorkflow:
    """Test SequentialValidationWorkflow class."""

    def test_workflow_initialization(self):
        """Test workflow initialization."""
        workflow = SequentialValidationWorkflow()

        assert workflow.current_phase == ValidationPhase.IDEA_REFINEMENT
        assert isinstance(workflow.phase_results, dict)
        assert isinstance(workflow.business_context, dict)
        assert isinstance(workflow.agents, dict)

    def test_agents_creation(self):
        """Test that all required agents are created."""
        workflow = SequentialValidationWorkflow()

        expected_agents = [
            "idea_refiner",
            "market_validator",
            "financial_modeler",
            "risk_assessor",
            "competitive_analyst",
            "compliance_expert",
            "synthesizer",
        ]

        for agent_name in expected_agents:
            assert agent_name in workflow.agents
            assert workflow.agents[agent_name] is not None

    @patch("src.workflows.sequential_validation.rag_tool_executor")
    @patch("src.workflows.sequential_validation.web_search_executor")
    def test_execute_idea_refinement(self, mock_web, mock_rag):
        """Test idea refinement phase execution."""
        workflow = SequentialValidationWorkflow()

        # Mock agent response
        with patch.object(workflow.agents["idea_refiner"], "generate_reply") as mock_reply:
            mock_reply.return_value = "Refined business concept analysis"

            input_data = {
                "business_idea": "AI-powered analytics platform",
                "target_market": "Enterprise customers",
            }

            result = workflow.execute_phase(ValidationPhase.IDEA_REFINEMENT, input_data)

            assert result.phase == ValidationPhase.IDEA_REFINEMENT
            assert result.success is True
            assert "original_idea" in result.data
            assert result.next_phase == ValidationPhase.MARKET_VALIDATION
            assert result.confidence_score == 0.8

    @patch("src.workflows.sequential_validation.rag_tool_executor")
    @patch("src.workflows.sequential_validation.web_search_executor")
    def test_execute_market_validation(self, mock_web, mock_rag):
        """Test market validation phase execution."""
        workflow = SequentialValidationWorkflow()

        # Mock tool responses
        mock_rag.return_value = {"market_insights": "Strong growth"}
        mock_web.return_value = {"trends": "Positive outlook"}

        # Mock agent response
        with patch.object(workflow.agents["market_validator"], "generate_reply") as mock_reply:
            mock_reply.return_value = "Market analysis complete"

            input_data = {"industry": "Technology", "target_market": "B2B"}

            result = workflow.execute_phase(ValidationPhase.MARKET_VALIDATION, input_data)

            assert result.phase == ValidationPhase.MARKET_VALIDATION
            assert result.success is True
            assert "market_size_analysis" in result.data
            assert result.next_phase == ValidationPhase.FINANCIAL_MODELING

            # Verify tools were called
            mock_rag.assert_called_once()
            mock_web.assert_called_once()

    @patch("src.workflows.sequential_validation.financial_tool_executor")
    def test_execute_financial_modeling(self, mock_financial):
        """Test financial modeling phase execution."""
        workflow = SequentialValidationWorkflow()

        # Mock financial tool response
        mock_financial.return_value = {"projections": "5-year forecast"}

        # Mock agent response
        with patch.object(workflow.agents["financial_modeler"], "generate_reply") as mock_reply:
            mock_reply.return_value = "Financial model analysis"

            input_data = {
                "projected_revenue": 1000000,
                "growth_rate": 0.25,
                "cac": 100,
                "ltv": 1000,
            }

            result = workflow.execute_phase(ValidationPhase.FINANCIAL_MODELING, input_data)

            assert result.phase == ValidationPhase.FINANCIAL_MODELING
            assert result.success is True
            assert "financial_model" in result.data
            assert result.next_phase == ValidationPhase.RISK_ASSESSMENT

            # Verify financial tools were called
            assert mock_financial.call_count >= 1

    @patch("src.workflows.sequential_validation.database_tool_executor")
    def test_execute_risk_assessment(self, mock_database):
        """Test risk assessment phase execution."""
        workflow = SequentialValidationWorkflow()

        # Mock database response
        mock_database.return_value = {"historical_data": "Industry benchmarks"}

        # Mock agent response
        with patch.object(workflow.agents["risk_assessor"], "generate_reply") as mock_reply:
            mock_reply.return_value = "Risk assessment complete"

            input_data = {"industry": "SaaS", "business_model": "Subscription"}

            result = workflow.execute_phase(ValidationPhase.RISK_ASSESSMENT, input_data)

            assert result.phase == ValidationPhase.RISK_ASSESSMENT
            assert result.success is True
            assert "risk_assessment" in result.data
            assert result.next_phase == ValidationPhase.COMPETITIVE_ANALYSIS

            # Verify database tool was called
            mock_database.assert_called_once()

    @patch("src.workflows.sequential_validation.web_search_executor")
    def test_execute_competitive_analysis(self, mock_web):
        """Test competitive analysis phase execution."""
        workflow = SequentialValidationWorkflow()

        # Mock web search response
        mock_web.return_value = {"competitors": ["CompetitorA", "CompetitorB"]}

        # Mock agent response
        with patch.object(workflow.agents["competitive_analyst"], "generate_reply") as mock_reply:
            mock_reply.return_value = "Competitive analysis complete"

            input_data = {"business_idea": "AI analytics", "target_market": "Enterprise"}

            result = workflow.execute_phase(ValidationPhase.COMPETITIVE_ANALYSIS, input_data)

            assert result.phase == ValidationPhase.COMPETITIVE_ANALYSIS
            assert result.success is True
            assert "competitive_analysis" in result.data
            assert result.next_phase == ValidationPhase.REGULATORY_COMPLIANCE

            # Verify web search was called
            mock_web.assert_called_once()

    @patch("src.workflows.sequential_validation.api_tool_executor")
    def test_execute_regulatory_compliance(self, mock_api):
        """Test regulatory compliance phase execution."""
        workflow = SequentialValidationWorkflow()

        # Mock API response
        mock_api.return_value = {"regulations": "GDPR, SOX compliance required"}

        # Mock agent response
        with patch.object(workflow.agents["compliance_expert"], "generate_reply") as mock_reply:
            mock_reply.return_value = "Compliance analysis complete"

            input_data = {"industry": "FinTech", "region": "US"}

            result = workflow.execute_phase(ValidationPhase.REGULATORY_COMPLIANCE, input_data)

            assert result.phase == ValidationPhase.REGULATORY_COMPLIANCE
            assert result.success is True
            assert "compliance_analysis" in result.data
            assert result.next_phase == ValidationPhase.FINAL_SYNTHESIS

            # Verify API tool was called
            mock_api.assert_called_once()

    @patch("src.workflows.sequential_validation.document_tool_executor")
    def test_execute_final_synthesis(self, mock_document):
        """Test final synthesis phase execution."""
        workflow = SequentialValidationWorkflow()

        # Add some phase results to synthesize
        workflow.phase_results[ValidationPhase.MARKET_VALIDATION] = PhaseResult(
            phase=ValidationPhase.MARKET_VALIDATION,
            success=True,
            data={"market_data": "validated"},
            recommendations=[],
        )

        # Mock document generation response
        mock_document.return_value = {"document": "business_plan.pdf"}

        # Mock agent response
        with patch.object(workflow.agents["synthesizer"], "generate_reply") as mock_reply:
            mock_reply.return_value = "Final synthesis complete"

            input_data = {"business_name": "Test Venture"}

            result = workflow.execute_phase(ValidationPhase.FINAL_SYNTHESIS, input_data)

            assert result.phase == ValidationPhase.FINAL_SYNTHESIS
            assert result.success is True
            assert "final_assessment" in result.data
            assert result.next_phase is None  # Final phase

            # Verify document generation was called
            mock_document.assert_called_once()

    def test_execute_unknown_phase(self):
        """Test execution with unknown phase."""
        workflow = SequentialValidationWorkflow()

        # Create a mock phase that doesn't exist
        class UnknownPhase:
            pass

        unknown_phase = UnknownPhase()
        result = workflow.execute_phase(unknown_phase, {})

        assert result.success is False
        assert "error" in result.data
        assert "Unknown phase" in result.data["error"]

    def test_execute_phase_with_exception(self):
        """Test phase execution with agent exception."""
        workflow = SequentialValidationWorkflow()

        # Mock agent to raise exception
        with patch.object(workflow.agents["idea_refiner"], "generate_reply") as mock_reply:
            mock_reply.side_effect = Exception("Agent failed")

            result = workflow.execute_phase(ValidationPhase.IDEA_REFINEMENT, {})

            assert result.phase == ValidationPhase.IDEA_REFINEMENT
            assert result.success is False
            assert "error" in result.data

    def test_run_full_validation_success(self):
        """Test running complete validation workflow successfully."""
        workflow = SequentialValidationWorkflow()

        # Mock all tool executors
        with (
            patch("src.workflows.sequential_validation.rag_tool_executor", return_value={}),
            patch("src.workflows.sequential_validation.web_search_executor", return_value={}),
            patch("src.workflows.sequential_validation.financial_tool_executor", return_value={}),
            patch("src.workflows.sequential_validation.database_tool_executor", return_value={}),
            patch("src.workflows.sequential_validation.api_tool_executor", return_value={}),
            patch("src.workflows.sequential_validation.document_tool_executor", return_value={}),
        ):
            # Mock all agents to return success responses
            for agent_name, agent in workflow.agents.items():
                agent.generate_reply = Mock(return_value=f"Success from {agent_name}")

            initial_data = {
                "business_idea": "AI Platform",
                "industry": "Technology",
                "target_market": "B2B",
            }

            results = workflow.run_full_validation(initial_data)

            assert len(results) == 7  # All phases executed
            assert all(phase in results for phase in ValidationPhase)

            # Check business context was updated
            assert workflow.business_context == initial_data

    def test_run_full_validation_with_failure(self):
        """Test validation workflow stopping on failure."""
        workflow = SequentialValidationWorkflow()

        # Mock first agent to fail, others shouldn't be called
        call_count = 0

        def mock_generate_reply(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("First phase failed")
            return "Success"

        for agent in workflow.agents.values():
            agent.generate_reply = mock_generate_reply

        with (
            patch("src.workflows.sequential_validation.rag_tool_executor", return_value={}),
            patch("src.workflows.sequential_validation.web_search_executor", return_value={}),
        ):
            results = workflow.run_full_validation({"business_idea": "Test"})

            # Should stop after first failure
            assert len(results) == 1
            assert ValidationPhase.IDEA_REFINEMENT in results
            assert results[ValidationPhase.IDEA_REFINEMENT].success is False

    def test_get_phase_summary_empty(self):
        """Test phase summary with no completed phases."""
        workflow = SequentialValidationWorkflow()

        summary = workflow.get_phase_summary()

        assert summary["total_phases"] == 7
        assert summary["completed_phases"] == 0
        assert summary["success_rate"] == 0
        assert summary["average_confidence"] == 0
        assert summary["phase_details"] == {}

    def test_get_phase_summary_with_results(self):
        """Test phase summary with completed phases."""
        workflow = SequentialValidationWorkflow()

        # Add some phase results
        workflow.phase_results[ValidationPhase.IDEA_REFINEMENT] = PhaseResult(
            phase=ValidationPhase.IDEA_REFINEMENT,
            success=True,
            data={},
            recommendations=["rec1", "rec2"],
            confidence_score=0.8,
        )

        workflow.phase_results[ValidationPhase.MARKET_VALIDATION] = PhaseResult(
            phase=ValidationPhase.MARKET_VALIDATION,
            success=False,
            data={},
            recommendations=["rec3"],
            confidence_score=0.4,
        )

        summary = workflow.get_phase_summary()

        assert summary["total_phases"] == 7
        assert summary["completed_phases"] == 2
        assert summary["success_rate"] == 0.5  # 1 out of 2 successful
        assert abs(summary["average_confidence"] - 0.6) < 0.01  # (0.8 + 0.4) / 2
        assert len(summary["phase_details"]) == 2

        # Check phase details
        phase_details = summary["phase_details"]
        assert "idea_refinement" in phase_details
        assert "market_validation" in phase_details

        idea_details = phase_details["idea_refinement"]
        assert idea_details["success"] is True
        assert idea_details["confidence"] == 0.8
        assert idea_details["recommendations_count"] == 2

        market_details = phase_details["market_validation"]
        assert market_details["success"] is False
        assert market_details["confidence"] == 0.4
        assert market_details["recommendations_count"] == 1

    def test_create_anthropic_config(self):
        """Test anthropic config creation."""
        workflow = SequentialValidationWorkflow()

        config = workflow._create_anthropic_config(0.5, 1000)

        # Verify config has the expected properties and structure
        assert hasattr(config, "temperature")
        assert config.temperature == 0.5

        # LLMConfig stores max_tokens in config_list
        assert hasattr(config, "config_list")
        assert len(config.config_list) > 0
        assert config.config_list[0]["max_tokens"] == 1000

    def test_phase_execution_order(self):
        """Test that phases execute in correct order."""
        workflow = SequentialValidationWorkflow()

        # Test the phase ordering
        expected_order = [
            ValidationPhase.IDEA_REFINEMENT,
            ValidationPhase.MARKET_VALIDATION,
            ValidationPhase.FINANCIAL_MODELING,
            ValidationPhase.RISK_ASSESSMENT,
            ValidationPhase.COMPETITIVE_ANALYSIS,
            ValidationPhase.REGULATORY_COMPLIANCE,
            ValidationPhase.FINAL_SYNTHESIS,
        ]

        # This test verifies the order is defined correctly
        # by checking the next_phase assignments in each phase execution
        input_data = {"test": "data"}

        # Check idea refinement -> market validation
        with patch.object(workflow.agents["idea_refiner"], "generate_reply", return_value="test"):
            result = workflow.execute_phase(ValidationPhase.IDEA_REFINEMENT, input_data)
            assert result.next_phase == ValidationPhase.MARKET_VALIDATION

        # Check market validation -> financial modeling
        with (
            patch("src.workflows.sequential_validation.rag_tool_executor", return_value={}),
            patch("src.workflows.sequential_validation.web_search_executor", return_value={}),
            patch.object(
                workflow.agents["market_validator"], "generate_reply", return_value="test"
            ),
        ):
            result = workflow.execute_phase(ValidationPhase.MARKET_VALIDATION, input_data)
            assert result.next_phase == ValidationPhase.FINANCIAL_MODELING


class TestValidationIntegration:
    """Test integration scenarios."""

    def test_full_validation_workflow_integration(self):
        """Test complete workflow integration."""
        workflow = SequentialValidationWorkflow()

        # Mock all external dependencies
        with (
            patch("src.workflows.sequential_validation.rag_tool_executor") as mock_rag,
            patch("src.workflows.sequential_validation.web_search_executor") as mock_web,
            patch("src.workflows.sequential_validation.financial_tool_executor") as mock_fin,
            patch("src.workflows.sequential_validation.database_tool_executor") as mock_db,
            patch("src.workflows.sequential_validation.api_tool_executor") as mock_api,
            patch("src.workflows.sequential_validation.document_tool_executor") as mock_doc,
        ):
            # Configure mock responses
            mock_rag.return_value = {"insights": "market data"}
            mock_web.return_value = {"trends": "positive"}
            mock_fin.return_value = {"projections": "profitable"}
            mock_db.return_value = {"benchmarks": "industry data"}
            mock_api.return_value = {"regulations": "compliant"}
            mock_doc.return_value = {"document": "business_plan"}

            # Mock all agent responses
            for agent in workflow.agents.values():
                agent.generate_reply = Mock(return_value="Phase completed successfully")

            business_data = {
                "business_idea": "AI-powered analytics platform",
                "industry": "Technology",
                "target_market": "Enterprise",
                "business_name": "Analytics Inc",
            }

            results = workflow.run_full_validation(business_data)

            # Verify all phases completed
            assert len(results) == 7
            assert all(results[phase].success for phase in ValidationPhase)

            # Verify tools were called appropriately
            mock_rag.assert_called()
            mock_web.assert_called()
            mock_fin.assert_called()
            mock_db.assert_called()
            mock_api.assert_called()
            mock_doc.assert_called()

    def test_validation_with_partial_failure_recovery(self):
        """Test workflow handles partial failures gracefully."""
        workflow = SequentialValidationWorkflow()

        # Mock some phases to fail, others to succeed
        phase_results = {}

        def mock_execute_phase(phase, data):
            if phase == ValidationPhase.FINANCIAL_MODELING:
                return PhaseResult(
                    phase=phase,
                    success=False,
                    data={"error": "Insufficient financial data"},
                    recommendations=["Gather more financial assumptions"],
                )
            else:
                return PhaseResult(
                    phase=phase,
                    success=True,
                    data={"status": "completed"},
                    recommendations=[],
                    confidence_score=0.8,
                )

        workflow.execute_phase = mock_execute_phase

        results = workflow.run_full_validation({"business_idea": "Test"})

        # Should stop at financial modeling failure
        assert len(results) == 3  # idea_refinement, market_validation, financial_modeling
        assert results[ValidationPhase.FINANCIAL_MODELING].success is False
