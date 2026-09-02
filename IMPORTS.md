# Imports

Source repositories enter this repository as single verified snapshots created with
`git subtree add --prefix=packages/<destination> <url> <commit> --squash`. Historical
tags and releases stay in the source repositories, which remain the authoritative
location for pre-consolidation history.

Tracked-tree SHA-256 is the SHA-256 of the NUL-delimited bytes of
`git ls-tree -r --full-tree -z HEAD` in a fresh clone of the source at the recorded
commit. The imported subtree must have the same tree id as the source commit.

## Anchor

| Repository | Commit | Tree | Tracked-tree SHA-256 | Latest release | Location |
|---|---|---|---|---|---|
| `https://github.com/ryanduguid/aus-accounting-mcp.git` | `d6bf940cc6850ecb97c07035519167ed86e151ad` | `53718483bad344783dc9728ad5f81ad14a81d723` | `fd5600a4e36b8e090abdc165993e3e7344247b08cdca9bff5f0e5870613f6bae` | v0.1.6 (2026-08-31) | moved to `apps/aus-accounting-mcp/` |

## Sources

| Repository | Commit | Tree | Tracked-tree SHA-256 | Latest release | Destination | Status |
|---|---|---|---|---|---|---|
| `https://github.com/ryanduguid/ato-benchmark-compare.git` | `d290c8b77d5cc47346d7a41e843642c2c7908748` | `2405cd169c5731298851f96d7c992715c49c3c6f` | `29468715ce198635375c944c865c3b15578b84f3ac9945fb53a9731d77dea189` | v0.1.5 (2026-08-31) | `packages/ato-benchmark-compare/` | imported: squash `965739bf4348b74987bd8541a996599bdaeba53b`, merge `f4289747daa83a79ee318d4405fd45c3ea9d6cd8` |
| `https://github.com/ryanduguid/payday-super-checker.git` | `5ffe1d48ef4262bb6aecb34122b314fec7c437c6` | `89631a8992225fd11ca637e726968838667d5846` | `3bc9819cc9230709630fac33f1276944a744d3310d23d005c84b429f6291368e` | v0.1.2 prerelease (2026-08-23) | `packages/payday-super-checker/` | pending |
| `https://github.com/ryanduguid/div7a-loan-review.git` | `753e7d630cba0f3b4d5b97f29141c685fc47dd09` | `0d65c3cac7799ffd83f835223bed0253bbf6b212` | `baea80653779c9270c70751a2418b278bcadef1ee7cc10b1eccdf2113e163680` | v0.1.0 (2026-08-31) | `packages/div7a-loan-review/` | pending |
| `https://github.com/ryanduguid/TheExchequerTally.git` | `1e89aebc9611f1e87114290dc13f3434ac6f5d88` | `a6c50adda17a8ef97f2f439bb64da5761c712880` | `b099a7cddaf55c14ad042445d28b507a3a697e0e47c217a44c508967b08e20ca` | v0.1.2 (2026-08-22) | `packages/the-exchequer-tally/` | pending |
| `https://github.com/ryanduguid/SolomonsSword.git` | `af988a45f777559116ec3e59d5abdb0ee7771f90` | `66422d183637058701546a7a1d7ac8aa1254206b` | `b66aa69e69e1589c7864d4d01b60e5f5314c36a5eac344a3749b4faf4cdf4a3e` | v0.1.2 (2026-08-22) | `packages/solomons-sword/` | pending |
| `https://github.com/ryanduguid/TheWIPTally.git` | `f6dcdd702d9344745e95174c8783c0b77b5f9dd2` | `578a0419d959801c36ba429969c96d2585f7ab93` | `9549f0ce2f08063cfc5a39ce1febe630dcb0ebbf60a70bcabef3a3e484c1548a` | none | `packages/the-wip-tally/` | pending |

## Import records

### ato-benchmark-compare

- Imported 2026-09-02 from `https://github.com/ryanduguid/ato-benchmark-compare.git` at commit
  `d290c8b77d5cc47346d7a41e843642c2c7908748` (tree `2405cd169c5731298851f96d7c992715c49c3c6f`,
  tracked-tree SHA-256 `29468715ce198635375c944c865c3b15578b84f3ac9945fb53a9731d77dea189`,
  latest source release v0.1.5).
- Command: `git subtree add --prefix=packages/ato-benchmark-compare https://github.com/ryanduguid/ato-benchmark-compare.git d290c8b77d5cc47346d7a41e843642c2c7908748 --squash`.
- Squash commit `965739bf4348b74987bd8541a996599bdaeba53b`; merge commit
  `f4289747daa83a79ee318d4405fd45c3ea9d6cd8`. `git rev-parse <merge>:packages/ato-benchmark-compare`
  equals the source tree.
- Imported files edited for location: none. The nested `.github/workflows/ci.yml`, `codeql.yml`
  and `release.yml`, `.github/dependabot.yml` and `tools/build_dataset.py` are inert records of the
  source repository; only root workflows are active.
- Checks run from `packages/ato-benchmark-compare/` immediately after import, as the source
  `ci.yml` defines: `uv run --locked --extra dev pytest -q` (279 passed);
  scoped branch coverage run and `coverage xml`; `pip-audit --local --strict` (no known
  vulnerabilities); `python -m build`; clean-wheel `show` and `compare` smoke (`31% to 38%` and
  `32.00%` present); shipped-sdist `pip install -e ".[dev]"` and `pytest -q`
  (276 passed, 3 skipped); `ruff check atobenchmark tests`; `mypy atobenchmark`;
  `uv lock --check`. All passed.
- Migration-context exception: `diff-cover coverage.xml --compare-branch=origin/main
  --branch-coverage --fail-under=100` exits 1 here because `origin/main` of this repository
  (`d6bf940cc6850ecb97c07035519167ed86e151ad`) predates the import, so every line of
  `atobenchmark/mapping.py` counts as changed and the whole file must reach 100 percent.
  Measured 96 percent branch-inclusive over the whole file (`coverage report`: 227 statements,
  5 missed, 100 branches, 4 partial, 97 percent). The check is unchanged; once `main` contains
  the package the comparison covers only changed lines again, as in the source repository.
