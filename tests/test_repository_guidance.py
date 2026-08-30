from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]


def _ci_run_commands() -> list[str]:
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    commands = re.findall(r"^\s+(?:-\s+)?run:\s*(\S.*)$", workflow, flags=re.MULTILINE)
    return list(dict.fromkeys(commands))


def _section(document: str, heading: str) -> str:
    match = re.search(
        rf"^## {re.escape(heading)}\s*$\n(.*?)(?=^## |\Z)",
        document,
        flags=re.MULTILINE | re.DOTALL,
    )
    assert match is not None, f"missing ## {heading} section"
    return match.group(1)


def _fenced_commands(section: str) -> list[str]:
    blocks = re.findall(r"```(?:bash|powershell)\n(.*?)```", section, flags=re.DOTALL)
    return [line for block in blocks for line in block.splitlines() if line]


def test_agents_preserves_the_mcp_domain_boundaries() -> None:
    guidance = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

    required = (
        "MCP facade",
        "delegated",
        "payday-super-checker",
        "ato-benchmark-compare",
        "Division 7A",
        "refused",
        "synthetic-only",
        "aus_accounting_mcp.money",
        "Never invent current rates",
    )
    for text in required:
        assert text in guidance


def test_agents_tracks_exact_ci_commands_and_classifies_other_checks() -> None:
    guidance = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

    assert _fenced_commands(_section(guidance, "CI gates")) == _ci_run_commands()
    supplementary = _section(guidance, "Supplementary local and release-readiness checks")
    assert "not CI gates" in supplementary
    assert "uv run --locked aus-accounting-mcp-demo" in supplementary


def test_runtime_entry_points_and_contribution_scope_are_explicit() -> None:
    assert (ROOT / "CLAUDE.md").read_text(encoding="utf-8") == "@AGENTS.md\n"

    contributing = re.sub(
        r"\s+",
        " ",
        (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8"),
    )
    required = (
        "adapter",
        "delegated engines",
        "compatibility.json",
        "server.json",
        "docs/quick-proof.txt",
        "docs/quick-proof.gif",
        "release workflow",
        "Publish to PyPI",
        "Publish to MCP Registry",
    )
    for text in required:
        assert text in contributing
