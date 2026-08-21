"""
Unified Australian Accounting MCP Server
Exposes deterministic calculation engines, ATO benchmarks, and compliance tools
over the Model Context Protocol (MCP).
"""

from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any, Dict

from mcp.server.fastmcp import FastMCP

from .engines.benchmarks import analyze_ato_benchmarks
from .engines.div7a import generate_div7a_schedule, generate_dividend_offset_journal
from .engines.paydaysuper_sim import ClearingHouseType, simulate_payday_super
from .engines.synthetic_sbr import (
    generate_synthetic_bas_payload,
    generate_synthetic_ctr_payload,
)

# Initialize FastMCP Server
mcp = FastMCP("aus-accounting-mcp")

MoneyInput = str | int | float


def _decimal_input(value: MoneyInput, field_name: str) -> Decimal:
    if isinstance(value, bool):
        raise TypeError(f"{field_name} must be a finite decimal value")
    try:
        parsed = Decimal(value) if isinstance(value, int) else Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"{field_name} must be a finite decimal value") from exc
    if not parsed.is_finite():
        raise ValueError(f"{field_name} must be a finite decimal value")
    return parsed


def _decimal_text(value: Decimal) -> str:
    return format(value, "f")


def _monetary_precision(*values: MoneyInput | None) -> dict[str, str | None]:
    exact_inputs = all(value is None or isinstance(value, str) for value in values)
    return {
        "input_mode": "exact_decimal_string" if exact_inputs else "legacy_json_number",
        "input_warning": None
        if exact_inputs
        else (
            "JSON numbers may already be rounded by a client or parser; send "
            "monetary inputs as decimal strings for exact values."
        ),
        "output_warning": (
            "Numeric monetary fields remain for compatibility and may round; "
            "use the corresponding *_exact string fields for exact values."
        ),
    }


@mcp.tool()
def get_ato_benchmarks(
    industry_key: str,
    annual_turnover: MoneyInput,
    cost_of_sales: MoneyInput | None = None,
    labour_expenses: MoneyInput | None = None,
    rent_expenses: MoneyInput | None = None,
    motor_vehicle_expenses: MoneyInput | None = None,
) -> Dict[str, Any]:
    """
    Query ATO Small Business Benchmarks and analyze expense variances against official ratios.
    Available industries: cafes_and_restaurants, residential_building_construction, hairdressing_and_beauty, plumbing_services, management_consultancy.
    Send monetary values as decimal strings for exact input and use the *_exact
    result fields for exact output.
    """
    annual_turnover_decimal = _decimal_input(annual_turnover, "annual_turnover")
    cost_of_sales_decimal = (
        _decimal_input(cost_of_sales, "cost_of_sales")
        if cost_of_sales is not None
        else None
    )
    labour_expenses_decimal = (
        _decimal_input(labour_expenses, "labour_expenses")
        if labour_expenses is not None
        else None
    )
    rent_expenses_decimal = (
        _decimal_input(rent_expenses, "rent_expenses")
        if rent_expenses is not None
        else None
    )
    motor_vehicle_expenses_decimal = (
        _decimal_input(motor_vehicle_expenses, "motor_vehicle_expenses")
        if motor_vehicle_expenses is not None
        else None
    )

    res = analyze_ato_benchmarks(
        industry_key=industry_key,
        annual_turnover=annual_turnover_decimal,
        cost_of_sales=cost_of_sales_decimal,
        labour_expenses=labour_expenses_decimal,
        rent_expenses=rent_expenses_decimal,
        motor_vehicle_expenses=motor_vehicle_expenses_decimal,
    )

    return {
        "industry": res.industry_key,
        "annual_turnover": float(res.annual_turnover),
        "annual_turnover_exact": _decimal_text(res.annual_turnover),
        "overall_audit_risk": res.overall_audit_risk,
        "metrics": [
            {
                "metric": m.metric_name,
                "actual_amount": float(m.actual_amount),
                "actual_amount_exact": _decimal_text(m.actual_amount),
                "actual_percentage": float(m.actual_percentage),
                "actual_percentage_exact": _decimal_text(m.actual_percentage),
                "benchmark_range": f"{m.benchmark_low}% - {m.benchmark_high}% (median {m.benchmark_median}%)",
                "status": m.status,
                "risk_level": m.risk_level,
            }
            for m in res.metrics_evaluated
        ],
        "monetary_precision": _monetary_precision(
            annual_turnover,
            cost_of_sales,
            labour_expenses,
            rent_expenses,
            motor_vehicle_expenses,
        ),
    }


