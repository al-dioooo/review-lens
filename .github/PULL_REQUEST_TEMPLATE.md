## Summary

Describe the user-visible or internal change.

## Verification

- [ ] Focused tests pass.
- [ ] `uv run ruff check .` passes.
- [ ] `uv run ruff format --check .` passes.
- [ ] `uv run mypy src tests` passes.
- [ ] `uv run pytest --cov=reviewlens --cov-fail-under=90` passes.
- [ ] No private, production, credential, or legacy-project data was added.
- [ ] Documentation and CHANGELOG were updated when behavior changed.
