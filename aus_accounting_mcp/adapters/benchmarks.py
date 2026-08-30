"""Adapter over ato-benchmark-compare.

No ATO ratios are hardcoded here. Figures are bucket totals; the engine
applies QC 37143 turnover and labour rules and the shipped dataset.
Omitted buckets are not treated as evidenced zeros. The turnover rule reads
other_income to choose the ratio denominator, so no ratio is reported without it.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from atobenchmark import __version__ as BENCHMARK_VERSION
from atobenchmark.dataset import DatasetError, load
from atobenchmark.mapping import BUCKETS
from atobenchmark.money import money
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
    # labour figure and an omitted one cannot move the ratio. W1 replaces that
    # rebuilt label, which leaves the deduction without its matching addition,
    # and there an omitted bucket does reach the engine as a definite zero.
    # Requiring it on both paths would decline a ratio the engine computes
    # correctly without it.
    labour_evidenced = (
        ("salary_wages" in supplied or w1_amount is not None)
        and all(name in supplied for name in ("contractor_commission", "cost_of_sales_labour"))
        and (w1_amount is None or "associated_persons" in supplied)
    )

    # Every ratio is a percentage of turnover, and the ATO picks that denominator
    # by reading both income buckets: it is the sales of goods and services
    # figure unless that is zero or less than half of total business income, in
    # which case total business income is used instead. An omitted other_income
    # reaches the engine as zero, which makes total business income equal sales
    # and puts the fallback permanently out of reach, so the engine can only ever
    # select sales and nobody has established that sales is the right base. The
    # denominator, the turnover band it falls in and every ratio computed on it
    # therefore stay unevidenced until the bucket is supplied. An explicit 0 is
    # evidence and leaves all of them definite.
    denominator_evidenced = "other_income" in supplied

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
        if evidenced and denominator_evidenced:
            ratios.append(row)
            continue
        ratios.append(
            {
                "ratio": row["ratio"],
                "label": row["label"],
                "value": None,
                "percent": None,
                # The published range is the one for the selected turnover band,
                # so it is only as established as the denominator that chose it.
                "benchmark_min": row["benchmark_min"] if denominator_evidenced else None,
                "benchmark_max": row["benchmark_max"] if denominator_evidenced else None,
                "status": "not_supplied",
                "is_key_ratio": row["is_key_ratio"],
            }
        )

    # The engine needs a figure for every bucket, so an omitted bucket reaches it
    # as zero. That zero is not evidence, so neither the bucket total nor any
    # figure derived from it is published as a definite amount. "w1" rides along
    # in omitted but is an activity statement label, not a bucket.
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
    if not denominator_evidenced:
        payload["figures"]["total_business_income"] = None
        payload["figures"]["other_business_income"] = None
        # The denominator, the ATO rule that selected it and the band it falls
        # in are all downstream of the same unsupplied bucket. The sales figure
        # the operator did supply stays readable at figures and bucket_totals.
        payload["turnover"] = None
        payload["turnover_basis"] = None
        payload["turnover_band"] = None
    if "cost_of_sales" not in supplied:
        payload["figures"]["cost_of_sales_for_ratio"] = None

    notes = list(payload["notes"])
    if not denominator_evidenced:
        # The engine's own notes quote the turnover it was handed, and one of
        # them concludes from that figure that the ATO benchmarks do not apply
        # at all. That is the same unevidenced denominator carried in prose, and
        # it can be flatly wrong: the business may well fall in a published band
        # once the missing income is counted. So a note quoting the amount is
        # withheld rather than published beside the fields nulled above.
        # Matching the rendered figure catches every such note without depending
        # on the engine's wording.
        quoted_turnover = money(figures.turnover)
        notes = [note for note in notes if quoted_turnover not in note]
    if omitted:
        notes.append(
            "These buckets were omitted, not evidenced as zero, so their ratios "
            f"are not_supplied: {', '.join(omitted)}."
        )
    if not denominator_evidenced:
        notes.append(
            "other_income was not supplied, so no ratio is reported. The ATO takes "
            "turnover from sales of goods and services unless that is zero or less "
            "than half of total business income, in which case total business "
            "income is used instead, so an unsupplied other_income leaves the "
            "denominator, the turnover band and every ratio computed on them "
            "unestablished. Any note that quoted that turnover has been withheld "
            "for the same reason. Supply other_income to compare; use 0 only "
            "where the operator established there is none."
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
