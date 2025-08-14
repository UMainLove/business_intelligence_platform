"""
Synthetic tests for financial tools without external dependencies.
"""

import pytest
from src.tools.financial_tools import (
    FinancialCalculator,
    FinancialMetrics,
    financial_tool_executor,
)


class TestFinancialCalculatorSynthetic:
    """Test FinancialCalculator with synthetic data."""

    def setup_method(self):
        """Set up test fixtures."""
        self.calc = FinancialCalculator()

    def test_calculate_npv(self):
        """Test NPV calculation with synthetic cash flows."""
        # Test case: Initial investment of $1000, returns $300, $400, $500
        cash_flows = [-1000, 300, 400, 500]
        discount_rate = 0.1
        
        npv = self.calc.calculate_npv(cash_flows, discount_rate)
        
        # Expected NPV calculation: -1000 + 300/1.1 + 400/1.21 + 500/1.331
        expected = -1000 + 272.73 + 330.58 + 375.66  # Approximately -21.03
        assert abs(npv - expected) < 1.0, f"NPV calculation error: got {npv}, expected ~{expected}"

    def test_calculate_irr(self):
        """Test IRR calculation with synthetic cash flows."""
        cash_flows = [-1000, 300, 400, 500]
        
        irr = self.calc.calculate_irr(cash_flows)
        
        # IRR should be between 0 and 1 (0% to 100%)
        assert 0 <= irr <= 1, f"IRR out of reasonable range: {irr}"
        
        # Verify NPV at IRR is approximately zero
        npv_at_irr = self.calc.calculate_npv(cash_flows, irr)
        assert abs(npv_at_irr) < 0.01, f"NPV at IRR should be ~0, got {npv_at_irr}"

    def test_calculate_payback(self):
        """Test payback period calculation."""
        initial_investment = 10000
        annual_cash_flow = 2500
        
        payback = self.calc.calculate_payback(initial_investment, annual_cash_flow)
        
        assert payback == 4.0, f"Payback should be 4 years, got {payback}"

    def test_calculate_payback_zero_flow(self):
        """Test payback with zero cash flow."""
        payback = self.calc.calculate_payback(1000, 0)
        assert payback == float('inf'), "Should return infinity for zero cash flow"

    def test_calculate_break_even(self):
        """Test break-even calculation."""
        fixed_costs = 10000
        price_per_unit = 50
        variable_cost_per_unit = 30
        
        break_even = self.calc.calculate_break_even(fixed_costs, price_per_unit, variable_cost_per_unit)
        
        # Break-even = 10000 / (50-30) = 500 units
        assert break_even == 500, f"Break-even should be 500 units, got {break_even}"

    def test_calculate_roi(self):
        """Test ROI calculation."""
        gain = 1500
        cost = 1000
        
        roi = self.calc.calculate_roi(gain, cost)
        
        # ROI = (1500-1000)/1000 * 100 = 50%
        assert roi == 50.0, f"ROI should be 50%, got {roi}"

    def test_generate_financial_projection(self):
        """Test financial projection generation."""
        projection = self.calc.generate_financial_projection(
            initial_revenue=100000,
            growth_rate=0.2,
            years=3,
            operating_margin=0.25,
            tax_rate=0.3
        )
        
        assert "revenues" in projection
        assert "ebitda" in projection
        assert "net_income" in projection
        assert len(projection["revenues"]) == 3
        
        # Year 1: 100k, Year 2: 120k, Year 3: 144k
        assert projection["revenues"][0] == 100000
        assert projection["revenues"][1] == 120000
        assert projection["revenues"][2] == 144000

    def test_unit_economics_analysis(self):
        """Test unit economics analysis."""
        analysis = self.calc.unit_economics_analysis(
            customer_acquisition_cost=100,
            customer_lifetime_value=500,
            monthly_churn_rate=0.05,
            average_revenue_per_user=50
        )
        
        assert "ltv_cac_ratio" in analysis
        assert "months_to_recover_cac" in analysis
        assert "is_sustainable" in analysis
        
        # LTV/CAC = 500/100 = 5.0
        assert analysis["ltv_cac_ratio"] == 5.0
        assert analysis["is_sustainable"] is True  # > 3 threshold

    def test_safe_exec_financial_code_disabled(self):
        """Test that code execution is safely disabled."""
        result = self.calc.safe_exec_financial_code("print('test')")
        
        assert result["success"] is False
        assert "security reasons" in result["error"]
        assert result["variables"] == {}


class TestFinancialToolExecutor:
    """Test financial tool executor with synthetic data."""

    def test_npv_operation(self):
        """Test NPV operation through executor."""
        result = financial_tool_executor("npv", {
            "cash_flows": [-1000, 300, 400, 500],
            "discount_rate": 0.1
        })
        
        assert "npv" in result
        assert isinstance(result["npv"], (int, float))

    def test_roi_operation(self):
        """Test ROI operation through executor."""
        result = financial_tool_executor("roi", {
            "gain": 1500,
            "cost": 1000
        })
        
        assert "roi_percentage" in result
        assert result["roi_percentage"] == 50.0

    def test_projection_operation(self):
        """Test projection operation through executor."""
        result = financial_tool_executor("projection", {
            "initial_revenue": 100000,
            "growth_rate": 0.2,
            "years": 3
        })
        
        assert "revenues" in result
        assert len(result["revenues"]) == 3

    def test_unknown_operation(self):
        """Test error handling for unknown operation."""
        result = financial_tool_executor("unknown", {})
        
        assert "error" in result
        assert "Unknown operation" in result["error"]


class TestFinancialMetrics:
    """Test FinancialMetrics dataclass."""

    def test_financial_metrics_creation(self):
        """Test creating FinancialMetrics instance."""
        metrics = FinancialMetrics(
            npv=1000.0,
            irr=0.15,
            payback_period=3.5,
            break_even_point=500,
            roi=25.0
        )
        
        assert metrics.npv == 1000.0
        assert metrics.irr == 0.15
        assert metrics.payback_period == 3.5
        assert metrics.break_even_point == 500
        assert metrics.roi == 25.0