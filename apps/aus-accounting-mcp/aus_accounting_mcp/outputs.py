"""MCP result contracts; calculations and provenance remain owned by the engines.

Typed dictionaries preserve the existing JSON objects. Optional keys describe
summary/full and CTR/BAS variants without inserting defaults. Extra fields are
retained so engine audit information is never discarded during serialization.
"""

from typing import Annotated, Any, Literal

from pydantic import ConfigDict, Field, with_config
from typing_extensions import NotRequired, TypedDict


DecimalText = Annotated[str, Field(description="Engine decimal string; retain its precision.")]
MaybeDecimal = Annotated[
    str | None,
    Field(description="Engine decimal string, or null when unavailable; null is not zero."),
]
DateText = Annotated[str, Field(description="Date in YYYY-MM-DD form.")]
YearText = Annotated[str, Field(description="Income or dataset year in YYYY-YY form.")]
Caveats = Annotated[
    list[str], Field(description="Limitations to retain when presenting the result.")
]
Reasons = Annotated[list[str], Field(description="Engine reasons for the reported verdict.")]
Trace = Annotated[
    list[str], Field(description="Engine statutory citations and audit trace; full only.")
]
Provenance = Annotated[
    dict[str, Any],
    Field(description="Unmodified engine source metadata and review provenance."),
]


@with_config(ConfigDict(extra="allow", strict=True))
class ResultObject(TypedDict):
    """Preserve additional engine fields and reject coercion of declared values."""


class EngineResult(ResultObject):
    ok: Annotated[
        Literal[True],
        Field(description="The review ran; this does not mean compliance or a known verdict."),
    ]
    engine: Annotated[str, Field(description="Delegated distribution that produced this result.")]
    engine_version: Annotated[str, Field(description="Installed version of that engine.")]


class Industry(ResultObject):
    name: Annotated[str, Field(description="Business-type name accepted by get_ato_benchmarks.")]
    key_ratio: Annotated[str, Field(description="ATO key-ratio identifier for this industry.")]


class IndustryList(EngineResult):
    benchmark_year: YearText
    count: Annotated[int, Field(description="Number of industries matching the search.")]
    total_business_types: Annotated[
        int, Field(description="Total industries in the selected dataset.")
    ]
    industries: Annotated[
        list[Industry], Field(description="Matching industries; empty if no match.")
    ]
    source: Provenance


class BenchmarkRatio(ResultObject):
    ratio: Annotated[str, Field(description="Ratio identifier.")]
    label: Annotated[str, Field(description="Human-readable ratio name.")]
    value: MaybeDecimal
    percent: Annotated[
        str | None, Field(description="Formatted percentage, or null if unavailable.")
    ]
    benchmark_min: MaybeDecimal
    benchmark_max: MaybeDecimal
    status: Annotated[
        str,
        Field(
            description="Engine comparison status; not_supplied means facts do not establish the ratio."
        ),
    ]
    is_key_ratio: Annotated[bool, Field(description="Whether this is the selected ATO key ratio.")]


class BenchmarkComparison(EngineResult):
    benchmark_year: YearText
    business_type: Annotated[str, Field(description="Selected ATO industry name.")]
    key_ratio: Annotated[str, Field(description="Selected ATO key-ratio identifier.")]
    turnover: MaybeDecimal
    turnover_basis: Annotated[
        str | None, Field(description="Engine denominator basis; null if unestablished.")
    ]
    turnover_band: Annotated[
        dict[str, str] | None,
        Field(description="Selected dataset band and label, or null if unavailable."),
    ]
    figures: Annotated[
        dict[str, MaybeDecimal], Field(description="Engine figures; unevidenced totals are null.")
    ]
    bucket_totals: Annotated[
        dict[str, MaybeDecimal], Field(description="Bucket amounts; omitted inputs remain null.")
    ]
    ratios: Annotated[
        list[BenchmarkRatio], Field(description="Comparisons, including unevidenced ratios.")
    ]
    unreviewed_accounts: Annotated[
        None, Field(description="Unknown: this tool receives totals, not an account ledger.")
    ]
    notes: Annotated[list[str], Field(description="Dataset and missing-fact explanations.")]
    checks_to_make: Annotated[
        list[str], Field(description="Suggested human checks, not findings of wrongdoing.")
    ]
    source: Provenance
    disclaimer: Annotated[
        str, Field(description="Engine limitations on using benchmark comparisons.")
    ]
    supplied_buckets: Annotated[
        list[str], Field(description="Buckets explicitly supplied by the operator.")
    ]
    omitted_buckets: Annotated[
        list[str], Field(description="Buckets not supplied; never evidence of zero.")
    ]
    complete_buckets: Annotated[
        bool, Field(description="Whether all required expense buckets were supplied.")
    ]


