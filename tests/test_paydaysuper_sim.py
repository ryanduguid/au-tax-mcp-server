from datetime import date
from decimal import Decimal

import pytest

from aus_accounting_mcp.engines.paydaysuper_sim import (
    ClearingHouseType,
    add_business_days,
    simulate_payday_super,
)


def test_nt_picnic_day_shifts_the_national_deadline():
    result = simulate_payday_super(
        pay_date=date(2026, 7, 24),
        submission_date=date(2026, 7, 24),
        sg_contribution=Decimal("1200.00"),
        clearing_house_type=ClearingHouseType.COMMERCIAL,
    )

    # Picnic Day applies to the whole NT, so SGAA 1992 s 6(1) excludes it
    # from the single national business-day calendar. Employer and employee
    # location do not alter this deadline.
    assert result.statutory_due_date == date(2026, 8, 5)


@pytest.mark.parametrize(
    ("start_date", "business_days", "expected"),
    [
        pytest.param(
            date(2026, 10, 30),
            2,
            date(2026, 11, 3),
            id="melbourne-cup-day",
        ),
        pytest.param(
            date(2026, 8, 10),
            2,
            date(2026, 8, 12),
            id="brisbane-show-day",
        ),
        pytest.param(
            date(2026, 12, 21),
            3,
            date(2026, 12, 24),
            id="christmas-eve-part-day-holiday",
        ),
    ],
)
def test_regional_and_part_day_holidays_remain_business_days(
    start_date: date,
    business_days: int,
    expected: date,
):
    assert add_business_days(start_date, business_days) == expected


def test_business_day_calculation_fails_beyond_the_verified_2026_horizon():
    with pytest.raises(ValueError, match="outside the verified 2026 calendar"):
        add_business_days(date(2026, 12, 31), 1)


def test_2026_shortfall_uses_the_twelve_percent_charge_rate():
    result = simulate_payday_super(
        pay_date=date(2026, 7, 7),
        submission_date=date(2026, 7, 20),
        sg_contribution=Decimal("0.00"),
        total_salary_wages=Decimal("10000.00"),
        clearing_house_type=ClearingHouseType.DIRECT_PAYMENT,
    )

    assert result.is_compliant is False
    assert result.potential_sgc_shortfall == Decimal("1200.00")
