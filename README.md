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
| `calc_payday_super_deadline` | Evaluates Payday Super 7 business day compliance window and simulates clearing house latency and SGC liability. | Payday Super (1 July 2026) / SGAA 1992 |
| `calc_div7a_repayment` | Calculates s 109N Minimum Yearly Repayment (MYR), amortisation schedule, and franked dividend offset journals. | Division 7A ITAA 1936 |
| `generate_synthetic_sbr_fixture` | Generates synthetic, zero-network, privacy-safe ATO SBR payloads (CTR and BAS) for testing AI agents. | Standard Business Reporting (SBR) |

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