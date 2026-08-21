from datetime import date
from decimal import Decimal

import pytest

from aus_accounting_mcp.engines import paydaysuper_sim as payday_super
from aus_accounting_mcp.engines.paydaysuper_sim import (
    ClearingHouseType,
    add_business_days,
    simulate_payday_super,
)

_NSW_HOLIDAYS = "https://www.nsw.gov.au/about-nsw/public-holidays"
_ACT_HOLIDAYS = (
    "https://www.act.gov.au/living-in-the-act/"
    "public-holidays-school-terms-and-daylight-saving"
)
_NT_HOLIDAYS = "https://nt.gov.au/nt-public-holidays"
_SA_HOLIDAYS = "https://safework.sa.gov.au/resources/public-holidays"
_VIC_HOLIDAYS = (
    "https://business.vic.gov.au/business-information/"
    "public-holidays/victorian-public-holidays-2026"
)
_WA_HOLIDAYS = (
    "https://www.wa.gov.au/service/employment/"
    "workplace-arrangements/public-holidays-western-australia"
)

# This is the complete 2026 union transcribed from the official jurisdiction
# publications above. Each row cites one jurisdiction that observes the date
# throughout that jurisdiction, which is sufficient for SGAA 1992 s 6(1).
_VERIFIED_NATIONAL_HOLIDAY_UNION_2026 = [
    (date(2026, 1, 1), "New Year's Day", _NSW_HOLIDAYS, "new-years-day"),
    (date(2026, 1, 26), "Australia Day", _NSW_HOLIDAYS, "australia-day"),
    (date(2026, 3, 2), "Labour Day (WA)", _WA_HOLIDAYS, "wa-labour-day"),
    (
        date(2026, 3, 9),
        "Adelaide Cup Day; Canberra Day; Eight Hours Day; Labour Day",
        _ACT_HOLIDAYS,
        "canberra-day-and-other-state-holidays",
    ),
    (date(2026, 4, 3), "Good Friday", _NSW_HOLIDAYS, "good-friday"),
    (date(2026, 4, 4), "Easter Saturday", _NSW_HOLIDAYS, "easter-saturday"),
    (date(2026, 4, 5), "Easter Sunday", _NSW_HOLIDAYS, "easter-sunday"),
    (date(2026, 4, 6), "Easter Monday", _NSW_HOLIDAYS, "easter-monday"),
    (date(2026, 4, 25), "ANZAC Day", _NSW_HOLIDAYS, "anzac-day"),
    (
        date(2026, 4, 27),
        "ANZAC Day (observed)",
        _ACT_HOLIDAYS,
        "anzac-day-observed",
    ),
    (date(2026, 5, 4), "Labour Day; May Day", _NT_HOLIDAYS, "may-day"),
    (
        date(2026, 6, 1),
        "Reconciliation Day; Western Australia Day",
        _ACT_HOLIDAYS,
        "reconciliation-day-and-wa-day",
    ),
    (date(2026, 6, 8), "King's Birthday", _NSW_HOLIDAYS, "kings-birthday"),
    (date(2026, 8, 3), "Picnic Day (NT)", _NT_HOLIDAYS, "nt-picnic-day"),
    (
        date(2026, 9, 25),
        "Friday before the AFL Grand Final (VIC)",
        _VIC_HOLIDAYS,
        "victoria-afl-grand-final-friday",
    ),
    (
        date(2026, 10, 5),
        "King's Birthday; Labour Day",
        _NSW_HOLIDAYS,
        "october-state-holidays",
    ),
    (date(2026, 12, 25), "Christmas Day", _NSW_HOLIDAYS, "christmas-day"),
    (
        date(2026, 12, 26),
        "Boxing Day; Proclamation Day",
        _SA_HOLIDAYS,
        "boxing-and-proclamation-day",
    ),
    (
        date(2026, 12, 28),
        "Boxing Day; Proclamation Day (observed)",
        _SA_HOLIDAYS,
        "boxing-and-proclamation-day-observed",
    ),
]


@pytest.mark.parametrize(
    ("holiday", "expected_name", "source_url"),
    [row[:3] for row in _VERIFIED_NATIONAL_HOLIDAY_UNION_2026],
    ids=[row[3] for row in _VERIFIED_NATIONAL_HOLIDAY_UNION_2026],
)
def test_complete_verified_2026_holiday_union_is_excluded_nationally(
    holiday: date,
    expected_name: str,
    source_url: str,
):
    expected_dates = {
        row[0] for row in _VERIFIED_NATIONAL_HOLIDAY_UNION_2026
    }

    assert set(payday_super._WHOLE_OF_JURISDICTION_HOLIDAYS_2026) == expected_dates
    assert payday_super._WHOLE_OF_JURISDICTION_HOLIDAYS_2026[holiday] == expected_name
    assert source_url in payday_super.__doc__
    assert payday_super._is_business_day(holiday) is False


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
    assert result.usual_period_end_date == date(2026, 8, 5)
    assert result.estimated_receipt_within_usual_period is True
    assert result.compliance_status == "NOT_ASSESSED"


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


def test_late_estimate_is_returned_without_a_legal_compliance_conclusion():
    result = simulate_payday_super(
        pay_date=date(2026, 7, 7),
        submission_date=date(2026, 7, 20),
        sg_contribution=Decimal("1200.00"),
        clearing_house_type=ClearingHouseType.DIRECT,
    )

    assert result.estimated_receipt_within_usual_period is False
    assert result.compliance_status == "NOT_ASSESSED"
    assert "actual fund receipt" in result.compliance_warning.lower()
    assert not hasattr(result, "is_compliant")
    assert not hasattr(result, "total_sgc_exposure")


def test_zero_contribution_is_timing_only_and_never_reported_as_compliant():
    result = simulate_payday_super(
        pay_date=date(2026, 7, 7),
        submission_date=date(2026, 7, 7),
        sg_contribution=Decimal("0.00"),
    )

    assert result.estimated_receipt_within_usual_period is True
    assert result.compliance_status == "NOT_ASSESSED"
    assert "no compliance or SGC conclusion" in result.compliance_warning


def test_payday_super_rejects_a_negative_contribution():
    with pytest.raises(ValueError, match="sg_contribution must not be negative"):
        simulate_payday_super(
            pay_date=date(2026, 7, 7),
            submission_date=date(2026, 7, 7),
            sg_contribution=Decimal("-0.01"),
        )


def test_payday_super_rejects_submission_before_pay_date():
    with pytest.raises(
        ValueError, match="submission date must not be before pay date"
    ):
        simulate_payday_super(
            pay_date=date(2026, 7, 7),
            submission_date=date(2026, 7, 6),
            sg_contribution=Decimal("1200.00"),
        )
