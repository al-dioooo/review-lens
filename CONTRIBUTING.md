# Contributing to ReviewLens

Thank you for helping improve ReviewLens. Contributions should preserve its
deterministic, Indonesian-first, local analysis scope and its transparent data
contracts. By participating, you agree to follow the
[Code of Conduct](CODE_OF_CONDUCT.md).

## Development setup

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), enter your
checkout, and synchronize the exact locked development environment:

```bash
uv sync --all-groups --locked
```

ReviewLens requires Python 3.11 or newer. The committed lockfile is the source
of exact development dependency versions; do not edit it by hand.

## Fork and branch workflow

1. Fork `al-dioooo/review-lens` through GitHub and clone your fork using the URL
   shown on its page.
2. Add the upstream repository if you need to synchronize your fork.
3. Create a focused branch from the current `production` branch:

   ```bash
   git switch -c feat/short-description
   ```

4. Keep the change narrowly scoped, update documentation, and add tests for
   behavior changes.
5. Run the quality checks below before opening a pull request.
6. Explain the user-visible behavior, testing performed, and any privacy or
   compatibility impact in the pull request.

## Tests and quality checks

Run the smallest relevant test while developing. For example:

```bash
uv run pytest tests/unit/test_ingestion.py -q
```

Before submitting, run the complete local gates:

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy
```

Coverage must remain at least 90%. When changing packaging or the CLI, also
build the distributions and exercise the installed command in an isolated
environment.

## Code and commit conventions

- Add type hints to all public interfaces and document public behavior.
- Prefer immutable configuration and explicit stage boundaries.
- Keep library calls quiet; return structured diagnostics for non-fatal
  conditions and use the public exception hierarchy for fatal conditions.
- Preserve deterministic ordering and seeded behavior.
- Use Ruff for linting and formatting; do not hand-format around it.
- Use conventional commit prefixes: `feat:`, `fix:`, `docs:`, `test:`,
  `refactor:`, or `chore:`.

## Data, privacy, and clean-room rules

Tests and examples must use newly authored synthetic Indonesian review data.
Do not commit data about real people or businesses, copied reviews, URLs,
credentials, local datasets, generated reports, or other private material.

ReviewLens is a clean-room implementation. Do not copy, mechanically translate,
or adapt source code, datasets, output artifacts, credentials, names, or
venue-specific behavior from any earlier or unrelated project. Implement from
the public requirements, the approved design, and ReviewLens's own interfaces.

Contributions must stay inside the current product scope: local analysis of
user-provided CSV or JSON files. Scrapers, hosted services, external or local
generative AI, runtime downloads, dashboards, plugin systems, and MCP behavior
are outside v0.1.x.

## Reporting security issues

Do not open a public issue for a suspected vulnerability. Follow
[SECURITY.md](SECURITY.md) so the maintainer can coordinate a safe resolution.
