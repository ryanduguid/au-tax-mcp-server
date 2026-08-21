"""
Unified Australian Accounting MCP Server
Exposes deterministic calculation engines, ATO benchmarks, and compliance tools
over the Model Context Protocol (MCP).
"""

from datetime import date
from decimal import Decimal
from typing import Optional, Dict, Any

from mcp.server.fastmcp import FastMCP

from .engines.div7a import generate_div7a_schedule, generate_dividend_offset_journal
from .engines.paydaysuper_sim import simulate_payday_super, ClearingHouseType
from .engines.benchmarks import analyze_ato_benchmarks, INDUSTRY_BENCHMARKS
from .engines.synthetic_sbr import generate_synthetic_ctr_payload, generate_synthetic_bas_payload

# Initialize FastMCP Server
mcp = FastMCP("aus-accounting-mcp")


@mcp.tool()
def get_ato_benchmarks(
    industry_key: str,
    annual_turnover: float,
    cost_of_sales: Optional[float] = None,
    labour_expenses: Optional[float] = None,
    rent_expenses: Optional[float] = None,
    motor_vehicle_expenses: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Query ATO Small Business Benchmarks and analyze expense variances against official ratios.
    Available industries: cafes_and_restaurants, residential_building_construction, hairdressing_and_beauty, plumbing_services, management_consultancy.
    """
    res = analyze_ato_benchmarks(
        industry_key=industry_key,
        annual_turnover=Decimal(str(annual_turnover)),
        cost_of_sales=Decimal(str(cost_of_sales)) if cost_of_sales is not None else None,
        labour_expenses=Decimal(str(labour_expenses)) if labour_expenses is not None else None,
        rent_expenses=Decimal(str(rent_expenses)) if rent_expenses is not None else None,
        motor_vehicle_expenses=Decimal(str(motor_vehicle_expenses)) if motor_vehicle_expenses is not None else None,
    )

    return {
        "industry": res.industry_key,
        "annual_turnover": float(res.annual_turnover),
        "overall_audit_risk": res.overall_audit_risk,
        "metrics": [
            {
                "metric": m.metric_name,
                "actual_amount": float(m.actual_amount),
                "actual_percentage": float(m.actual_percentage),
                "benchmark_range": f"{m.benchmark_low}% - {m.benchmark_high}% (median {m.benchmark_median}%)",
                "status": m.status,
                "risk_level": m.risk_level,
            }
            for m in res.metrics_evaluated
        ],
    }


@mcp.tool()
def calc_payday_super_deadline(
    pay_date_iso: str,
    submission_date_iso: str,
    sg_contribution: float,
    clearing_house_type: str = "COMMERCIAL",
    total_salary_wages: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Simulate Payday Super 2026 compliance window (7 business days from payday)
    and estimate Superannuation Guarantee Charge (SGC) exposure for late receipt.
    """
    ch_type = ClearingHouseType[clearing_house_type.upper()]
    p_date = date.fromisoformat(pay_date_iso)
    s_date = date.fromisoformat(submission_date_iso)

    res = simulate_payday_super(
        pay_date=p_date,
        submission_date=s_date,
        sg_contribution=Decimal(str(sg_contribution)),
        total_salary_wages=Decimal(str(total_salary_wages)) if total_salary_wages is not None else None,
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
        "sgc_exposure": {
            "shortfall": float(res.potential_sgc_shortfall),
            "nominal_interest": float(res.nominal_interest_charge),
            "admin_fee": float(res.admin_fee_charge),
            "total_liability": float(res.total_sgc_exposure),
        },
        "risk_assessment": res.risk_assessment,
    }


@mcp.tool()
def calc_div7a_repayment(
    borrower_name: str,
    lender_entity_name: str,
    loan_principal: float,
    start_fy: int = 2025,
    is_secured_25_year: bool = False,
) -> Dict[str, Any]:
    """
    Generate statutory Division 7A s 109N amortisation schedule, benchmark interest rates,
    and dividend offset journal under ITAA 1936.
    """
    sched = generate_div7a_schedule(
        borrower_name=borrower_name,
        lender_entity_name=lender_entity_name,
        principal=Decimal(str(loan_principal)),
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
        "term_years": sched.loan_term_years,
        "total_interest_payable": float(sched.total_interest_payable),
        "schedule": [
            {
                "year_index": y.year_index,
                "financial_year": y.financial_year,
                "opening_balance": float(y.opening_balance),
                "benchmark_rate": float(y.benchmark_interest_rate),
                "interest_charge": float(y.interest_charge),
                "minimum_yearly_repayment": float(y.minimum_yearly_repayment),
                "principal_reduction": float(y.principal_reduction),
                "closing_balance": float(y.closing_balance),
            }
            for y in sched.schedule
        ],
        "first_year_myr_offset_journal": journals,
    }


@mcp.tool()
def generate_synthetic_sbr_fixture(
    form_type: str,
    entity_name: str = "Synthetix Pty Ltd",
    revenue_or_sales: float = 1000000.0,
) -> Dict[str, Any]:
    """
    Generate synthetic, privacy-safe Standard Business Reporting (SBR) payloads
    for testing Australian tax agent workflows (form_type: 'CTR' or 'BAS').
    """
    if form_type.upper() == "CTR":
        rev = Decimal(str(revenue_or_sales))
        return generate_synthetic_ctr_payload(
            company_name=entity_name,
            gross_revenue=rev,
            cost_of_sales=(rev * Decimal("0.4")).quantize(Decimal("0.01")),
            deductible_operating_expenses=(rev * Decimal("0.3")).quantize(Decimal("0.01")),
        )
    elif form_type.upper() == "BAS":
        sales = Decimal(str(revenue_or_sales))
        return generate_synthetic_bas_payload(
            entity_name=entity_name,
            total_sales_g1=sales,
            capital_purchases_g10=Decimal("11000.00"),
            non_capital_purchases_g11=(sales * Decimal("0.4")).quantize(Decimal("0.01")),
        )
    else:
        raise ValueError(f"Unknown form_type '{form_type}'. Supported: 'CTR', 'BAS'.")


def run_stdio() -> None:
    """Run MCP server over stdio transport."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    run_stdio()