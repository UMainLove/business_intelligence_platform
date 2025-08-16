"""
Focused tests for financial_tools.py to achieve 95%+ coverage.
"""

from unittest.mock import patch

import pytest

from src.error_handling import ValidationError
from src.tools.financial_tools import (
    FinancialCalculator,
    FinancialMetrics,
    create_financial_tool_spec,
    financial_tool_executor,
)


class TestFinancialMetrics:
    """Test FinancialMetrics dataclass."""

    def test_financial_metrics_creation(self):
        """Test creating FinancialMetrics instance."""
        metrics = FinancialMetrics(
            npv=10000.0, irr=0.15, payback_period=3.5, break_even_point=1000, roi=25.0
        )

        assert metrics.npv == 10000.0
        assert metrics.irr == 0.15
        assert metrics.payback_period == 3.5
        assert metrics.break_even_point == 1000
        assert metrics.roi == 25.0

    def test_financial_metrics_types(self):
        """Test FinancialMetrics type annotations."""
        metrics = FinancialMetrics(1.0, 0.1, 2.0, 100, 5.0)

        assert isinstance(metrics.npv, float)
        assert isinstance(metrics.irr, float)
        assert isinstance(metrics.payback_period, float)
        assert isinstance(metrics.break_even_point, int)
        assert isinstance(metrics.roi, float)


class TestFinancialCalculatorNPV:
    """Test NPV calculations."""

    def test_calculate_npv_positive_flows(self):
        """Test NPV calculation with positive cash flows."""
        cash_flows = [-1000, 300, 400, 500, 600]  # Initial investment followed by returns
        discount_rate = 0.10

        result = FinancialCalculator.calculate_npv(cash_flows, discount_rate)

        # Manual calculation: -1000 + 300/1.1 + 400/1.21 + 500/1.331 + 600/1.4641
        expected = -1000 + 272.73 + 330.58 + 375.66 + 409.81
        assert abs(result - expected) < 1.0  # Allow small floating point differences

    def test_calculate_npv_negative_flows(self):
        """Test NPV calculation with negative cash flows."""
        cash_flows = [-1000, -200, -300]  # All negative flows
        discount_rate = 0.05

        result = FinancialCalculator.calculate_npv(cash_flows, discount_rate)

        assert result < 0  # Should be negative

    def test_calculate_npv_zero_discount_rate(self):
        """Test NPV calculation with zero discount rate."""
        cash_flows = [-1000, 300, 400, 500]
        discount_rate = 0.0

        result = FinancialCalculator.calculate_npv(cash_flows, discount_rate)

        # With 0% discount rate, NPV is just the sum
        expected = sum(cash_flows)
        assert result == expected

    def test_calculate_npv_single_cash_flow(self):
        """Test NPV calculation with single cash flow."""
        cash_flows = [1000]
        discount_rate = 0.10

        result = FinancialCalculator.calculate_npv(cash_flows, discount_rate)

        assert result == 1000  # t=0, so no discounting

    def test_calculate_npv_empty_flows(self):
        """Test NPV calculation with empty cash flows."""
        cash_flows = []
        discount_rate = 0.10

        result = FinancialCalculator.calculate_npv(cash_flows, discount_rate)

        assert result == 0


class TestFinancialCalculatorIRR:
    """Test IRR calculations."""

    def test_calculate_irr_positive_project(self):
        """Test IRR calculation for profitable project."""
        cash_flows = [-1000, 300, 400, 500, 600]

        result = FinancialCalculator.calculate_irr(cash_flows)

        # Should be positive for profitable project
        assert result > 0
        assert result < 1  # Should be reasonable percentage

    def test_calculate_irr_negative_project(self):
        """Test IRR calculation for unprofitable project."""
        cash_flows = [-1000, 100, 100, 100]  # Low returns

        result = FinancialCalculator.calculate_irr(cash_flows)

        # Should be low or negative for unprofitable project
        assert result < 0.2  # Less than 20%

    def test_calculate_irr_single_cash_flow(self):
        """Test IRR calculation with single cash flow."""
        cash_flows = [1000]

        result = FinancialCalculator.calculate_irr(cash_flows)

        assert result == 0.0

    def test_calculate_irr_empty_flows(self):
        """Test IRR calculation with empty cash flows."""
        cash_flows = []

        result = FinancialCalculator.calculate_irr(cash_flows)

        assert result == 0.0

    def test_calculate_irr_two_flows(self):
        """Test IRR calculation with two cash flows."""
        cash_flows = [-100, 110]  # 10% return

        result = FinancialCalculator.calculate_irr(cash_flows)

        assert abs(result - 0.1) < 0.01  # Should be approximately 10%

    def test_calculate_irr_bounds_check(self):
        """Test IRR calculation handles bounds correctly."""
        # Extreme case that might cause bounds issues
        cash_flows = [-1, 0.001, 0.001, 0.001]  # Very small returns

        result = FinancialCalculator.calculate_irr(cash_flows)

        # Should not crash and should return reasonable value
        assert result >= -0.99
        assert result <= 10

    def test_calculate_irr_convergence_failure(self):
        """Test IRR calculation when convergence fails."""
        # Case that might not converge easily
        cash_flows = [-1000, 1, 1, 1, 1, 1]  # Very low returns

        result = FinancialCalculator.calculate_irr(cash_flows)

        # Should handle non-convergence gracefully
        assert isinstance(result, float)


