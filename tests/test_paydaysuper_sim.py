from datetime import date
from decimal import Decimal

import pytest

from aus_accounting_mcp.engines import paydaysuper_sim as payday_super
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


def test_2026_individual_sg_amount_uses_the_twelve_percent_charge_rate():
    assert payday_super.calculate_individual_sg_amount_2026(
        Decimal("10000.00")
    ) == Decimal("1200.00")


def test_payday_super_rejects_pay_dates_before_commencement():
    with pytest.raises(ValueError, match="commences on 1 July 2026"):
        simulate_payday_super(
            pay_date=date(2026, 6, 30),
            submission_date=date(2026, 6, 30),
            sg_contribution=Decimal("1200.00"),
        )


def test_payday_super_rejects_the_closed_sbsch_route():
    with pytest.raises(ValueError, match="SBSCH closed on 1 July 2026"):
        simulate_payday_super(
            pay_date=date(2026, 7, 7),
            submission_date=date(2026, 7, 7),
            sg_contribution=Decimal("1200.00"),
            clearing_house_type=ClearingHouseType.SBSCH,
        )


def test_late_result_does_not_report_the_obsolete_quarterly_sgc_formula():
    with pytest.raises(
        ValueError, match="Post-1 July 2026 SGC exposure is not modelled"
    ):
        simulate_payday_super(
            pay_date=date(2026, 7, 7),
            submission_date=date(2026, 7, 20),
            sg_contribution=Decimal("1200.00"),
            total_salary_wages=Decimal("10000.00"),
            clearing_house_type=ClearingHouseType.DIRECT_PAYMENT,
        )
