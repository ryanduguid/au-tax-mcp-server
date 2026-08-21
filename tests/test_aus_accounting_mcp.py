from datetime import date
from decimal import Decimal
from aus_accounting_mcp.engines.div7a import generate_div7a_schedule, calculate_div7a_myr, generate_dividend_offset_journal
from aus_accounting_mcp.engines.paydaysuper_sim import simulate_payday_super, ClearingHouseType
from aus_accounting_mcp.engines.benchmarks import analyze_ato_benchmarks
from aus_accounting_mcp.engines.synthetic_sbr import generate_synthetic_ctr_payload, generate_synthetic_bas_payload
from aus_accounting_mcp.server import get_ato_benchmarks, calc_payday_super_deadline, calc_div7a_repayment, generate_synthetic_sbr_fixture

def test_div7a_amortisation_7year():
    # $100k loan at FY2025 benchmark rate (8.77%)
    sched = generate_div7a_schedule(
        borrower_name="John Doe",
        lender_entity_name="Acme Pty Ltd",
        principal=Decimal("100000.00"),
        start_financial_year=2025,
        is_secured_25_year=False,
    )
    assert sched.loan_term_years == 7
    assert len(sched.schedule) == 7
    first_year = sched.schedule[0]
    assert first_year.benchmark_interest_rate == Decimal("0.0877")
    assert first_year.interest_charge == Decimal("8770.00")
    assert first_year.minimum_yearly_repayment > Decimal("19000.00")
    # Final year closing balance is 0
    assert sched.schedule[-1].closing_balance == Decimal("0.00")

def test_dividend_offset_journal():
    journals = generate_dividend_offset_journal(
        borrower_name="John Doe",
        lender_entity_name="Acme Pty Ltd",
        offset_amount=Decimal("20000.00"),
        corporate_tax_rate=Decimal("0.25"),
    )
    assert len(journals) == 3
    # Franking debit is 20000 * (0.25 / 0.75) = 6666.67
    assert "$6,666.67" in journals[2]["debit"]

def test_payday_super_simulation():
    # Compliant scenario: Commercial clearing house submitted on payday
    comp_res = simulate_payday_super(
        pay_date=date(2026, 7, 7),        # Tuesday
        submission_date=date(2026, 7, 7), # Tuesday
        sg_contribution=Decimal("1150.00"),
        clearing_house_type=ClearingHouseType.COMMERCIAL, # +2 business days -> Thursday 9 July
    )
    assert comp_res.is_compliant is True
    assert comp_res.total_sgc_exposure == Decimal("0.00")

def test_ato_benchmarks_analysis():
    # Cafe with turnover $1M, cost of sales $300k (30% within 28-37% range)
    res = analyze_ato_benchmarks(
        industry_key="cafes_and_restaurants",
        annual_turnover=Decimal("1000000.00"),
        cost_of_sales=Decimal("300000.00"),
        labour_expenses=Decimal("290000.00"),
    )
    assert res.overall_audit_risk == "LOW"
    assert len(res.metrics_evaluated) == 2
    assert res.metrics_evaluated[0].status == "WITHIN_RANGE"

def test_synthetic_sbr_fixtures():
    ctr = generate_synthetic_ctr_payload(gross_revenue=Decimal("1000000.00"))
    assert ctr["form_type"] == "CTR_AU_2025"
    assert ctr["income_statement"]["gross_profit"] == 600000.0

    bas = generate_synthetic_bas_payload(total_sales_g1=Decimal("110000.00"))
    assert bas["gst_labels"]["1A_gst_on_sales"] == 10000.0

def test_mcp_tool_functions():
    bm_tool = get_ato_benchmarks("cafes_and_restaurants", 500000.0, cost_of_sales=150000.0)
    assert bm_tool["industry"] == "cafes_and_restaurants"

    pds_tool = calc_payday_super_deadline("2026-07-07", "2026-07-07", 1000.0)
    assert pds_tool["is_compliant"] is True

    div7a_tool = calc_div7a_repayment("Alice", "HoldingCo Pty Ltd", 50000.0)
    assert div7a_tool["principal"] == 50000.0
    assert len(div7a_tool["schedule"]) == 7
