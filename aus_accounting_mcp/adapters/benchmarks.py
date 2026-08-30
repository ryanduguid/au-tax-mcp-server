"""Adapter over ato-benchmark-compare.

No ATO ratios are hardcoded here. Figures are bucket totals; the engine
applies QC 37143 turnover and labour rules and the shipped dataset.
Omitted buckets are not treated as evidenced zeros.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from atobenchmark import __version__ as BENCHMARK_VERSION
from atobenchmark.dataset import DatasetError, load
from atobenchmark.mapping import BUCKETS
from atobenchmark.ratios import RatioError, compute
from atobenchmark.report import DISCLAIMER, compare, to_dict

from aus_accounting_mcp.money import parse_amount, parse_optional_amount

EXPENSE_FIELDS = (
    "cost_of_sales",
    "cost_of_sales_labour",
    "salary_wages",
    "contractor_commission",
    "associated_persons",
    "rent",
    "motor_vehicle",
    "other_expense",
)

RATIO_SOURCES: dict[str, tuple[str, ...]] = {
    "cost_of_sales_to_turnover": ("cost_of_sales",),
    "rent_to_turnover": ("rent",),
    "motor_vehicle_to_turnover": ("motor_vehicle",),
    "labour_to_turnover": (
        "salary_wages",
        "contractor_commission",
        "cost_of_sales_labour",
        "w1",
    ),
    "total_expenses_to_turnover": EXPENSE_FIELDS,
}


def list_industries(search: str | None = None, year: str | None = None) -> dict[str, Any]:
    data = load(year)
    matches = data.search(search) if search else list(data.business_types)
    return {
        "ok": True,
        "engine": "ato-benchmark-compare",
        "engine_version": BENCHMARK_VERSION,
        "benchmark_year": data.year,
        "count": len(matches),
        "total_business_types": len(data.business_types),
        "industries": [{"name": bt.name, "key_ratio": bt.key_ratio} for bt in matches],
        "source": dict(data.source),
    }


def compare_figures(
    *,
    industry: str,
    turnover: str,
    year: str | None = None,
    other_income: str | None = None,
    cost_of_sales: str | None = None,
    cost_of_sales_labour: str | None = None,
    salary_wages: str | None = None,
    contractor_commission: str | None = None,
    associated_persons: str | None = None,
    rent: str | None = None,
    motor_vehicle: str | None = None,
    other_expense: str | None = None,
    w1: str | None = None,
) -> dict[str, Any]:
    """Compare operator-supplied bucket totals against the ATO dataset."""
    supplied: dict[str, Decimal] = {"turnover": parse_amount(turnover, "turnover")}
    optional = {
        "other_income": other_income,
        "cost_of_sales": cost_of_sales,
        "cost_of_sales_labour": cost_of_sales_labour,
        "salary_wages": salary_wages,
        "contractor_commission": contractor_commission,
        "associated_persons": associated_persons,
        "rent": rent,
        "motor_vehicle": motor_vehicle,
        "other_expense": other_expense,
    }
    for field, raw in optional.items():
        amount = parse_optional_amount(raw, field)
        if amount is not None:
            supplied[field] = amount
    w1_amount = parse_optional_amount(w1, "w1")

    if not any(field in supplied for field in EXPENSE_FIELDS):
        raise ValueError(
            "no expense figures were supplied, so no ATO ratio can be compared. "
            "Pass at least one expense bucket as a decimal string; use 0 only when "
            "the operator established that the amount is zero."
        )

    totals = {name: Decimal("0") for name in BUCKETS}
    totals.update(supplied)

    try:
        data = load(year)
        business_type = data.get(industry)
        figures = compute(totals, w1_amount)
        comparison = compare(data, business_type, figures)
    except (DatasetError, RatioError) as exc:
        raise ValueError(str(exc)) from exc

    payload = to_dict(comparison)
    omitted = [name for name in optional if name not in supplied]
    if w1_amount is None:
        omitted.append("w1")
    expense_complete = all(name in supplied for name in EXPENSE_FIELDS)

    # Labour sums several buckets, and an omitted bucket is not evidenced as
    # zero, so a partial labour picture must not present as a definite ratio.
    #
    # associated_persons is required only when W1 is supplied, and that
    # asymmetry is deliberate rather than an oversight. The engine rebuilds the
    # return's salary and wages label by adding associates back, then deducts
    # them once at the end, so on the salary path the bucket cancels out of the
    # labour figure and an omitted one cannot move the ratio. When W1 is greater
    # it replaces that rebuilt label, which leaves the deduction without its
    # matching addition, and there an omitted bucket does reach the engine as a
    # definite zero. Requiring it on both paths would decline a ratio the engine
    # computes correctly without it.
    #
    # W1 does not stand in for salary_wages either, which is why the first clause
    # is an "and" rather than an "or". The engine takes the greater of W1 and the
    # rebuilt label, so with salary_wages omitted nobody can say which side wins,
    # and the labour the engine returns is only a lower bound.
    labour_evidenced = (
        "salary_wages" in supplied
        and all(name in supplied for name in ("contractor_commission", "cost_of_sales_labour"))
        and (w1_amount is None or "associated_persons" in supplied)
    )

    # Every ratio divides by turnover, and the ATO rule picks that denominator
    # from two candidates: sales, or total business income, which is sales plus
    # other income. The engine switches to total business income once other
    # income exceeds sales, so an omitted other_income does not merely leave one
    # numerator unknown, it leaves the denominator under every ratio unknown.
    #
    # Omitting it reaches the engine as zero, which picks sales, the smallest
    # denominator the rule can select. Every ratio built on it is therefore an
    # upper bound rather than an amount. Publishing those as definite states a
    # verdict the figures do not support, so none of them is published without
    # the income figure.
    income_evidenced = "other_income" in supplied

    ratios = []
    for row in payload["ratios"]:
        if row["ratio"] == "total_expenses_to_turnover":
            evidenced = all(name in supplied for name in EXPENSE_FIELDS)
        elif row["ratio"] == "labour_to_turnover":
            evidenced = labour_evidenced
        else:
            sources = RATIO_SOURCES.get(row["ratio"], ())
            evidenced = any(
                (source == "w1" and w1_amount is not None) or source in supplied
                for source in sources
            )
        if evidenced and income_evidenced:
            ratios.append(row)
            continue
        ratios.append(
            {
                "ratio": row["ratio"],
                "label": row["label"],
                "value": None,
                "percent": None,
                "benchmark_min": row["benchmark_min"],
                "benchmark_max": row["benchmark_max"],
                "status": "not_supplied",
                "is_key_ratio": row["is_key_ratio"],
            }
        )

    # The engine needs a figure for every bucket, so an omitted bucket reaches it
    # as zero. That zero is not evidence, so the bucket total and each figure
    # withheld below are reported as unknown rather than as definite amounts.
    # "w1" rides along in omitted but is an activity statement label, not a
    # bucket.
    #
    # sales_of_goods_and_services stays as it is. The caller supplies it, so it
    # is the one income figure this payload can state.
    for name in omitted:
        if name in payload["bucket_totals"]:
            payload["bucket_totals"][name] = None
    if not expense_complete:
        payload["figures"]["total_expenses"] = None
        payload["figures"]["total_expenses_for_ratio"] = None
    if not labour_evidenced:
        payload["figures"]["labour"] = None
    if "associated_persons" not in supplied:
        payload["figures"]["payments_to_associated_persons"] = None
    if "other_income" not in supplied:
        payload["figures"]["total_business_income"] = None
        payload["figures"]["other_business_income"] = None
    if "cost_of_sales" not in supplied:
        payload["figures"]["cost_of_sales_for_ratio"] = None

    notes = list(payload["notes"])
    if omitted:
        notes.append(
            "These buckets were omitted, not evidenced as zero, so their ratios "
            f"are not_supplied: {', '.join(omitted)}."
        )
    if not income_evidenced:
        notes.append(
            "other_business_income was omitted. The ATO rule divides by sales, or "
            "by total business income once other income exceeds sales, so every "
            "ratio is not_supplied until that figure is established. Pass 0 only "
            "when the operator established the business had no other income."
        )

    payload.update(
        {
            "ok": True,
            "engine": "ato-benchmark-compare",
            "engine_version": BENCHMARK_VERSION,
            "disclaimer": DISCLAIMER,
            "ratios": ratios,
            "notes": notes,
            "supplied_buckets": sorted(supplied),
            "omitted_buckets": omitted,
            "complete_buckets": expense_complete,
            "unreviewed_accounts": None,
        }
    )
    return payload
