<!--
Title format: type(scope): description (#issue)
Example:      fix(ingestion): reject NUL bytes in CSV headers (#42)
Types:        feat, fix, refactor, docs, chore, test, ci, build, perf, style, revert
Add ! before the colon for a breaking change, e.g. feat(api)!: ...
-->

Closes #

## Summary

<!-- Brief description of the change. -->

## Problem

<!-- What issue or limitation this PR addresses. -->

## Solution

<!-- How the change solves the problem. -->

## Test Evidence

<!--
Paste the commands you ran and their results. For changes to charts or
workbook output, also attach screenshots covering the normal flow and some
edge cases.
-->

## Deployment Prerequisite / Breaking Changes

<!--
Public API or CLI changes, removed functions, new or changed dependencies,
configuration or workflow changes, or anything else that must happen before
release. Write "None" if nothing is needed.
-->

## Notes

<!-- Additional context, and what reviewers should focus on. -->

## Checklist

- [ ] The title follows Conventional Commits and ends with the issue number, e.g. `(#42)`.
- [ ] The issue is linked above with `Closes #<issue>`.
- [ ] Focused tests pass.
- [ ] `uv sync --all-groups --locked` succeeds.
- [ ] `uv run ruff check .` passes.
- [ ] `uv run ruff format --check .` passes.
- [ ] `uv run mypy src tests` passes.
- [ ] `uv run pytest --cov=reviewlens --cov-fail-under=90` passes.
- [ ] No private, production, credential, or legacy-project data, `.env` files, or logs were added.
- [ ] Documentation and CHANGELOG were updated when behavior changed.
