"""
Payday Super 2026 Clearing House Latency Simulator & SGC Exposure Engine.
Models the 7 business day statutory window from payday (commencing 1 July 2026)
and evaluates Superannuation Guarantee Charge (SGC) liabilities under SGAA 1992.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import List, Optional


class ClearingHouseType(str, Enum):
    SBSCH = "SBSCH"                  # Small Business Superannuation Clearing House (3-7 days)
    COMMERCIAL = "COMMERCIAL"        # Modern Commercial Clearing House (1-3 days)
    DIRECT_PAYMENT = "DIRECT"        # Direct SuperStream Gateway (< 1 day)


@dataclass(frozen=True)
class PaydaySuperSimulationResult:
    pay_date: date
    statutory_due_date: date
    clearing_house_submission_date: date
    estimated_fund_receipt_date: date
    is_compliant: bool
    business_days_taken: int
    sg_contribution_amount: Decimal
    potential_sgc_shortfall: Decimal
    nominal_interest_charge: Decimal
    admin_fee_charge: Decimal
    total_sgc_exposure: Decimal
    risk_assessment: str


def add_business_days(start_date: date, num_days: int) -> date:
    """Add business days excluding weekends (Sat/Sun)."""
    current = start_date
    added = 0
    while added < num_days:
        current += timedelta(days=1)
        if current.weekday() < 5:  # Monday to Friday
            added += 1
    return current


def count_business_days(start_date: date, end_date: date) -> int:
    """Count business days between two dates."""
    if end_date <= start_date:
        return 0
    current = start_date
    count = 0
    while current < end_date:
        current += timedelta(days=1)
        if current.weekday() < 5:
            count += 1
    return count


def simulate_payday_super(
    pay_date: date,
    submission_date: date,
    sg_contribution: Decimal,
    total_salary_wages: Optional[Decimal] = None,
    clearing_house_type: ClearingHouseType = ClearingHouseType.COMMERCIAL,
    days_in_quarter_prior: int = 45,
    num_employees: int = 1,
) -> PaydaySuperSimulationResult:
    """
    Simulate Payday Super 2026 compliance window (7 business days from payday).
    Under Payday Super, contributions must be RECEIVED by the super fund by Day 7.
    """
    # 7 business day statutory window from pay_date
    statutory_due_date = add_business_days(pay_date, 7)

    # Clearing house typical latency
    latency_days = {
        ClearingHouseType.SBSCH: 5,
        ClearingHouseType.COMMERCIAL: 2,
        ClearingHouseType.DIRECT_PAYMENT: 1,
    }[clearing_house_type]

    estimated_receipt_date = add_business_days(submission_date, latency_days)
    business_days_from_pay = count_business_days(pay_date, estimated_receipt_date)
    is_compliant = estimated_receipt_date <= statutory_due_date

    if is_compliant:
        return PaydaySuperSimulationResult(
            pay_date=pay_date,
            statutory_due_date=statutory_due_date,
            clearing_house_submission_date=submission_date,
            estimated_fund_receipt_date=estimated_receipt_date,
            is_compliant=True,
            business_days_taken=business_days_from_pay,
            sg_contribution_amount=sg_contribution,
            potential_sgc_shortfall=Decimal("0.00"),
            nominal_interest_charge=Decimal("0.00"),
            admin_fee_charge=Decimal("0.00"),
            total_sgc_exposure=Decimal("0.00"),
            risk_assessment="COMPLIANT: Estimated fund receipt is within the 7 business day statutory window.",
        )

    # If late, compute SGC exposure under SGAA 1992
    # Shortfall is calculated on salary and wages (not just OTE)
    base_for_shortfall = total_salary_wages if total_salary_wages is not None else (sg_contribution / Decimal("0.115"))
    shortfall = (base_for_shortfall * Decimal("0.115")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Nominal interest: 10% p.a. from start of quarter to SGC lodgment date (est. 60 days)
    nominal_interest = (shortfall * Decimal("0.10") * Decimal(days_in_quarter_prior + 30) / Decimal("365")).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    admin_fee = Decimal(num_employees * 20)
    total_exposure = shortfall + nominal_interest + admin_fee

    risk_msg = (
        f"LATE / NON-COMPLIANT: Fund receives payment {business_days_from_pay} business days after payday "
        f"(due {statutory_due_date.isoformat()}, est. received {estimated_receipt_date.isoformat()}). "
        f"SG Charge liability triggered: ${total_exposure:,.2f}."
    )

    return PaydaySuperSimulationResult(
        pay_date=pay_date,
        statutory_due_date=statutory_due_date,
        clearing_house_submission_date=submission_date,
        estimated_fund_receipt_date=estimated_receipt_date,
        is_compliant=False,
        business_days_taken=business_days_from_pay,
        sg_contribution_amount=sg_contribution,
        potential_sgc_shortfall=shortfall,
        nominal_interest_charge=nominal_interest,
        admin_fee_charge=admin_fee,
        total_sgc_exposure=total_exposure,
        risk_assessment=risk_msg,
    )