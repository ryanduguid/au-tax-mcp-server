"""
Division 7A ITAA 1936 Loan Amortisation, Minimum Yearly Repayments (MYR),
Benchmark Interest Rates, and Dividend Offset Journals.
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, localcontext
from typing import Dict, List

# ATO Division 7A Benchmark Interest Rates (s 109N(2))
BENCHMARK_RATES: Dict[int, Decimal] = {
    2015: Decimal("0.0595"),
    2016: Decimal("0.0545"),
    2017: Decimal("0.0540"),
    2018: Decimal("0.0530"),
    2019: Decimal("0.0520"),
    2020: Decimal("0.0537"),
    2021: Decimal("0.0452"),
    2022: Decimal("0.0452"),
    2023: Decimal("0.0477"),
    2024: Decimal("0.0827"),
    2025: Decimal("0.0877"),
    2026: Decimal("0.0877"),
}


@dataclass(frozen=True)
class AmortisationYear:
    year_index: int
    financial_year: int
    opening_balance: Decimal
    benchmark_interest_rate: Decimal
    interest_charge: Decimal
    minimum_yearly_repayment: Decimal
    principal_reduction: Decimal
    closing_balance: Decimal


@dataclass(frozen=True)
class Div7ALoanSchedule:
    borrower_name: str
    lender_entity_name: str
    original_principal: Decimal
    loan_term_years: int
    is_secured_25_year: bool
    schedule: List[AmortisationYear]
    total_interest_payable: Decimal


def calculate_div7a_myr(
    opening_balance: Decimal,
    benchmark_rate: Decimal,
    remaining_term_years: int,
) -> Decimal:
    """
    Calculate statutory Minimum Yearly Repayment (MYR) under s 109E(6) ITAA 1936.
    Formula: P = [I * L] / [1 - (1 + I)^(-N)]
    """
    if opening_balance <= Decimal("0.00") or remaining_term_years <= 0:
        return Decimal("0.00")

    with localcontext() as context:
        context.prec = max(50, len(opening_balance.as_tuple().digits) + 20)
        denominator = Decimal("1") - (
            (Decimal("1") + benchmark_rate) ** (-remaining_term_years)
        )
        if denominator <= 0:
            return Decimal("0.00")
        myr = (benchmark_rate * opening_balance) / denominator

    return myr.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def generate_div7a_schedule(
    borrower_name: str,
    lender_entity_name: str,
    principal: Decimal,
    start_financial_year: int,
    is_secured_25_year: bool = False,
) -> Div7ALoanSchedule:
    """
    Generate full statutory Division 7A amortisation schedule across standard term
    (7 years unsecured under s 109N(3)(a) or 25 years secured under s 109N(3)(b)).
    """
    term_years = 25 if is_secured_25_year else 7
    schedule: List[AmortisationYear] = []
    current_balance = principal
    total_interest = Decimal("0.00")

    for year_idx in range(1, term_years + 1):
        fy = start_financial_year + year_idx - 1
        rate = BENCHMARK_RATES.get(fy, BENCHMARK_RATES[2025])
        rem_years = term_years - year_idx + 1

        myr = calculate_div7a_myr(current_balance, rate, rem_years)
        interest = (current_balance * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        if year_idx == term_years:
            # Final year cleanup
            principal_reduction = current_balance
            myr = current_balance + interest
            closing = Decimal("0.00")
        else:
            principal_reduction = max(Decimal("0.00"), myr - interest)
            closing = max(Decimal("0.00"), current_balance - principal_reduction)

        total_interest += interest
        schedule.append(
            AmortisationYear(
                year_index=year_idx,
                financial_year=fy,
                opening_balance=current_balance,
                benchmark_interest_rate=rate,
                interest_charge=interest,
                minimum_yearly_repayment=myr,
                principal_reduction=principal_reduction,
                closing_balance=closing,
            )
        )
        current_balance = closing

    return Div7ALoanSchedule(
        borrower_name=borrower_name,
        lender_entity_name=lender_entity_name,
        original_principal=principal,
        loan_term_years=term_years,
        is_secured_25_year=is_secured_25_year,
        schedule=schedule,
        total_interest_payable=total_interest,
    )


def generate_dividend_offset_journal(
    borrower_name: str,
    lender_entity_name: str,
    offset_amount: Decimal,
    corporate_tax_rate: Decimal = Decimal("0.25"),
) -> List[Dict[str, str]]:
    """
    Generate journal entries to satisfy Div 7A MYR via declared franked dividend offset.
    """
    multiplier = corporate_tax_rate / (Decimal("1.00") - corporate_tax_rate)
    franking_credits = (offset_amount * multiplier).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return [
        {
            "account": "Retained Earnings / Dividends Declared",
            "debit": f"${offset_amount:,.2f}",
            "credit": "$0.00",
            "description": f"Dividend declared to {borrower_name} to satisfy Div 7A MYR",
        },
        {
            "account": f"Division 7A Loan Receivable — {borrower_name}",
            "debit": "$0.00",
            "credit": f"${offset_amount:,.2f}",
            "description": "Credit loan account to satisfy MYR offset under s 109E",
        },
        {
            "account": "Franking Account (FAB)",
            "debit": f"${franking_credits:,.2f}",
            "credit": "$0.00",
            "description": "Franking debit on franked dividend offset (s 205-30 Item 1)",
        },
    ]