class TestFinancialCalculatorPayback:
    """Test payback period calculations."""

    def test_calculate_payback_normal_case(self):
        """Test payback calculation for normal case."""
        initial_investment = 10000
        annual_cash_flow = 2500

        result = FinancialCalculator.calculate_payback(initial_investment, annual_cash_flow)

        assert result == 4.0  # 10000 / 2500 = 4 years

    def test_calculate_payback_fractional(self):
        """Test payback calculation with fractional result."""
        initial_investment = 7500
        annual_cash_flow = 2000

        result = FinancialCalculator.calculate_payback(initial_investment, annual_cash_flow)

        assert result == 3.75  # 7500 / 2000 = 3.75 years

    def test_calculate_payback_zero_cash_flow(self):
        """Test payback calculation with zero cash flow."""
        initial_investment = 10000
        annual_cash_flow = 0

        result = FinancialCalculator.calculate_payback(initial_investment, annual_cash_flow)

        assert result == float("inf")

    def test_calculate_payback_negative_cash_flow(self):
        """Test payback calculation with negative cash flow."""
        initial_investment = 10000
        annual_cash_flow = -1000

        result = FinancialCalculator.calculate_payback(initial_investment, annual_cash_flow)

        assert result == float("inf")

    def test_calculate_payback_zero_investment(self):
        """Test payback calculation with zero investment."""
        initial_investment = 0
        annual_cash_flow = 1000

        result = FinancialCalculator.calculate_payback(initial_investment, annual_cash_flow)

        assert result == 0.0


class TestFinancialCalculatorBreakEven:
    """Test break-even calculations."""

    def test_calculate_break_even_normal_case(self):
        """Test break-even calculation for normal case."""
        fixed_costs = 10000
        price_per_unit = 50
        variable_cost_per_unit = 30

        result = FinancialCalculator.calculate_break_even(
            fixed_costs, price_per_unit, variable_cost_per_unit
        )

        # 10000 / (50 - 30) = 500 units
        assert result == 500

    def test_calculate_break_even_fractional_result(self):
        """Test break-even calculation with fractional result."""
        fixed_costs = 7500
        price_per_unit = 40
        variable_cost_per_unit = 25

        result = FinancialCalculator.calculate_break_even(
            fixed_costs, price_per_unit, variable_cost_per_unit
        )

        # 7500 / (40 - 25) = 500 exactly
        assert result == 500

    def test_calculate_break_even_ceiling(self):
        """Test break-even calculation uses ceiling for fractional units."""
        fixed_costs = 7501  # Slight increase to force ceiling
        price_per_unit = 40
        variable_cost_per_unit = 25

        result = FinancialCalculator.calculate_break_even(
            fixed_costs, price_per_unit, variable_cost_per_unit
        )

        # 7501 / 15 = 500.0667, ceiling = 501
        assert result == 501

    def test_calculate_break_even_no_margin(self):
        """Test break-even calculation when price equals variable cost."""
        fixed_costs = 10000
        price_per_unit = 30
        variable_cost_per_unit = 30

        result = FinancialCalculator.calculate_break_even(
            fixed_costs, price_per_unit, variable_cost_per_unit
        )

        assert result == float("inf")

    def test_calculate_break_even_negative_margin(self):
        """Test break-even calculation when price is less than variable cost."""
        fixed_costs = 10000
        price_per_unit = 25
        variable_cost_per_unit = 30

        result = FinancialCalculator.calculate_break_even(
            fixed_costs, price_per_unit, variable_cost_per_unit
        )

        assert result == float("inf")

    def test_calculate_break_even_zero_fixed_costs(self):
        """Test break-even calculation with zero fixed costs."""
        fixed_costs = 0
        price_per_unit = 50
        variable_cost_per_unit = 30

        result = FinancialCalculator.calculate_break_even(
            fixed_costs, price_per_unit, variable_cost_per_unit
        )

        assert result == 0


