"""
Tests for financial modeling tools.
"""

import pytest
import numpy as np
from unittest.mock import patch, Mock
from src.tools.financial_tools import (
    FinancialCalculator,
    FinancialMetrics,
    financial_tool_executor,
    create_financial_tool_spec,
)
from src.error_handling import ValidationError


class TestFinancialCalculator:
    """Test financial calculation functionality."""

    def test_calculate_npv(self):
        """Test NPV calculation."""
        calc = FinancialCalculator()
        cash_flows = [-100000, 30000, 40000, 50000, 60000]
        discount_rate = 0.1

        npv = calc.calculate_npv(cash_flows, discount_rate)

        # NPV should be positive for this profitable project
        assert npv > 0
        assert isinstance(npv, float)

    def test_calculate_npv_negative(self):
        """Test NPV calculation for unprofitable project."""
        calc = FinancialCalculator()
        cash_flows = [-100000, 10000, 10000, 10000, 10000]
        discount_rate = 0.15

        npv = calc.calculate_npv(cash_flows, discount_rate)

        # NPV should be negative for this unprofitable project
        assert npv < 0

    def test_calculate_irr(self):
        """Test IRR calculation."""
        calc = FinancialCalculator()
        cash_flows = [-100000, 30000, 40000, 50000, 60000]

        irr = calc.calculate_irr(cash_flows)

        # IRR should be a reasonable percentage
        assert 0.1 < irr < 0.5  # Between 10% and 50%
        assert isinstance(irr, float)

    def test_calculate_irr_no_solution(self):
        """Test IRR calculation when no solution exists."""
        calc = FinancialCalculator()
        cash_flows = [100000, 10000, 10000, 10000]  # All positive

        irr = calc.calculate_irr(cash_flows)

        # Should return None when no solution
        assert irr is None

    def test_calculate_payback_period(self):
        """Test payback period calculation."""
        calc = FinancialCalculator()
        cash_flows = [-100000, 30000, 40000, 50000, 60000]

        payback = calc.calculate_payback_period(cash_flows)

        # Should recover investment in less than 4 years
        assert 2 < payback < 4
        assert isinstance(payback, float)

    def test_calculate_payback_period_never(self):
        """Test payback period when investment never recovered."""
        calc = FinancialCalculator()
        cash_flows = [-100000, 10000, 10000, 10000]  # Never recovers

        payback = calc.calculate_payback_period(cash_flows)

        # Should return None when never recovers
        assert payback is None

    def test_calculate_break_even(self):
        """Test break-even analysis."""
        calc = FinancialCalculator()

        break_even = calc.calculate_break_even(
            fixed_costs=50000, variable_cost_per_unit=20, price_per_unit=50
        )

        # Break-even should be reasonable
        assert break_even > 0
        assert break_even == 50000 / (50 - 20)  # 1,667 units

    def test_calculate_roi(self):
        """Test ROI calculation."""
        calc = FinancialCalculator()

        roi = calc.calculate_roi(gain=150000, investment=100000)

        assert roi == 0.5  # 50% ROI

    def test_unit_economics(self):
        """Test unit economics calculations."""
        calc = FinancialCalculator()

        metrics = calc.calculate_unit_economics(
            cac=100, ltv=500, monthly_revenue_per_customer=50, monthly_churn_rate=0.05
        )

        assert metrics["ltv_cac_ratio"] == 5.0
        assert metrics["payback_months"] == 2.0
        assert metrics["monthly_cohort_value"] > 0

    def test_financial_model_comprehensive(self):
        """Test comprehensive financial model."""
        calc = FinancialCalculator()

        params = {
            "initial_investment": 100000,
            "monthly_revenue": 10000,
            "monthly_costs": 7000,
            "growth_rate": 0.1,
            "periods": 12,
            "discount_rate": 0.1,
        }

        result = calc.calculate_comprehensive_model(**params)

        assert "npv" in result
        assert "irr" in result
        assert "payback_period" in result
        assert "break_even_point" in result
        assert "roi" in result
        assert isinstance(result["npv"], float)


