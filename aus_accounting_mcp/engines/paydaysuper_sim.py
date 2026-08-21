"""
Payday Super 2026 national usual-period and clearing-house timing estimator.

Models the seven-business-day usual period from payday (commencing 1 July
2026) and estimates clearing-house receipt timing. It does not collect actual
fund receipt, eligibility, allocation or assessment facts, and therefore never
assesses legal compliance or Superannuation Guarantee Charge (SGC) liability.

Calendar and rate provenance (reviewed 21 August 2026):

* SGAA 1992 compilation 78, sections 6(1) and 17A(2):
  https://www.legislation.gov.au/C2004A04402/2026-07-01
* ATO national business-day guidance:
  https://www.ato.gov.au/tax-and-super-professionals/for-superannuation-professionals/super-funds-newsroom/business-days-decoded-why-it-matters-for-your-fund
* Official jurisdiction holiday publications:
  https://www.act.gov.au/living-in-the-act/public-holidays-school-terms-and-daylight-saving
  https://www.nsw.gov.au/about-nsw/public-holidays
  https://nt.gov.au/nt-public-holidays
  https://www.qld.gov.au/recreation/travel/holidays/public
  https://safework.sa.gov.au/resources/public-holidays
  https://worksafe.tas.gov.au/topics/laws-and-compliance/public-holidays
  https://business.vic.gov.au/business-information/public-holidays/victorian-public-holidays-2026
  https://www.wa.gov.au/service/employment/workplace-arrangements/public-holidays-western-australia

SGAA 1992 s 6(1) supplies one national calendar: a public holiday applying to
the whole of any State, the ACT or the NT is excluded nationally. Regional and
part-day holidays are business days for this definition.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from enum import Enum

_CALENDAR_VERIFIED_FROM = date(2026, 1, 1)
_CALENDAR_VERIFIED_UNTIL = date(2026, 12, 31)
_PAYDAY_SUPER_COMMENCEMENT = date(2026, 7, 1)

# At least one jurisdiction observes each date throughout that jurisdiction.
# Names are retained to keep the bundled statutory facts reviewable.
_WHOLE_OF_JURISDICTION_HOLIDAYS_2026 = {
    date(2026, 1, 1): "New Year's Day",
    date(2026, 1, 26): "Australia Day",
    date(2026, 3, 2): "Labour Day (WA)",
    date(2026, 3, 9): "Adelaide Cup Day; Canberra Day; Eight Hours Day; Labour Day",
    date(2026, 4, 3): "Good Friday",
    date(2026, 4, 4): "Easter Saturday",
    date(2026, 4, 5): "Easter Sunday",
    date(2026, 4, 6): "Easter Monday",
    date(2026, 4, 25): "ANZAC Day",
    date(2026, 4, 27): "ANZAC Day (observed)",
    date(2026, 5, 4): "Labour Day; May Day",
    date(2026, 6, 1): "Reconciliation Day; Western Australia Day",
    date(2026, 6, 8): "King's Birthday",
    date(2026, 8, 3): "Picnic Day (NT)",
    date(2026, 9, 25): "Friday before the AFL Grand Final (VIC)",
    date(2026, 10, 5): "King's Birthday; Labour Day",
    date(2026, 12, 25): "Christmas Day",
    date(2026, 12, 26): "Boxing Day; Proclamation Day",
    date(2026, 12, 28): "Boxing Day; Proclamation Day (observed)",
}

_SG_CHARGE_RATE_2026 = Decimal("0.12")
_COMPLIANCE_WARNING = (
    "Timing estimate only. Actual fund receipt, contribution eligibility and "
    "allocation, assessment and other statutory facts are not collected; no "
    "compliance or SGC conclusion is made."
)


class ClearingHouseType(str, Enum):
    SBSCH = "SBSCH"                  # Closed permanently on 1 July 2026
    COMMERCIAL = "COMMERCIAL"        # Modern Commercial Clearing House (1-3 days)
    DIRECT = "DIRECT"                # Direct SuperStream Gateway (< 1 day)


@dataclass(frozen=True)
class PaydaySuperSimulationResult:
    pay_date: date
    usual_period_end_date: date
    clearing_house_submission_date: date
    estimated_fund_receipt_date: date
    estimated_receipt_within_usual_period: bool
    business_days_taken: int
    sg_contribution_amount: Decimal
    compliance_status: str
    compliance_warning: str


def _is_business_day(day: date) -> bool:
    if not _CALENDAR_VERIFIED_FROM <= day <= _CALENDAR_VERIFIED_UNTIL:
        raise ValueError(
            f"{day.isoformat()} is outside the verified 2026 calendar "
            f"({_CALENDAR_VERIFIED_FROM.isoformat()} to "
            f"{_CALENDAR_VERIFIED_UNTIL.isoformat()})"
        )
    return day.weekday() < 5 and day not in _WHOLE_OF_JURISDICTION_HOLIDAYS_2026


def add_business_days(start_date: date, num_days: int) -> date:
    """Add days using the national SGAA 1992 s 6(1) calendar."""
    _is_business_day(start_date)
    current = start_date
    added = 0
    while added < num_days:
        current += timedelta(days=1)
        if _is_business_day(current):
            added += 1
    return current


def count_business_days(start_date: date, end_date: date) -> int:
    """Count days using the national SGAA 1992 s 6(1) calendar."""
    _is_business_day(start_date)
    _is_business_day(end_date)
    if end_date <= start_date:
        return 0
    current = start_date
    count = 0
    while current < end_date:
        current += timedelta(days=1)
        if _is_business_day(current):
            count += 1
    return count


def calculate_individual_sg_amount_2026(qualifying_earnings: Decimal) -> Decimal:
    """Return the SGAA 1992 s 17A amount before contributions or assessment."""
    if qualifying_earnings < 0:
        raise ValueError("qualifying earnings must not be negative")
    return qualifying_earnings * _SG_CHARGE_RATE_2026


def simulate_payday_super(
    pay_date: date,
    submission_date: date,
    sg_contribution: Decimal,
    clearing_house_type: ClearingHouseType = ClearingHouseType.COMMERCIAL,
) -> PaydaySuperSimulationResult:
    """
    Estimate receipt timing against the 2026 seven-business-day usual period.

    The result always reports compliance as ``NOT_ASSESSED``. An estimated
    receipt cannot establish actual receipt or allocation and is not an SGC
    calculation.
    """
    if pay_date < _PAYDAY_SUPER_COMMENCEMENT:
        raise ValueError("Payday Super commences on 1 July 2026")
    if submission_date < pay_date:
        raise ValueError("submission date must not be before pay date")
    if sg_contribution < 0:
        raise ValueError("sg_contribution must not be negative")
    if clearing_house_type is ClearingHouseType.SBSCH:
        raise ValueError(
            "SBSCH closed on 1 July 2026 and is unavailable for Payday Super"
        )

    usual_period_end_date = add_business_days(pay_date, 7)

    # Clearing house typical latency
    latency_days = {
        ClearingHouseType.SBSCH: 5,
        ClearingHouseType.COMMERCIAL: 2,
        ClearingHouseType.DIRECT: 1,
    }[clearing_house_type]

    estimated_receipt_date = add_business_days(submission_date, latency_days)
    business_days_from_pay = count_business_days(pay_date, estimated_receipt_date)
    estimated_within_usual_period = (
        estimated_receipt_date <= usual_period_end_date
    )

    return PaydaySuperSimulationResult(
        pay_date=pay_date,
        usual_period_end_date=usual_period_end_date,
        clearing_house_submission_date=submission_date,
        estimated_fund_receipt_date=estimated_receipt_date,
        estimated_receipt_within_usual_period=estimated_within_usual_period,
        business_days_taken=business_days_from_pay,
        sg_contribution_amount=sg_contribution,
        compliance_status="NOT_ASSESSED",
        compliance_warning=_COMPLIANCE_WARNING,
    )
