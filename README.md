# John Kenley

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Model Context Protocol](https://img.shields.io/badge/MCP-Standard%20Protocol-8A2BE2)](https://modelcontextprotocol.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

MCP facade over reviewed Australian computational accounting engines. Compatible with Claude Desktop, Claude Code, Cursor and Antigravity.

This server does **not** reimplement tax law. Payday Super and ATO small-business benchmarks are delegated to:

- [CharlesHenryWickens](https://github.com/ryanduguid/CharlesHenryWickens) (`payday-super-checker`, `paydaysuper`)
- [RaymondChambers](https://github.com/ryanduguid/RaymondChambers) (`ato-benchmark-compare`)

Division 7A is **refused** until a reviewed engine exists. SBR payloads are **synthetic fixtures**, not lodgments.

The repository name is the public project identity; the `aus-accounting-mcp` distribution, `aus-accounting-mcp` command, `aus_accounting_mcp` import package and the `aus-accounting-mcp` MCP server name remain compatibility identifiers, so existing client configurations keep working unchanged.

John Kenley was the first technical officer of the Australian Society of Accountants, now CPA Australia, and moved to a full-time role at the Australian Accounting Research Foundation in 1966, where he helped establish the Auditing Standards Board. This server exposes reviewed engines only, and refuses the rest.

## Tools

| Tool | Engine | What it does |
| :--- | :--- | :--- |
| `list_ato_benchmark_industries` | ato-benchmark-compare | List or search the shipped ATO business types |
| `get_ato_benchmarks` | ato-benchmark-compare | Compare operator-supplied bucket totals to ATO ranges |
| `calc_payday_super_deadline` | payday-super-checker | Review one contribution; `as_at` is required; does not invent clearing-house latency; cannot confirm LCR 2026/1 transition allocation |
| `calc_div7a_repayment` | none | Returns a refusal. No reviewed Div 7A engine is wired |
| `generate_synthetic_sbr_fixture` | local fixture | Synthetic CTR/BAS for agent tests (`synthetic: true`) |

Amounts are decimal strings, finite, at most two decimal places, and no greater than AUD 1,000,000,000,000.00. Dates are ISO-8601. Payday Super uses payday-super-checker's national SGAA 1992 s 6(1) calendar. The checker marks `UNKNOWN` or refuses where the facts do not establish the statutory test. A remittance date alone cannot produce `ON_TIME`. Omitted ATO expense buckets are `not_supplied`, not zero.

## Install

Python 3.10+. The engines are installed from GitHub because they are not on PyPI.

```bash
git clone https://github.com/ryanduguid/JohnKenley.git
cd JohnKenley
pip install .
```

```bash
aus-accounting-mcp
```

## Client integration

### Claude Desktop

`%APPDATA%\Claude\claude_desktop_config.json`:

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

`.cursor/mcp.json`:

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

## License

MIT License. Created by Ryan Duguid.