class TestFinancialCalculatorROI:
    """Test ROI calculations."""

    def test_calculate_roi_positive_return(self):
        """Test ROI calculation with positive return."""
        gain = 1500
        cost = 1000

        result = FinancialCalculator.calculate_roi(gain, cost)

        # ((1500 - 1000) / 1000) * 100 = 50%
        assert result == 50.0

    def test_calculate_roi_negative_return(self):
        """Test ROI calculation with negative return."""
        gain = 800
        cost = 1000

        result = FinancialCalculator.calculate_roi(gain, cost)

        # ((800 - 1000) / 1000) * 100 = -20%
        assert result == -20.0

    def test_calculate_roi_zero_gain(self):
        """Test ROI calculation with zero gain."""
        gain = 0
        cost = 1000

        result = FinancialCalculator.calculate_roi(gain, cost)

        # ((0 - 1000) / 1000) * 100 = -100%
        assert result == -100.0

    def test_calculate_roi_zero_cost(self):
        """Test ROI calculation with zero cost."""
        gain = 1500
        cost = 0

        result = FinancialCalculator.calculate_roi(gain, cost)

        assert result == 0

    def test_calculate_roi_equal_gain_cost(self):
        """Test ROI calculation when gain equals cost."""
        gain = 1000
        cost = 1000

        result = FinancialCalculator.calculate_roi(gain, cost)

        # ((1000 - 1000) / 1000) * 100 = 0%
        assert result == 0.0


class TestFinancialCalculatorCodeExecution:
    """Test code execution method."""

    def test_safe_exec_financial_code_disabled(self):
        """Test that code execution is disabled for security."""
        code = "result = 2 + 2"

        result = FinancialCalculator.safe_exec_financial_code(code)

        assert result["success"] is False
        assert "disabled for security" in result["error"]
        assert result["output"] == ""
        assert result["variables"] == {}

    def test_safe_exec_financial_code_malicious(self):
        """Test that malicious code is blocked."""
        code = "import os; os.system('rm -rf /')"

        result = FinancialCalculator.safe_exec_financial_code(code)

        assert result["success"] is False
        assert "disabled for security" in result["error"]

    def test_safe_exec_financial_code_empty(self):
        """Test code execution with empty code."""
        code = ""

        result = FinancialCalculator.safe_exec_financial_code(code)

        assert result["success"] is False
        assert "disabled for security" in result["error"]


class TestFinancialCalculatorProjections:
    """Test financial projection calculations."""

    def test_generate_financial_projection_default(self):
        """Test financial projection with default parameters."""
        initial_revenue = 100000
        growth_rate = 0.2

        result = FinancialCalculator.generate_financial_projection(initial_revenue, growth_rate)

        assert "revenues" in result
        assert "ebitda" in result
        assert "net_income" in result
        assert "years" in result

        # Check default 5 years
        assert len(result["revenues"]) == 5
        assert len(result["ebitda"]) == 5
        assert len(result["net_income"]) == 5
        assert result["years"] == [1, 2, 3, 4, 5]

    def test_generate_financial_projection_custom_years(self):
        """Test financial projection with custom years."""
        initial_revenue = 100000
        growth_rate = 0.15
        years = 3

        result = FinancialCalculator.generate_financial_projection(
            initial_revenue, growth_rate, years=years
        )

        assert len(result["revenues"]) == 3
        assert len(result["ebitda"]) == 3
        assert len(result["net_income"]) == 3
        assert result["years"] == [1, 2, 3]

    def test_generate_financial_projection_growth_calculation(self):
        """Test financial projection growth calculations."""
        initial_revenue = 100000
        growth_rate = 0.2
        years = 3

        result = FinancialCalculator.generate_financial_projection(
            initial_revenue, growth_rate, years=years
        )

        # Year 1: 100000 * (1.2)^0 = 100000
        # Year 2: 100000 * (1.2)^1 = 120000
        # Year 3: 100000 * (1.2)^2 = 144000
        assert abs(result["revenues"][0] - 100000) < 0.01
        assert abs(result["revenues"][1] - 120000) < 0.01
        assert abs(result["revenues"][2] - 144000) < 0.01

    def test_generate_financial_projection_margins(self):
        """Test financial projection with custom margins."""
        initial_revenue = 100000
        growth_rate = 0.2
        years = 2
        operating_margin = 0.3
        tax_rate = 0.2

        result = FinancialCalculator.generate_financial_projection(
            initial_revenue,
            growth_rate,
            years=years,
            operating_margin=operating_margin,
            tax_rate=tax_rate,
        )

        # Year 1: Revenue 100000, EBITDA 30000, Net Income 24000
        assert abs(result["ebitda"][0] - 30000) < 0.01
        assert abs(result["net_income"][0] - 24000) < 0.01

    def test_generate_financial_projection_zero_growth(self):
        """Test financial projection with zero growth."""
        initial_revenue = 100000
        growth_rate = 0.0
        years = 3

        result = FinancialCalculator.generate_financial_projection(
            initial_revenue, growth_rate, years=years
        )

        # All years should have same revenue
        for revenue in result["revenues"]:
            assert revenue == 100000

    def test_generate_financial_projection_negative_growth(self):
        """Test financial projection with negative growth."""
        initial_revenue = 100000
        growth_rate = -0.1
        years = 2

        result = FinancialCalculator.generate_financial_projection(
            initial_revenue, growth_rate, years=years
        )

        # Year 1: 100000, Year 2: 90000
        assert abs(result["revenues"][0] - 100000) < 0.01
        assert abs(result["revenues"][1] - 90000) < 0.01


