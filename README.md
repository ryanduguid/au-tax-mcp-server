# JohnKenley

[![tests](https://github.com/ryanduguid/JohnKenley/actions/workflows/ci.yml/badge.svg)](https://github.com/ryanduguid/JohnKenley/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Model Context Protocol](https://img.shields.io/badge/MCP-Standard%20Protocol-8A2BE2)](https://modelcontextprotocol.io/)
[![Glama](https://glama.ai/mcp/servers/ryanduguid/JohnKenley/badge)](https://glama.ai/mcp/servers/ryanduguid/JohnKenley)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

MCP facade over reviewed Australian computational accounting engines. Compatible with Claude Desktop, Claude Code, Cursor, Codex and Antigravity.

> [!WARNING]
> **Not tax advice.** This server returns structured results, refusals, and citations. It does not lodge, and it does not replace a registered agent. See [DISCLAIMER.md](DISCLAIMER.md).

This server does **not** reimplement tax law. Payday Super and ATO small-business benchmarks are delegated to:

- [CharlesHenryWickens](https://github.com/ryanduguid/CharlesHenryWickens) (`payday-super-checker`)
- [RaymondChambers](https://github.com/ryanduguid/RaymondChambers) (`ato-benchmark-compare`)

Division 7A is **refused** until a reviewed engine exists. SBR payloads are **synthetic fixtures**, not lodgments.

## Install

Python 3.10+ and [uv](https://docs.astral.sh/uv/). The engines install from GitHub because they are not on PyPI, so the one-command path is `uvx` from this repository:

```bash
uvx --from git+https://github.com/ryanduguid/JohnKenley aus-accounting-mcp
```

Clone and `pip install .` still works when you want a local editable tree.

## Client integration

**Standard config** works with hosts that run a local stdio MCP server:

```json
{
  "mcpServers": {
    "aus-accounting": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/ryanduguid/JohnKenley",
        "aus-accounting-mcp"
      ]
    }
  }
}
```

Ready-made copies live in [`clients/`](clients/).

### Cursor

[![Add to Cursor](https://img.shields.io/badge/Cursor-Add%20MCP-black)](https://cursor.com/en/install-mcp?name=aus-accounting&config=eyJjb21tYW5kIjoidXZ4IiwiYXJncyI6WyItLWZyb20iLCJnaXQraHR0cHM6Ly9naXRodWIuY29tL3J5YW5kdWd1aWQvSm9obktlbmxleSIsImF1cy1hY2NvdW50aW5nLW1jcCJdfQ==)

Or drop the standard config into `~/.cursor/mcp.json`.

### Claude Desktop

Paste the standard config into `claude_desktop_config.json` (`%APPDATA%\Claude\` on Windows, `~/Library/Application Support/Claude/` on macOS).

### Claude Code

```bash
claude mcp add aus-accounting -- uvx --from git+https://github.com/ryanduguid/JohnKenley aus-accounting-mcp
```

### Codex

```bash
codex mcp add aus-accounting -- uvx --from git+https://github.com/ryanduguid/JohnKenley aus-accounting-mcp
```

## Tools

| Tool | Job | Engine |
| :--- | :--- | :--- |
| `list_ato_benchmark_industries` | List or search the shipped ATO business types | ato-benchmark-compare |
| `get_ato_benchmarks` | Compare operator-supplied bucket totals to ATO ranges | ato-benchmark-compare |
| `calc_payday_super_deadline` | Review one contribution against Payday Super timing | payday-super-checker |
| `refuse_div7a` | Returns a refusal. No reviewed Div 7A engine is wired | none |
| `generate_synthetic_sbr_fixture` | Synthetic CTR/BAS for agent tests (`synthetic: true`) | local fixture |

`calc_payday_super_deadline` requires `as_at`. It does not invent clearing-house latency and cannot confirm LCR 2026/1 transition allocation. A remittance date alone cannot produce `ON_TIME`. Omitted ATO expense buckets are `not_supplied`, not zero.

Amounts are decimal strings, finite, at most two decimal places, and no greater than AUD 1,000,000,000,000.00. Dates are ISO-8601. Payday Super uses payday-super-checker's national SGAA 1992 s 6(1) calendar.

Ask the agent:

```text
Compare these P&L buckets to the ATO small-business benchmarks for this industry. Omit buckets I have not supplied. Do not treat missing as zero.
```

```text
Review this Payday Super contribution. QE day, remitted date, and fund-receipt date are in the CSV. as_at is today. Do not invent an SGC charge.
```

## Licence

MIT License. Created by Ryan Duguid. Boundary statement: [DISCLAIMER.md](DISCLAIMER.md). Discovery copy: [docs/DISCOVERY.md](docs/DISCOVERY.md). Cite: [CITATION.cff](CITATION.cff).
