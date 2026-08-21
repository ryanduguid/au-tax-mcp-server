import asyncio
import json

import pytest
from mcp.server.fastmcp.exceptions import ToolError

from aus_accounting_mcp.server import mcp


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


def test_payday_mcp_tool_preserves_exact_decimal_string_input_and_output():
    result = _call_payday_tool("9007199254740993.01")

    assert result["sg_contribution_exact"] == "9007199254740993.01"
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
            "annual_turnover": "9007199254740993.01",
            "cost_of_sales": "4503599627370496.505",
        },
    )

    assert result["annual_turnover_exact"] == "9007199254740993.01"
    assert result["metrics"][0]["actual_amount_exact"] == "4503599627370496.505"
    assert result["monetary_precision"]["input_mode"] == "exact_decimal_string"


def test_div7a_mcp_tool_uses_exact_decimal_input_through_the_myr_calculation():
    result = _call_tool(
        "calc_div7a_repayment",
        {
            "borrower_name": "Alice",
            "lender_entity_name": "HoldingCo Pty Ltd",
            "loan_principal": "9007199254740993.01",
        },
    )

    assert result["principal_exact"] == "9007199254740993.01"
    assert result["schedule"][0]["opening_balance_exact"] == "9007199254740993.01"
    assert result["schedule"][0]["minimum_yearly_repayment_exact"] == (
        "1775856679456262.12"
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
            "revenue_or_sales": "9007199254740993.01",
        },
    )

    assert result[section][field] == "9007199254740993.01"
    assert result["monetary_precision"]["input_mode"] == "exact_decimal_string"


@pytest.mark.parametrize(
    ("tool_name", "field_name"),
    [
        ("get_ato_benchmarks", "annual_turnover"),
        ("get_ato_benchmarks", "cost_of_sales"),
        ("get_ato_benchmarks", "labour_expenses"),
        ("get_ato_benchmarks", "rent_expenses"),
        ("get_ato_benchmarks", "motor_vehicle_expenses"),
        ("calc_payday_super_deadline", "sg_contribution"),
        ("calc_div7a_repayment", "loan_principal"),
        ("generate_synthetic_sbr_fixture", "revenue_or_sales"),
    ],
)
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