class TestFinancialCalculatorUnitEconomics:
    """Test unit economics calculations."""

    def test_unit_economics_analysis_healthy_metrics(self):
        """Test unit economics analysis with healthy metrics."""
        cac = 100
        ltv = 400
        monthly_churn = 0.05
        arpu = 50

        result = FinancialCalculator.unit_economics_analysis(cac, ltv, monthly_churn, arpu)

        assert result["ltv_cac_ratio"] == 4.0  # 400 / 100
        assert result["months_to_recover_cac"] == 2.0  # 100 / 50
        assert result["is_sustainable"] is True  # Ratio > 3
        assert result["health_score"] == 100  # Will be capped at 100

    def test_unit_economics_analysis_unhealthy_metrics(self):
        """Test unit economics analysis with unhealthy metrics."""
        cac = 200
        ltv = 300
        monthly_churn = 0.1
        arpu = 20

        result = FinancialCalculator.unit_economics_analysis(cac, ltv, monthly_churn, arpu)

        assert result["ltv_cac_ratio"] == 1.5  # 300 / 200
        assert result["months_to_recover_cac"] == 10.0  # 200 / 20
        assert result["is_sustainable"] is False  # Ratio < 3
        assert result["health_score"] == 50.0  # (1.5 / 3) * 100

    def test_unit_economics_analysis_zero_cac(self):
        """Test unit economics analysis with zero CAC."""
        cac = 0
        ltv = 400
        monthly_churn = 0.05
        arpu = 50

        result = FinancialCalculator.unit_economics_analysis(cac, ltv, monthly_churn, arpu)

        assert result["ltv_cac_ratio"] == 0
        assert result["months_to_recover_cac"] == 0.0  # 0 / 50 = 0

    def test_unit_economics_analysis_zero_arpu(self):
        """Test unit economics analysis with zero ARPU."""
        cac = 100
        ltv = 400
        monthly_churn = 0.05
        arpu = 0

        result = FinancialCalculator.unit_economics_analysis(cac, ltv, monthly_churn, arpu)

        assert result["months_to_recover_cac"] == float("inf")

    def test_unit_economics_analysis_churn_calculation(self):
        """Test unit economics churn rate calculation."""
        cac = 100
        ltv = 400
        monthly_churn = 0.1
        arpu = 50

        result = FinancialCalculator.unit_economics_analysis(cac, ltv, monthly_churn, arpu)

        # Annual churn = 1 - (1 - 0.1)^12 = 1 - 0.9^12
        expected_annual_churn = (1 - (0.9**12)) * 100
        assert abs(result["annual_churn_rate"] - expected_annual_churn) < 0.01

    def test_unit_economics_analysis_health_score_capping(self):
        """Test unit economics health score is capped at 100."""
        cac = 50
        ltv = 500  # Very high LTV
        monthly_churn = 0.01
        arpu = 100

        result = FinancialCalculator.unit_economics_analysis(cac, ltv, monthly_churn, arpu)

        # LTV/CAC = 10, health score should be capped at 100
        assert result["health_score"] == 100


