import asyncio
import json

import pytest
from mcp.server.fastmcp.exceptions import ToolError

from aus_accounting_mcp.server import mcp

_MAX_MONEY = "1000000000000.00"
_MONETARY_ENDPOINT_FIELDS = [
    ("get_ato_benchmarks", "annual_turnover"),
    ("get_ato_benchmarks", "cost_of_sales"),
    ("get_ato_benchmarks", "labour_expenses"),
    ("get_ato_benchmarks", "rent_expenses"),
    ("get_ato_benchmarks", "motor_vehicle_expenses"),
    ("calc_payday_super_deadline", "sg_contribution"),
    ("calc_div7a_repayment", "loan_principal"),
    ("generate_synthetic_sbr_fixture", "revenue_or_sales"),
]


def _call_tool(name, arguments):
    contents = asyncio.run(mcp.call_tool(name, arguments))
    return json.loads(contents[0].text)


def _call_payday_tool(sg_contribution, clearing_house_type=None):
    arguments = {
        "pay_date_iso": "2026-07-07",
        "submission_date_iso": "2026-07-07",
        "sg_contribution": sg_contribution,
    }
    if clearing_house_type is not None:
        arguments["clearing_house_type"] = clearing_house_type

    return _call_tool("calc_payday_super_deadline", arguments)


def _call_tool_with_monetary_value(tool_name, field_name, value):
    if tool_name == "get_ato_benchmarks":
        arguments = {
            "industry_key": "cafes_and_restaurants",
            "annual_turnover": "1000000.00",
        }
    elif tool_name == "calc_payday_super_deadline":
        arguments = {
            "pay_date_iso": "2026-07-07",
            "submission_date_iso": "2026-07-07",
            "sg_contribution": "1200.00",
        }
    elif tool_name == "calc_div7a_repayment":
        arguments = {
            "borrower_name": "Alice",
            "lender_entity_name": "HoldingCo Pty Ltd",
            "loan_principal": "100000.00",
        }
    else:
        arguments = {
            "form_type": "CTR",
            "revenue_or_sales": "1000000.00",
        }

    arguments[field_name] = value
    return _call_tool(tool_name, arguments)


def test_payday_mcp_tool_preserves_exact_decimal_string_input_and_output():
    result = _call_payday_tool("999999999999.99")

    assert result["sg_contribution_exact"] == "999999999999.99"
    assert result["estimated_receipt_within_usual_period"] is True
    assert result["compliance_status"] == "NOT_ASSESSED"
    assert "sgc_exposure" not in result
    assert "is_compliant" not in result
    assert result["monetary_precision"]["input_mode"] == "exact_decimal_string"
    assert result["monetary_precision"]["input_warning"] is None
    assert "*_exact" in result["monetary_precision"]["output_warning"]


def test_payday_mcp_tool_keeps_legacy_numbers_with_an_explicit_precision_warning():
    result = _call_payday_tool(1000.25)

    assert result["sg_contribution"] == 1000.25
    assert result["sg_contribution_exact"] == "1000.25"
    assert result["monetary_precision"]["input_mode"] == "legacy_json_number"
    assert "decimal string" in result["monetary_precision"]["input_warning"]


def test_payday_mcp_tool_rejects_a_non_decimal_string_with_a_field_error():
    with pytest.raises(
        ToolError, match="sg_contribution must be a finite decimal value"
    ):
        _call_payday_tool("not-a-number")


def test_payday_mcp_tool_parses_the_documented_direct_route_by_value():
    result = _call_payday_tool("1200.00", clearing_house_type="DIRECT")

    assert result["estimated_fund_receipt"] == "2026-07-08"
    assert result["estimated_receipt_within_usual_period"] is True


@pytest.mark.parametrize("invalid_route", ["DIRECT_PAYMENT", "SBSCH"])
def test_payday_mcp_tool_rejects_routes_outside_the_public_contract(invalid_route):
    with pytest.raises(ToolError):
        _call_payday_tool("1200.00", clearing_house_type=invalid_route)


