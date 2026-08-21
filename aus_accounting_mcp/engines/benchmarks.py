"""
ATO Small Business Benchmark lookup and variance analysis engine.
"""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional


@dataclass(frozen=True)
class BenchmarkRatio:
    metric_name: str
    low_percent: Decimal
    median_percent: Decimal
    high_percent: Decimal


# Curated representative ATO Small Business Benchmarks
INDUSTRY_BENCHMARKS: Dict[str, Dict[str, BenchmarkRatio]] = {
    "cafes_and_restaurants": {
        "cost_of_sales": BenchmarkRatio("Cost of Sales / Turnover", Decimal("28.0"), Decimal("32.0"), Decimal("37.0")),
        "labour": BenchmarkRatio("Labour / Turnover", Decimal("25.0"), Decimal("29.0"), Decimal("34.0")),
        "rent": BenchmarkRatio("Rent / Turnover", Decimal("7.0"), Decimal("10.0"), Decimal("14.0")),
        "motor_vehicle": BenchmarkRatio("Motor Vehicle / Turnover", Decimal("0.5"), Decimal("1.0"), Decimal("2.0")),
    },
    "residential_building_construction": {
        "cost_of_sales": BenchmarkRatio("Cost of Sales / Turnover", Decimal("45.0"), Decimal("55.0"), Decimal("66.0")),
        "labour": BenchmarkRatio("Labour / Turnover", Decimal("12.0"), Decimal("18.0"), Decimal("25.0")),
        "rent": BenchmarkRatio("Rent / Turnover", Decimal("0.5"), Decimal("1.5"), Decimal("3.0")),
        "motor_vehicle": BenchmarkRatio("Motor Vehicle / Turnover", Decimal("2.0"), Decimal("3.5"), Decimal("5.5")),
    },
    "hairdressing_and_beauty": {
        "cost_of_sales": BenchmarkRatio("Cost of Sales / Turnover", Decimal("8.0"), Decimal("12.0"), Decimal("16.0")),
        "labour": BenchmarkRatio("Labour / Turnover", Decimal("28.0"), Decimal("35.0"), Decimal("42.0")),
        "rent": BenchmarkRatio("Rent / Turnover", Decimal("10.0"), Decimal("15.0"), Decimal("20.0")),
        "motor_vehicle": BenchmarkRatio("Motor Vehicle / Turnover", Decimal("0.5"), Decimal("1.5"), Decimal("3.0")),
    },
    "plumbing_services": {
        "cost_of_sales": BenchmarkRatio("Cost of Sales / Turnover", Decimal("25.0"), Decimal("33.0"), Decimal("42.0")),
        "labour": BenchmarkRatio("Labour / Turnover", Decimal("18.0"), Decimal("26.0"), Decimal("34.0")),
        "rent": BenchmarkRatio("Rent / Turnover", Decimal("1.0"), Decimal("2.5"), Decimal("4.5")),
        "motor_vehicle": BenchmarkRatio("Motor Vehicle / Turnover", Decimal("3.0"), Decimal("5.0"), Decimal("7.5")),
    },
    "management_consultancy": {
        "cost_of_sales": BenchmarkRatio("Cost of Sales / Turnover", Decimal("5.0"), Decimal("10.0"), Decimal("18.0")),
        "labour": BenchmarkRatio("Labour / Turnover", Decimal("20.0"), Decimal("32.0"), Decimal("45.0")),
        "rent": BenchmarkRatio("Rent / Turnover", Decimal("3.0"), Decimal("6.0"), Decimal("10.0")),
        "motor_vehicle": BenchmarkRatio("Motor Vehicle / Turnover", Decimal("1.0"), Decimal("2.5"), Decimal("5.0")),
    },
}


@dataclass(frozen=True)
class MetricVariance:
    metric_name: str
    actual_amount: Decimal
    actual_percentage: Decimal
    benchmark_low: Decimal
    benchmark_median: Decimal
    benchmark_high: Decimal
    status: str  # "WITHIN_RANGE", "BELOW_BENCHMARK", "ABOVE_BENCHMARK"
    risk_level: str  # "LOW", "MEDIUM", "HIGH"


@dataclass(frozen=True)
class BenchmarkAnalysisResult:
    industry_key: str
    annual_turnover: Decimal
    metrics_evaluated: List[MetricVariance]
    overall_audit_risk: str


def analyze_ato_benchmarks(
    industry_key: str,
    annual_turnover: Decimal,
    cost_of_sales: Optional[Decimal] = None,
    labour_expenses: Optional[Decimal] = None,
    rent_expenses: Optional[Decimal] = None,
    motor_vehicle_expenses: Optional[Decimal] = None,
) -> BenchmarkAnalysisResult:
    """
    Evaluate business performance ratios against ATO small business benchmarks.
    """
    benchmarks = INDUSTRY_BENCHMARKS.get(industry_key.lower())
    if not benchmarks:
        raise ValueError(f"Industry '{industry_key}' not found in benchmark database. Available: {list(INDUSTRY_BENCHMARKS.keys())}")

    if annual_turnover <= Decimal("0.00"):
        raise ValueError("Turnover must be greater than zero.")

    user_inputs = {
        "cost_of_sales": cost_of_sales,
        "labour": labour_expenses,
        "rent": rent_expenses,
        "motor_vehicle": motor_vehicle_expenses,
    }

    evaluations: List[MetricVariance] = []
    high_risk_count = 0

    for key, bm in benchmarks.items():
        val = user_inputs.get(key)
        if val is None:
            continue

        pct = ((val / annual_turnover) * Decimal("100.00")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)

        if pct < bm.low_percent:
            status = "BELOW_BENCHMARK"
            # Low cost of sales or low labour can indicate unrecorded cash or audit trigger
            risk = "MEDIUM" if (bm.low_percent - pct) > Decimal("5.0") else "LOW"
        elif pct > bm.high_percent:
            status = "ABOVE_BENCHMARK"
            # High cost of sales or high vehicle expenses can trigger ATO expense review
            diff = pct - bm.high_percent
            if diff > Decimal("7.0"):
                risk = "HIGH"
                high_risk_count += 1
            else:
                risk = "MEDIUM"
        else:
            status = "WITHIN_RANGE"
            risk = "LOW"

        evaluations.append(
            MetricVariance(
                metric_name=bm.metric_name,
                actual_amount=val,
                actual_percentage=pct,
                benchmark_low=bm.low_percent,
                benchmark_median=bm.median_percent,
                benchmark_high=bm.high_percent,
                status=status,
                risk_level=risk,
            )
        )

    overall_risk = "HIGH" if high_risk_count > 0 else ("MEDIUM" if any(e.risk_level == "MEDIUM" for e in evaluations) else "LOW")

    return BenchmarkAnalysisResult(
        industry_key=industry_key,
        annual_turnover=annual_turnover,
        metrics_evaluated=evaluations,
        overall_audit_risk=overall_risk,
    )