class TestCreateFinancialToolSpec:
    """Test tool specification creation."""

    def test_create_financial_tool_spec_structure(self):
        """Test financial tool specification structure."""
        spec = create_financial_tool_spec()

        assert spec["name"] == "financial_calculator"
        assert "description" in spec
        assert "parameters" in spec

    def test_create_financial_tool_spec_parameters(self):
        """Test financial tool specification parameters."""
        spec = create_financial_tool_spec()
        params = spec["parameters"]

        assert params["type"] == "object"
        assert "properties" in params
        assert "required" in params
        assert params["required"] == ["operation", "params"]

    def test_create_financial_tool_spec_operations(self):
        """Test financial tool specification operation enum."""
        spec = create_financial_tool_spec()
        operation_enum = spec["parameters"]["properties"]["operation"]["enum"]

        expected_operations = [
            "npv",
            "irr",
            "payback",
            "break_even",
            "roi",
            "projection",
            "unit_economics",
            "execute_code",
        ]

        for op in expected_operations:
            assert op in operation_enum


class TestFinancialToolExecutor:
    """Test financial tool executor."""

    def test_financial_tool_executor_npv(self):
        """Test financial tool executor NPV operation."""
        params = {"cash_flows": [-1000, 300, 400, 500], "discount_rate": 0.1}

        result = financial_tool_executor("npv", params)

        assert "npv" in result
        assert isinstance(result["npv"], float)

    def test_financial_tool_executor_irr(self):
        """Test financial tool executor IRR operation."""
        params = {"cash_flows": [-1000, 300, 400, 500]}

        result = financial_tool_executor("irr", params)

        assert "irr" in result
        assert isinstance(result["irr"], float)

    def test_financial_tool_executor_payback(self):
        """Test financial tool executor payback operation."""
        params = {"initial_investment": 10000, "annual_cash_flow": 2500}

        result = financial_tool_executor("payback", params)

        assert "payback_period_years" in result
        assert result["payback_period_years"] == 4.0

    def test_financial_tool_executor_break_even(self):
        """Test financial tool executor break-even operation."""
        params = {"fixed_costs": 10000, "price_per_unit": 50, "variable_cost_per_unit": 30}

        result = financial_tool_executor("break_even", params)

        assert "break_even_units" in result
        assert result["break_even_units"] == 500

    def test_financial_tool_executor_roi(self):
        """Test financial tool executor ROI operation."""
        params = {"gain": 1500, "cost": 1000}

        result = financial_tool_executor("roi", params)

        assert "roi_percentage" in result
        assert result["roi_percentage"] == 50.0

    def test_financial_tool_executor_projection(self):
        """Test financial tool executor projection operation."""
        params = {"initial_revenue": 100000, "growth_rate": 0.2, "years": 3}

        result = financial_tool_executor("projection", params)

        assert "revenues" in result
        assert "ebitda" in result
        assert "net_income" in result
        assert len(result["revenues"]) == 3

    def test_financial_tool_executor_unit_economics(self):
        """Test financial tool executor unit economics operation."""
        params = {
            "customer_acquisition_cost": 100,
            "customer_lifetime_value": 400,
            "monthly_churn_rate": 0.05,
            "average_revenue_per_user": 50,
        }

        result = financial_tool_executor("unit_economics", params)

        assert "ltv_cac_ratio" in result
        assert "months_to_recover_cac" in result
        assert "is_sustainable" in result

    def test_financial_tool_executor_execute_code(self):
        """Test financial tool executor code execution operation."""
        params = {"code": "result = 2 + 2"}

        result = financial_tool_executor("execute_code", params)

        assert "success" in result
        assert result["success"] is False
        assert "error" in result

    def test_financial_tool_executor_unknown_operation(self):
        """Test financial tool executor with unknown operation."""
        result = financial_tool_executor("unknown_op", {})

        assert "error" in result
        assert "Unknown operation" in result["error"]

    @patch("src.tools.financial_tools.validate_input")
    def test_financial_tool_executor_validation_error(self, mock_validate):
        """Test financial tool executor with validation error."""
        mock_validate.side_effect = ValidationError("Invalid input")

        result = financial_tool_executor("npv", {})

        assert "error" in result
        assert "Validation failed" in result["error"]

    def test_financial_tool_executor_missing_params(self):
        """Test financial tool executor with missing parameters."""
        # NPV requires cash_flows and discount_rate
        params = {"cash_flows": [-1000, 300, 400]}  # Missing discount_rate

        # This should raise a KeyError which gets handled by decorators
        with pytest.raises(ValidationError):
            financial_tool_executor("npv", params)