class PaydayAssessment(ResultObject):
    employee_id: Annotated[str, Field(description="Operator reference echoed from the input.")]
    qe_day: DateText
    sg_amount: DecimalText
    remitted: Annotated[
        str | None, Field(description="Remittance date, YYYY-MM-DD, or null if unknown.")
    ]
    received: Annotated[
        str | None, Field(description="Fund-receipt date, YYYY-MM-DD, or null if unknown.")
    ]
    due: Annotated[
        str | None, Field(description="Engine deadline, YYYY-MM-DD, or null when not applicable.")
    ]
    pathway: Annotated[str, Field(description="Deadline pathway chosen by the engine.")]
    verdict: Annotated[
        str, Field(description="Engine contribution verdict; read alongside caveats and pathway.")
    ]
    days_late: Annotated[
        int | None, Field(description="Engine days late, or null when not established.")
    ]
    lateness_basis: Annotated[
        str | None, Field(description="Receipt or assessment basis used to measure lateness.")
    ]
    base_shortfall: MaybeDecimal
    final_shortfall: MaybeDecimal
    notional_earnings: MaybeDecimal
    experimental_sgc_low: MaybeDecimal
    experimental_sgc_high: MaybeDecimal
    uplift: Annotated[
        dict[str, dict[str, DecimalText]] | None,
        Field(
            description="Experimental uplift scenarios by history and disclosure timing, or null."
        ),
    ]
    notes: Annotated[list[str], Field(description="Engine assessment notes.")]
    caveats: Caveats
    horizon_verdicts: Annotated[
        list[str] | None, Field(description="Engine horizon verdicts, when available.")
    ]


class PaydayReview(EngineResult):
    law_content_date: DateText
    as_at: Annotated[str, Field(description="Explicit operator assessment date, YYYY-MM-DD.")]
    disclaimer: Annotated[
        str, Field(description="Experimental review and fund-receipt limitations.")
    ]
    result: Annotated[
        PaydayAssessment,
        Field(description="Contribution assessment; not a compliance determination."),
    ]


class VerificationSource(ResultObject):
    verify_at: Annotated[
        str | None,
        Field(description="Engine verification URL; empty or null when none is available."),
    ]


class Div7aResult(EngineResult):
    law_content_date: DateText
    law_compilation: Annotated[str, Field(description="Compiled law identified by the engine.")]
    disclaimer: Annotated[
        str, Field(description="Experimental scope and human-review requirements.")
    ]
    response_detail: NotRequired[
        Annotated[
            Literal["summary"],
            Field(description="Present for summary responses; omitted for full responses."),
        ]
    ]
    source: NotRequired[
        Annotated[
            VerificationSource, Field(description="Concise verification source; summary only.")
        ]
    ]


class Div7aRate(Div7aResult):
    year_of_income: YearText
    verdict: Annotated[
        Literal["KNOWN", "UNKNOWN"], Field(description="Whether the engine has a reviewed rate.")
    ]
    benchmark_rate: Annotated[
        str | None, Field(description="Decimal fraction, e.g. 0.08 means 8%; null if UNKNOWN.")
    ]
    reason: Annotated[
        str | None,
        Field(description="Engine explanation when the rate is unavailable; otherwise null."),
    ]
    provenance: NotRequired[Provenance]
    statutory_trace: NotRequired[Trace]