@mcp.tool()
def calc_payday_super_deadline(
    pay_date_iso: str,
    submission_date_iso: str,
    sg_contribution: MoneyInput,
    clearing_house_type: str = "COMMERCIAL",
    total_salary_wages: MoneyInput | None = None,
) -> Dict[str, Any]:
    """
    Simulate Payday Super 2026 compliance window (7 business days from payday)
    and fail closed on late receipt because full post-reform SGC facts are not
    available to this tool.
    Send monetary values as decimal strings for exact input and use the *_exact
    result fields for exact output. JSON numbers remain supported for existing
    clients and are explicitly marked as a potentially rounded legacy mode.
    """
    ch_type = ClearingHouseType[clearing_house_type.upper()]
    p_date = date.fromisoformat(pay_date_iso)
    s_date = date.fromisoformat(submission_date_iso)

    sg_contribution_decimal = _decimal_input(sg_contribution, "sg_contribution")
    total_salary_wages_decimal = (
        _decimal_input(total_salary_wages, "total_salary_wages")
        if total_salary_wages is not None
        else None
    )

    res = simulate_payday_super(
        pay_date=p_date,
        submission_date=s_date,
        sg_contribution=sg_contribution_decimal,
        total_salary_wages=total_salary_wages_decimal,
        clearing_house_type=ch_type,
    )

    return {
        "pay_date": res.pay_date.isoformat(),
        "statutory_due_date": res.statutory_due_date.isoformat(),
        "clearing_house_submission": res.clearing_house_submission_date.isoformat(),
        "estimated_fund_receipt": res.estimated_fund_receipt_date.isoformat(),
        "is_compliant": res.is_compliant,
        "business_days_from_pay": res.business_days_taken,
        "sg_contribution": float(res.sg_contribution_amount),
        "sg_contribution_exact": _decimal_text(res.sg_contribution_amount),
        "sgc_exposure": {
            "shortfall": float(res.potential_sgc_shortfall),
            "shortfall_exact": _decimal_text(res.potential_sgc_shortfall),
            "nominal_interest": float(res.nominal_interest_charge),
            "nominal_interest_exact": _decimal_text(res.nominal_interest_charge),
            "admin_fee": float(res.admin_fee_charge),
            "admin_fee_exact": _decimal_text(res.admin_fee_charge),
            "total_liability": float(res.total_sgc_exposure),
            "total_liability_exact": _decimal_text(res.total_sgc_exposure),
        },
        "monetary_precision": _monetary_precision(
            sg_contribution, total_salary_wages
        ),
        "risk_assessment": res.risk_assessment,
    }


@mcp.tool()
def calc_div7a_repayment(
    borrower_name: str,
    lender_entity_name: str,
    loan_principal: MoneyInput,
    start_fy: int = 2025,
    is_secured_25_year: bool = False,
) -> Dict[str, Any]:
    """
    Generate statutory Division 7A s 109N amortisation schedule, benchmark interest rates,
    and dividend offset journal under ITAA 1936.
    Send the principal as a decimal string for exact input and use the *_exact
    result fields for exact output.
    """
    loan_principal_decimal = _decimal_input(loan_principal, "loan_principal")
    sched = generate_div7a_schedule(
        borrower_name=borrower_name,
        lender_entity_name=lender_entity_name,
        principal=loan_principal_decimal,
        start_financial_year=start_fy,
        is_secured_25_year=is_secured_25_year,
    )

    first_year = sched.schedule[0]
    journals = generate_dividend_offset_journal(
        borrower_name=borrower_name,
        lender_entity_name=lender_entity_name,
        offset_amount=first_year.minimum_yearly_repayment,
    )

    return {
        "borrower": sched.borrower_name,
        "lender": sched.lender_entity_name,
        "principal": float(sched.original_principal),
        "principal_exact": _decimal_text(sched.original_principal),
        "term_years": sched.loan_term_years,
        "total_interest_payable": float(sched.total_interest_payable),
        "total_interest_payable_exact": _decimal_text(sched.total_interest_payable),
        "schedule": [
            {
                "year_index": y.year_index,
                "financial_year": y.financial_year,
                "opening_balance": float(y.opening_balance),
                "opening_balance_exact": _decimal_text(y.opening_balance),
                "benchmark_rate": float(y.benchmark_interest_rate),
                "benchmark_rate_exact": _decimal_text(y.benchmark_interest_rate),
                "interest_charge": float(y.interest_charge),
                "interest_charge_exact": _decimal_text(y.interest_charge),
                "minimum_yearly_repayment": float(y.minimum_yearly_repayment),
                "minimum_yearly_repayment_exact": _decimal_text(
                    y.minimum_yearly_repayment
                ),
                "principal_reduction": float(y.principal_reduction),
                "principal_reduction_exact": _decimal_text(y.principal_reduction),
                "closing_balance": float(y.closing_balance),
                "closing_balance_exact": _decimal_text(y.closing_balance),
            }
            for y in sched.schedule
        ],
        "first_year_myr_offset_journal": journals,
        "monetary_precision": _monetary_precision(loan_principal),
    }


@mcp.tool()
def generate_synthetic_sbr_fixture(
    form_type: str,
    entity_name: str = "Synthetix Pty Ltd",
    revenue_or_sales: MoneyInput = 1000000.0,
) -> Dict[str, Any]:
    """
    Generate synthetic, privacy-safe Standard Business Reporting (SBR) payloads
    for testing Australian tax agent workflows (form_type: 'CTR' or 'BAS').
    Send revenue or sales as a decimal string for exact input and use the
    *_exact result fields for exact output.
    """
    revenue_or_sales_decimal = _decimal_input(
        revenue_or_sales, "revenue_or_sales"
    )
    if form_type.upper() == "CTR":
        rev = revenue_or_sales_decimal
        result = generate_synthetic_ctr_payload(
            company_name=entity_name,
            gross_revenue=rev,
            cost_of_sales=(rev * Decimal("0.4")).quantize(Decimal("0.01")),
            deductible_operating_expenses=(rev * Decimal("0.3")).quantize(Decimal("0.01")),
        )
    elif form_type.upper() == "BAS":
        sales = revenue_or_sales_decimal
        result = generate_synthetic_bas_payload(
            entity_name=entity_name,
            total_sales_g1=sales,
            capital_purchases_g10=Decimal("11000.00"),
            non_capital_purchases_g11=(sales * Decimal("0.4")).quantize(Decimal("0.01")),
        )
    else:
        raise ValueError(f"Unknown form_type '{form_type}'. Supported: 'CTR', 'BAS'.")

    result["monetary_precision"] = _monetary_precision(revenue_or_sales)
    return result


def run_stdio() -> None:
    """Run MCP server over stdio transport."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    run_stdio()
