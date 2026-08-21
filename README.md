# aus-accounting-mcp

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Model Context Protocol](https://img.shields.io/badge/MCP-Standard%20Protocol-8A2BE2)](https://modelcontextprotocol.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Unified Model Context Protocol (MCP) server for Australian computational accounting, ATO small business benchmarks, Payday Super 2026, and Division 7A.**

Compatible with **Claude Desktop, Claude Code, Cursor, Antigravity, and OpenAccountants**.

---

## 🛠️ Provided MCP Tools

| Tool Name | Description | Key Statutory Reference |
| :--- | :--- | :--- |
| `get_ato_benchmarks` | Queries ATO small business benchmarks and performs variance analysis on expense ratios. | ATO Small Business Benchmarks |
| `calc_payday_super_deadline` | Calculates the 2026 national seven-business-day usual-period end date and estimates clearing-house receipt timing. It does not assess compliance or SGC liability. | Payday Super (1 July 2026) / SGAA 1992 |
| `calc_div7a_repayment` | Calculates s 109N Minimum Yearly Repayment (MYR), amortisation schedule, and franked dividend offset journals. | Division 7A ITAA 1936 |
| `generate_synthetic_sbr_fixture` | Generates synthetic, zero-network, privacy-safe ATO SBR payloads (CTR and BAS) for testing AI agents. | Standard Business Reporting (SBR) |

---

## Payday Super timing scope

`calc_payday_super_deadline` is a timing estimator, not a compliance or SGC
calculator. It does not collect actual fund receipt, contribution eligibility
or allocation, assessment, uplift or choice-loading facts. Every result returns
`compliance_status: "NOT_ASSESSED"` with a warning. A contribution amount of
zero can still be timed but cannot produce a compliance conclusion; negative
amounts and submission dates before payday are rejected.

The calendar covers 2026 only and fails closed outside that verified horizon.
It uses the national union of whole-of-State, ACT and NT public holidays under
SGAA 1992 s 6(1); regional and part-day holidays are not excluded. The public
clearing-house route values are `COMMERCIAL` and `DIRECT`. SBSCH is unavailable
because it closed on 1 July 2026.

---

## Monetary input limits

All monetary MCP inputs accept exact decimal strings (preferred) and legacy
JSON numbers. Inputs must be finite, have an absolute value no greater than
AUD 1,000,000,000,000.00 and use no more than two fractional decimal places.
Exponent notation is accepted only when the resulting value and scale meet
those limits, so `1e2` and `1e-2` are valid but `1e30`, `1e10000` and
`1e-10000` are rejected. This conservative domain keeps the compatibility
number fields and derived JSON finite. Use each `*_exact` string result for
exact monetary values; legacy number inputs and number outputs may already
have been rounded by a client or JSON parser.

---

## ⚡ Installation & Quickstart

### 1. Install via pip
```bash
pip install .
```

### 2. Run MCP Server (stdio transport)
```bash
aus-accounting-mcp
```

---

## 🔌 Client Integration

### Claude Desktop
Add to your `claude_desktop_config.json` (`%APPDATA%\Claude\claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "aus-accounting": {
      "command": "aus-accounting-mcp"
    }
  }
}
```

### Cursor
Add to `.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "aus-accounting": {
      "command": "aus-accounting-mcp"
    }
  }
}
```

### Claude Code
```bash
claude mcp add aus-accounting -- aus-accounting-mcp
```

---

## ⚖️ License
MIT License. Created by Ryan Duguid.
