# Contributing

Each component is developed, tested and released from its own directory.

## Command routing

| Component | Directory | Checks |
|---|---|---|
| Aus Accounting MCP | `apps/aus-accounting-mcp/` | `uv run --locked --extra dev pytest -q`; `uv run --locked --extra dev ruff check aus_accounting_mcp tests`; `uv run --locked --extra dev mypy aus_accounting_mcp` |

Engine rows are added as each engine is imported.

## Rules

- Keep a change inside one component unless it is a root policy or workflow change.
- Do not move, rename or refactor a component in the same change that alters its
  behaviour.
- Never add a root package manager, root lockfile, shared runtime library, unified
  version or code generator.
- Engines must not import the MCP application or each other, and production code must
  not use relative imports that leave the component directory.
- Use fabricated data only, and follow the component's own `CONTRIBUTING.md` and
  `SECURITY.md`.

## Releases

Releases are per component. A release uses the namespaced tag `<component>/vX.Y.Z`
and that component's root release workflow. Nothing publishes from a contribution
branch.