class TestFinancialToolExecutor:
    """Test financial tool executor."""

    def test_npv_operation(self, sample_financial_params):
        """Test NPV operation through executor."""
        result = financial_tool_executor(
            "npv",
            {
                "cash_flows": sample_financial_params["cash_flows"],
                "discount_rate": sample_financial_params["discount_rate"],
            },
        )

        assert "npv" in result
        assert isinstance(result["npv"], float)

    def test_irr_operation(self, sample_financial_params):
        """Test IRR operation through executor."""
        result = financial_tool_executor(
            "irr", {"cash_flows": sample_financial_params["cash_flows"]}
        )

        assert "irr" in result
        # IRR might be None for some cash flows
        if result["irr"] is not None:
            assert isinstance(result["irr"], float)

    def test_payback_operation(self, sample_financial_params):
        """Test payback period operation."""
        result = financial_tool_executor(
            "payback", {"cash_flows": sample_financial_params["cash_flows"]}
        )

        assert "payback_period" in result
        if result["payback_period"] is not None:
            assert isinstance(result["payback_period"], float)

    def test_break_even_operation(self):
        """Test break-even operation."""
        result = financial_tool_executor(
            "break_even", {"fixed_costs": 50000, "variable_cost_per_unit": 20, "price_per_unit": 50}
        )

        assert "break_even_point" in result
        assert isinstance(result["break_even_point"], (int, float))

    def test_roi_operation(self):
        """Test ROI operation."""
        result = financial_tool_executor("roi", {"gain": 150000, "investment": 100000})

        assert "roi" in result
        assert isinstance(result["roi"], float)

    def test_unit_economics_operation(self):
        """Test unit economics operation."""
        result = financial_tool_executor(
            "unit_economics",
            {
                "cac": 100,
                "ltv": 500,
                "monthly_revenue_per_customer": 50,
                "monthly_churn_rate": 0.05,
            },
        )

        assert "ltv_cac_ratio" in result
        assert "payback_months" in result
        assert isinstance(result["ltv_cac_ratio"], float)

    def test_comprehensive_model_operation(self, sample_financial_params):
        """Test comprehensive financial model operation."""
        result = financial_tool_executor(
            "comprehensive_model",
            {
                "initial_investment": sample_financial_params["initial_investment"],
                "monthly_revenue": sample_financial_params["monthly_revenue"],
                "monthly_costs": sample_financial_params["monthly_costs"],
                "growth_rate": 0.1,
                "periods": 12,
                "discount_rate": sample_financial_params["discount_rate"],
            },
        )

        assert "npv" in result
        assert "irr" in result
        assert "payback_period" in result
        assert "break_even_point" in result
        assert "roi" in result

    def test_invalid_operation(self):
        """Test handling of invalid operation."""
        result = financial_tool_executor("invalid_operation", {})

        assert "error" in result
        assert "invalid_operation" in result["error"]

    def test_missing_parameters(self):
        """Test handling of missing parameters."""
        result = financial_tool_executor("npv", {})

        assert "error" in result

    def test_invalid_cash_flows(self):
        """Test handling of invalid cash flows."""
        result = financial_tool_executor("npv", {"cash_flows": "not_a_list", "discount_rate": 0.1})

        assert "error" in result


class TestFinancialToolSpec:
    """Test financial tool specification."""

    def test_create_tool_spec(self):
        """Test creation of tool specification."""
        spec = create_financial_tool_spec()

        assert "name" in spec
        assert "description" in spec
        assert "parameters" in spec
        assert spec["name"] == "financial_calculator"

        # Check parameters structure
        params = spec["parameters"]
        assert "type" in params
        assert "properties" in params
        assert "required" in params

        # Check required fields
        assert "operation" in params["required"]
        assert "params" in params["required"]

        # Check operation enum
        operation_enum = params["properties"]["operation"]["enum"]
        expected_operations = [
            "npv",
            "irr",
            "payback",
            "break_even",
            "roi",
            "unit_economics",
            "comprehensive_model",
        ]
        for op in expected_operations:
            assert op in operation_enum