def test_payday_mcp_schema_constrains_routes_and_omits_obsolete_sgc_inputs():
    tools = asyncio.run(mcp.list_tools())
    tool = next(
        candidate for candidate in tools
        if candidate.name == "calc_payday_super_deadline"
    )
    properties = tool.inputSchema["properties"]

    assert properties["clearing_house_type"]["enum"] == ["COMMERCIAL", "DIRECT"]
    assert "total_salary_wages" not in properties


def test_benchmark_mcp_tool_preserves_exact_decimal_strings():
    result = _call_tool(
        "get_ato_benchmarks",
        {
            "industry_key": "cafes_and_restaurants",
            "annual_turnover": "999999999999.99",
            "cost_of_sales": "499999999999.99",
        },
    )

    assert result["annual_turnover_exact"] == "999999999999.99"
    assert result["metrics"][0]["actual_amount_exact"] == "499999999999.99"
    assert result["monetary_precision"]["input_mode"] == "exact_decimal_string"


def test_div7a_mcp_tool_uses_exact_decimal_input_through_the_myr_calculation():
    result = _call_tool(
        "calc_div7a_repayment",
        {
            "borrower_name": "Alice",
            "lender_entity_name": "HoldingCo Pty Ltd",
            "loan_principal": "999999999999.99",
        },
    )

    assert result["principal_exact"] == "999999999999.99"
    assert result["schedule"][0]["opening_balance_exact"] == "999999999999.99"
    assert result["schedule"][0]["minimum_yearly_repayment_exact"] == (
        "197159697396.67"
    )
    assert result["monetary_precision"]["input_mode"] == "exact_decimal_string"


@pytest.mark.parametrize(
    ("form_type", "section", "field"),
    [
        ("CTR", "income_statement", "total_business_income_exact"),
        ("BAS", "gst_labels", "G1_total_sales_exact"),
    ],
)
def test_synthetic_sbr_mcp_tool_preserves_exact_decimal_strings(
    form_type,
    section,
    field,
):
    result = _call_tool(
        "generate_synthetic_sbr_fixture",
        {
            "form_type": form_type,
            "revenue_or_sales": "999999999999.99",
        },
    )

    assert result[section][field] == "999999999999.99"
    assert result["monetary_precision"]["input_mode"] == "exact_decimal_string"


@pytest.mark.parametrize(("tool_name", "field_name"), _MONETARY_ENDPOINT_FIELDS)
def test_every_monetary_mcp_schema_accepts_legacy_numbers_and_exact_strings(
    tool_name,
    field_name,
):
    tools = asyncio.run(mcp.list_tools())
    tool = next(candidate for candidate in tools if candidate.name == tool_name)
    field_schema = tool.inputSchema["properties"][field_name]

    assert {entry["type"] for entry in field_schema["anyOf"]} >= {
        "number",
        "string",
    }


@pytest.mark.parametrize(("tool_name", "field_name"), _MONETARY_ENDPOINT_FIELDS)
@pytest.mark.parametrize(
    "invalid_value",
    [
        "1000000000000.01",
        "-1000000000000.01",
        "1e30",
        "1e10000",
    ],
)
def test_every_monetary_endpoint_rejects_values_above_the_domain_limit(
    tool_name,
    field_name,
    invalid_value,
):
    with pytest.raises(
        ToolError,
        match=(
            rf"{field_name} absolute value must not exceed "
            r"AUD 1000000000000\.00"
        ),
    ):
        _call_tool_with_monetary_value(tool_name, field_name, invalid_value)


@pytest.mark.parametrize(("tool_name", "field_name"), _MONETARY_ENDPOINT_FIELDS)
@pytest.mark.parametrize("invalid_value", ["0.001", "1e-10000"])
def test_every_monetary_endpoint_rejects_more_than_two_decimal_places(
    tool_name,
    field_name,
    invalid_value,
):
    with pytest.raises(
        ToolError,
        match=rf"{field_name} must have no more than 2 decimal places",
    ):
        _call_tool_with_monetary_value(tool_name, field_name, invalid_value)


@pytest.mark.parametrize(("tool_name", "field_name"), _MONETARY_ENDPOINT_FIELDS)
def test_every_monetary_endpoint_accepts_the_limit_and_serialises_finite_json(
    tool_name,
    field_name,
):
    result = _call_tool_with_monetary_value(tool_name, field_name, _MAX_MONEY)

    json.dumps(result, allow_nan=False)