class TestIntegration:
    """Test integration scenarios."""

    def test_financial_calculator_comprehensive_analysis(self):
        """Test comprehensive financial analysis workflow."""
        calc = FinancialCalculator()

        # Project data
        cash_flows = [-50000, 15000, 20000, 25000, 30000]
        discount_rate = 0.12
        initial_investment = 50000
        annual_cash_flow = 22500  # Average

        # Calculate all metrics
        npv = calc.calculate_npv(cash_flows, discount_rate)
        irr = calc.calculate_irr(cash_flows)
        payback = calc.calculate_payback(initial_investment, annual_cash_flow)

        # All calculations should complete without error
        assert isinstance(npv, float)
        assert isinstance(irr, float)
        assert isinstance(payback, float)

        # Create metrics object
        metrics = FinancialMetrics(
            npv=npv, irr=irr, payback_period=payback, break_even_point=1000, roi=25.0
        )

        assert metrics.npv == npv
        assert metrics.irr == irr

    def test_tool_executor_all_operations(self):
        """Test tool executor with all operations."""
        operations = [
            ("npv", {"cash_flows": [-1000, 300, 400], "discount_rate": 0.1}),
            ("irr", {"cash_flows": [-1000, 300, 400]}),
            ("payback", {"initial_investment": 1000, "annual_cash_flow": 250}),
            (
                "break_even",
                {"fixed_costs": 5000, "price_per_unit": 25, "variable_cost_per_unit": 15},
            ),
            ("roi", {"gain": 1250, "cost": 1000}),
            ("projection", {"initial_revenue": 50000, "growth_rate": 0.15, "years": 2}),
            (
                "unit_economics",
                {
                    "customer_acquisition_cost": 50,
                    "customer_lifetime_value": 200,
                    "monthly_churn_rate": 0.05,
                    "average_revenue_per_user": 25,
                },
            ),
            ("execute_code", {"code": "x = 1 + 1"}),
        ]

        for operation, params in operations:
            result = financial_tool_executor(operation, params)

            # All operations should return a result (either success or error)
            assert isinstance(result, dict)
            assert len(result) > 0

    def test_edge_cases_handling(self):
        """Test handling of edge cases across all functions."""
        calc = FinancialCalculator()

        # Edge cases that should not crash
        edge_cases = [
            (calc.calculate_npv, ([], 0.1)),
            (calc.calculate_irr, ([])),
            (calc.calculate_payback, (0, 1000)),
            (calc.calculate_payback, (1000, 0)),
            (calc.calculate_break_even, (1000, 10, 10)),
            (calc.calculate_roi, (0, 0)),
            (calc.generate_financial_projection, (0, 0.1, 1)),
            (calc.unit_economics_analysis, (0, 100, 0.1, 0)),
        ]

        for func, args in edge_cases:
            try:
                result = func(*args)
                # Should not crash and should return a valid result
                assert result is not None
            except Exception as e:
                # If it does raise an exception, it should be a known type
                assert isinstance(e, (ValueError, ZeroDivisionError, TypeError))

    def test_financial_metrics_realistic_scenario(self):
        """Test realistic business scenario."""
        # SaaS startup scenario
        calc = FinancialCalculator()

        # 5-year projection
        projection = calc.generate_financial_projection(
            initial_revenue=120000,  # $10k MRR
            growth_rate=1.0,  # 100% YoY growth (aggressive but realistic for early SaaS)
            years=5,
            operating_margin=0.15,  # 15% after all costs
            tax_rate=0.25,
        )

        # Unit economics
        unit_economics = calc.unit_economics_analysis(
            customer_acquisition_cost=250,
            customer_lifetime_value=1500,
            monthly_churn_rate=0.05,  # 5% monthly churn
            average_revenue_per_user=100,  # $100 ARPU
        )

        # Validate realistic results
        assert len(projection["revenues"]) == 5
        assert projection["revenues"][0] == 120000  # Year 1
        assert projection["revenues"][4] > projection["revenues"][0]  # Growth

        assert unit_economics["ltv_cac_ratio"] == 6.0  # 1500/250
        assert unit_economics["is_sustainable"] is True  # Healthy ratio
        assert unit_economics["months_to_recover_cac"] == 2.5  # 250/100
