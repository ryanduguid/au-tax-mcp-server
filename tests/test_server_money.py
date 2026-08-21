import asyncio
import json

import pytest
from mcp.server.fastmcp.exceptions import ToolError

from aus_accounting_mcp.server import mcp


def _call_payday_tool(sg_contribution, total_salary_wages=None):
    arguments = {
        "pay_date_iso": "2026-07-07",
        "submission_date_iso": "2026-07-07",
        "sg_contribution": sg_contribution,
    }
    if total_salary_wages is not None:
        arguments["total_salary_wages"] = total_salary_wages

    contents = asyncio.run(mcp.call_tool("calc_payday_super_deadline", arguments))
    return json.loads(contents[0].text)


def test_payday_mcp_tool_preserves_exact_decimal_string_input_and_output():
    result = _call_payday_tool(
        "9007199254740993.01",
        total_salary_wages="10000.00",
    )

    assert result["sg_contribution_exact"] == "9007199254740993.01"
    assert result["sgc_exposure"]["total_liability_exact"] == "0.00"
    assert result["monetary_precision"]["input_mode"] == "exact_decimal_string"
    assert result["monetary_precision"]["input_warning"] is None
    assert "*_exact" in result["monetary_precision"]["output_warning"]


def test_payday_mcp_tool_keeps_legacy_numbers_with_an_explicit_precision_warning():
    result = _call_payday_tool(1000.25)

    assert result["sg_contribution"] == 1000.25
    assert result["sg_contribution_exact"] == "1000.25"
    assert result["monetary_precision"]["input_mode"] == "legacy_json_number"
    assert "decimal string" in result["monetary_precision"]["input_warning"]


def test_payday_mcp_schema_accepts_both_legacy_numbers_and_exact_strings():
    tools = asyncio.run(mcp.list_tools())
    payday_tool = next(tool for tool in tools if tool.name == "calc_payday_super_deadline")
    sg_schema = payday_tool.inputSchema["properties"]["sg_contribution"]

    assert {entry["type"] for entry in sg_schema["anyOf"]} >= {"number", "string"}


def test_payday_mcp_tool_rejects_a_non_decimal_string_with_a_field_error():
    with pytest.raises(
        ToolError, match="sg_contribution must be a finite decimal value"
    ):
        _call_payday_tool("not-a-number")
