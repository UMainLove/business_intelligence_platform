"""
Financial modeling tools with code execution capability for AG2 agents.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List

import numpy as np

from src.error_handling import ValidationError, handle_errors, track_errors, validate_input

logger = logging.getLogger(__name__)


@dataclass
class FinancialMetrics:
    """Container for financial analysis results."""

    npv: float
    irr: float
    payback_period: float
    break_even_point: int
    roi: float


class FinancialCalculator:
    """Financial modeling tool with safe code execution."""

    @staticmethod
    def calculate_npv(cash_flows: List[float], discount_rate: float) -> float:
        """Calculate Net Present Value."""
        npv = 0
        for t, cf in enumerate(cash_flows):
            npv += cf / ((1 + discount_rate) ** t)
        return npv

    @staticmethod
    def calculate_irr(cash_flows: List[float]) -> float:
        """Calculate Internal Rate of Return using Newton-Raphson method."""
        # numpy.irr was deprecated, so we implement our own
        if len(cash_flows) < 2:
            return 0.0

        # Initial guess
        rate = 0.1
        tolerance = 1e-6
        max_iterations = 100

        for _ in range(max_iterations):
            npv = sum(cf / (1 + rate) ** i for i, cf in enumerate(cash_flows))
            npv_derivative = sum(-i * cf / (1 + rate) ** (i + 1) for i, cf in enumerate(cash_flows))

            if abs(npv) < tolerance:
                return rate

            if abs(npv_derivative) < tolerance:
                break

            rate = rate - npv / npv_derivative

            # Bounds check
            if rate < -0.99:
                rate = -0.99
            elif rate > 10:
                rate = 10

        return rate

    @staticmethod
    def calculate_payback(initial_investment: float, annual_cash_flow: float) -> float:
        """Calculate simple payback period in years."""
        if annual_cash_flow <= 0:
            return float("inf")
        return initial_investment / annual_cash_flow

    @staticmethod
    def calculate_break_even(
        fixed_costs: float, price_per_unit: float, variable_cost_per_unit: float
    ) -> int:
        """Calculate break-even point in units."""
        if price_per_unit <= variable_cost_per_unit:
            return float("inf")
        contribution_margin = price_per_unit - variable_cost_per_unit
        return int(np.ceil(fixed_costs / contribution_margin))

    @staticmethod
    def calculate_roi(gain: float, cost: float) -> float:
        """Calculate Return on Investment as percentage."""
        if cost == 0:
            return 0
        return ((gain - cost) / cost) * 100

    @staticmethod
    def safe_exec_financial_code(code: str) -> Dict[str, Any]:
        """
        Safely execute financial modeling Python code.
        Returns the captured output and any defined variables.
        """
        # Security: Code execution disabled
        return {
            "success": False,
            "output": "",
            "variables": {},
            "error": "Code execution disabled for security reasons. Use specific financial calculation methods instead.",
        }

    @staticmethod
    def generate_financial_projection(
        initial_revenue: float,
        growth_rate: float,
        years: int = 5,
        operating_margin: float = 0.2,
        tax_rate: float = 0.25,
    ) -> Dict[str, List[float]]:
        """Generate multi-year financial projections."""
        revenues = []
        ebitda = []
        net_income = []

        for year in range(years):
            revenue = initial_revenue * ((1 + growth_rate) ** year)
            revenues.append(revenue)

            ebitda_val = revenue * operating_margin
            ebitda.append(ebitda_val)

            net_income_val = ebitda_val * (1 - tax_rate)
            net_income.append(net_income_val)

        return {
            "revenues": revenues,
            "ebitda": ebitda,
            "net_income": net_income,
            "years": list(range(1, years + 1)),
        }

    @staticmethod
    def unit_economics_analysis(
        customer_acquisition_cost: float,
        customer_lifetime_value: float,
        monthly_churn_rate: float,
        average_revenue_per_user: float,
    ) -> Dict[str, Any]:
        """Analyze unit economics for SaaS/subscription businesses."""
        ltv_cac_ratio = (
            customer_lifetime_value / customer_acquisition_cost
            if customer_acquisition_cost > 0
            else 0
        )
        months_to_recover_cac = (
            customer_acquisition_cost / average_revenue_per_user
            if average_revenue_per_user > 0
            else float("inf")
        )
        annual_churn = 1 - (1 - monthly_churn_rate) ** 12

        return {
            "ltv_cac_ratio": ltv_cac_ratio,
            "months_to_recover_cac": months_to_recover_cac,
            "annual_churn_rate": annual_churn * 100,
            "is_sustainable": ltv_cac_ratio > 3,  # Industry benchmark
            "health_score": min(100, (ltv_cac_ratio / 3) * 100),
        }


def create_financial_tool_spec():
    """Create tool specification for AG2 integration."""
    return {
        "name": "financial_calculator",
        "description": "Perform financial calculations and modeling",
        "parameters": {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": [
                        "npv",
                        "irr",
                        "payback",
                        "break_even",
                        "roi",
                        "projection",
                        "unit_economics",
                        "execute_code",
                    ],
                    "description": "The financial operation to perform",
                },
                "params": {"type": "object", "description": "Parameters specific to the operation"},
            },
            "required": ["operation", "params"],
        },
    }


@handle_errors(error_mapping={ValueError: ValidationError, KeyError: ValidationError})
@track_errors
def financial_tool_executor(operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute financial tool operations for AG2."""
    try:
        # Validate inputs
        validate_input({"operation": operation}, ["operation"], {"operation": str})
        validate_input(params, [], {})  # Ensure params is a dict

        calc = FinancialCalculator()
        logger.debug(f"Executing financial operation: {operation} with params: {params}")
    except Exception as e:
        logger.error(f"Financial tool validation failed: {str(e)}")
        return {"error": f"Validation failed: {str(e)}", "operation": operation}

    if operation == "npv":
        result = calc.calculate_npv(params["cash_flows"], params["discount_rate"])
        return {"npv": result}

    elif operation == "irr":
        result = calc.calculate_irr(params["cash_flows"])
        return {"irr": result}

    elif operation == "payback":
        result = calc.calculate_payback(params["initial_investment"], params["annual_cash_flow"])
        return {"payback_period_years": result}

    elif operation == "break_even":
        result = calc.calculate_break_even(
            params["fixed_costs"], params["price_per_unit"], params["variable_cost_per_unit"]
        )
        return {"break_even_units": result}

    elif operation == "roi":
        result = calc.calculate_roi(params["gain"], params["cost"])
        return {"roi_percentage": result}

    elif operation == "projection":
        return calc.generate_financial_projection(**params)

    elif operation == "unit_economics":
        return calc.unit_economics_analysis(**params)

    elif operation == "execute_code":
        return calc.safe_exec_financial_code(params["code"])

    else:
        return {"error": f"Unknown operation: {operation}"}
