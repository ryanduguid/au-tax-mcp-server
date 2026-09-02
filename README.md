# australian-accounting

Development home for the Aus Accounting MCP application and, as they are imported, six
independently released Australian accounting engines. Each component keeps its own
distribution name, version, lockfile, tests, release notes, commands and licence. There
is no root package, root lockfile, shared runtime library or combined version.

## Components

| Path | Distribution | Import package | Commands |
|---|---|---|---|
| `apps/aus-accounting-mcp/` | `aus-accounting-mcp` | `aus_accounting_mcp` | `aus-accounting-mcp`, `aus-accounting-mcp-demo` |

Engines arrive under `packages/<distribution>/` as verified snapshots. `IMPORTS.md`
records every source repository, commit and tree.

## Working in a component

Change into the component directory and use the commands its own `README.md`,
`AGENTS.md` or `CONTRIBUTING.md` documents. The root `CONTRIBUTING.md` routes the
common commands.

## Boundaries

- The MCP application depends on engines only through their published distributions.
- Engines never import `aus_accounting_mcp` or another engine.
- Only the workflows under the root `.github/workflows/` are active.
- No client data, credentials or generated client reports enter this repository.

Each component's `LICENSE` applies to that component. Outputs are review aids, not
advice.