class Div7aGate(ResultObject):
    verdict: Annotated[
        Literal["COMPLYING", "NOT_COMPLYING", "UNKNOWN"],
        Field(description="Reviewed s 109N gate only; UNKNOWN never means false or compliant."),
    ]
    loan_id: Annotated[str, Field(description="Operator loan reference.")]
    benchmark_year_used: Annotated[
        str | None, Field(description="Engine benchmark year, YYYY-YY, if known.")
    ]
    benchmark_rate: MaybeDecimal
    maximum_term_years_allowed: MaybeDecimal
    reasons: Reasons
    caveats: Caveats
    benchmark_provenance: NotRequired[Provenance | None]
    limbs: NotRequired[
        Annotated[list[dict[str, str]], Field(description="Individual s 109N findings; full only.")]
    ]
    statutory_trace: NotRequired[Trace]


class Div7aRepayment(ResultObject):
    verdict: Annotated[
        str,
        Field(
            description="Engine s 109E outcome, including MYR_MET, MYR_SHORT, UNKNOWN or REFUSED."
        ),
    ]
    loan_id: Annotated[str, Field(description="Operator loan reference.")]
    year_of_income: YearText
    gate_verdict: Annotated[
        str | None, Field(description="s 109N gate outcome used in the repayment review.")
    ]
    benchmark_rate: MaybeDecimal
    amalgamated_loan_unpaid_at_end_of_previous_year: MaybeDecimal
    remaining_term_years_used: MaybeDecimal
    myr_required: Annotated[
        str | None, Field(description="Required repayment in AUD; null if not determined.")
    ]
    payments_applied: MaybeDecimal
    shortfall: MaybeDecimal
    experimental_deemed_dividend_exposure: Annotated[
        str | None,
        Field(
            description="Experimental AUD exposure only, not an assessed dividend; null if unknown."
        ),
    ]
    rounding: Annotated[str, Field(description="Rounding rule reported by the engine.")]
    reasons: Reasons
    caveats: Caveats
    benchmark_provenance: NotRequired[Provenance | None]
    statutory_trace: NotRequired[Trace]


class Div7aReview(Div7aResult):
    gate: Annotated[Div7aGate, Field(description="s 109N gate outcome and reasons.")]
    minimum_yearly_repayment: Annotated[
        Div7aRepayment, Field(description="s 109E review or explicit refusal.")
    ]


class ScopeRefusal(ResultObject):
    ok: Annotated[Literal[False], Field(description="Unsupported request was refused.")]
    available: Annotated[
        Literal[False], Field(description="This compatibility tool cannot calculate a repayment.")
    ]
    reviewed_engine: Annotated[
        Literal[True], Field(description="Separate tools expose the reviewed engine scope.")
    ]
    code: Annotated[
        Literal["ERR_POLICY_DIV7A_SCOPE_REFUSED"],
        Field(description="Machine-readable refusal code."),
    ]
    reason: Annotated[str, Field(description="Supported alternatives and excluded matters.")]


class SyntheticFixture(ResultObject):
    synthetic: Annotated[
        Literal[True], Field(description="Fabricated test data; never real client results.")
    ]
    not_a_lodgment: Annotated[Literal[True], Field(description="Never a lodgment-ready payload.")]
    form_type: Annotated[
        Literal["CTR_AU_2025", "BAS_AU_ACTIVITY_STATEMENT"],
        Field(
            description="Fixture variant; CTR carries income/reconciliation, BAS carries GST/PAYG/summary."
        ),
    ]
    entity: Annotated[
        dict[str, Any],
        Field(description="Fabricated identity and period fields for the chosen variant."),
    ]
    income_statement: NotRequired[
        Annotated[dict[str, DecimalText], Field(description="Synthetic CTR income figures only.")]
    ]
    reconciliation: NotRequired[
        Annotated[dict[str, DecimalText], Field(description="Synthetic CTR reconciliation only.")]
    ]
    gst_labels: NotRequired[
        Annotated[dict[str, DecimalText], Field(description="Synthetic BAS GST labels only.")]
    ]
    payg_withholding_labels: NotRequired[
        Annotated[dict[str, DecimalText], Field(description="Synthetic BAS PAYG labels only.")]
    ]
    summary: NotRequired[
        Annotated[dict[str, DecimalText], Field(description="Synthetic BAS total only.")]
    ]
