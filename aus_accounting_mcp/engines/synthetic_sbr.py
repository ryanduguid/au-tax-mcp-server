"""
Synthetic SBR (Standard Business Reporting) Fixture Generator.
Provides synthetic test data for Company Tax Returns, BAS, and STP Phase 2.
"""

from decimal import Decimal
from typing import Any, Dict, Optional


def _decimal_text(value: Decimal) -> str:
    return format(value, "f")


def generate_synthetic_ctr_payload(
    company_name: str = "Synthetix Pty Ltd",
    tfn_masked: str = "XXX-XXX-123",
    abn: str = "11 222 333 444",
    financial_year: int = 2025,
    gross_revenue: Decimal = Decimal("2500000.00"),
    cost_of_sales: Optional[Decimal] = None,
    deductible_operating_expenses: Optional[Decimal] = None,
    non_deductible_entertainment: Decimal = Decimal("15000.00"),
    is_base_rate_entity: bool = True,
) -> Dict[str, Any]:
    """
    Generate synthetic Company Tax Return (CTR) data payload for AI agent testing.
    """
    cos = cost_of_sales if cost_of_sales is not None else (gross_revenue * Decimal("0.40")).quantize(Decimal("0.01"))
    expenses = deductible_operating_expenses if deductible_operating_expenses is not None else (gross_revenue * Decimal("0.30")).quantize(Decimal("0.01"))

    gross_profit = gross_revenue - cos
    accounting_net_profit = gross_profit - expenses - non_deductible_entertainment

    # Reconciliation to taxable income
    taxable_income = accounting_net_profit + non_deductible_entertainment
    tax_rate = Decimal("0.25") if is_base_rate_entity else Decimal("0.30")
    tax_liability = (taxable_income * tax_rate).quantize(Decimal("0.01"))

    return {
        "form_type": "CTR_AU_2025",
        "entity": {
            "legal_name": company_name,
            "tfn": tfn_masked,
            "abn": abn,
            "financial_year": financial_year,
            "base_rate_entity": is_base_rate_entity,
        },
        "income_statement": {
            "total_business_income": float(gross_revenue),
            "total_business_income_exact": _decimal_text(gross_revenue),
            "cost_of_sales": float(cos),
            "cost_of_sales_exact": _decimal_text(cos),
            "gross_profit": float(gross_profit),
            "gross_profit_exact": _decimal_text(gross_profit),
            "total_expenses": float(expenses + non_deductible_entertainment),
            "total_expenses_exact": _decimal_text(
                expenses + non_deductible_entertainment
            ),
            "operating_net_profit": float(accounting_net_profit),
            "operating_net_profit_exact": _decimal_text(accounting_net_profit),
        },
        "reconciliation": {
            "accounting_profit": float(accounting_net_profit),
            "accounting_profit_exact": _decimal_text(accounting_net_profit),
            "add_back_non_deductible": float(non_deductible_entertainment),
            "add_back_non_deductible_exact": _decimal_text(
                non_deductible_entertainment
            ),
            "taxable_income": float(taxable_income),
            "taxable_income_exact": _decimal_text(taxable_income),
            "applicable_tax_rate": float(tax_rate),
            "applicable_tax_rate_exact": _decimal_text(tax_rate),
            "gross_tax_liability": float(tax_liability),
            "gross_tax_liability_exact": _decimal_text(tax_liability),
        },
    }


def generate_synthetic_bas_payload(
    entity_name: str = "Synthetix Pty Ltd",
    abn: str = "11 222 333 444",
    quarter_ended: str = "2025-03-31",
    total_sales_g1: Decimal = Decimal("660000.00"),     # Inc GST
    capital_purchases_g10: Decimal = Decimal("55000.00"), # Inc GST
    non_capital_purchases_g11: Optional[Decimal] = None, # Inc GST
    total_salary_wages_w1: Decimal = Decimal("150000.00"),
    payg_withheld_w2: Decimal = Decimal("37500.00"),
) -> Dict[str, Any]:
    """
    Generate synthetic Business Activity Statement (BAS) payload.
    """
    g11 = non_capital_purchases_g11 if non_capital_purchases_g11 is not None else (total_sales_g1 * Decimal("0.40")).quantize(Decimal("0.01"))

    gst_collected_1a = (total_sales_g1 / Decimal("11.0")).quantize(Decimal("0.01"))
    gst_purchases_1b = ((capital_purchases_g10 + g11) / Decimal("11.0")).quantize(Decimal("0.01"))
    net_gst = gst_collected_1a - gst_purchases_1b
    net_bas_payable = net_gst + payg_withheld_w2

    return {
        "form_type": "BAS_AU_ACTIVITY_STATEMENT",
        "entity": {
            "name": entity_name,
            "abn": abn,
            "quarter_ended": quarter_ended,
        },
        "gst_labels": {
            "G1_total_sales": float(total_sales_g1),
            "G1_total_sales_exact": _decimal_text(total_sales_g1),
            "G10_capital_purchases": float(capital_purchases_g10),
            "G10_capital_purchases_exact": _decimal_text(capital_purchases_g10),
            "G11_non_capital_purchases": float(g11),
            "G11_non_capital_purchases_exact": _decimal_text(g11),
            "1A_gst_on_sales": float(gst_collected_1a),
            "1A_gst_on_sales_exact": _decimal_text(gst_collected_1a),
            "1B_gst_on_purchases": float(gst_purchases_1b),
            "1B_gst_on_purchases_exact": _decimal_text(gst_purchases_1b),
            "net_gst": float(net_gst),
            "net_gst_exact": _decimal_text(net_gst),
        },
        "payg_withholding_labels": {
            "W1_total_salary_wages": float(total_salary_wages_w1),
            "W1_total_salary_wages_exact": _decimal_text(total_salary_wages_w1),
            "W2_amounts_withheld": float(payg_withheld_w2),
            "W2_amounts_withheld_exact": _decimal_text(payg_withheld_w2),
        },
        "summary": {
            "total_payable_to_ato": float(net_bas_payable),
            "total_payable_to_ato_exact": _decimal_text(net_bas_payable),
        },
    }
