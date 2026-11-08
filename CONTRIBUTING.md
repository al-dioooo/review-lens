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

## Contribution workflow

Every change takes the same path: an issue, a short-lived branch, small
commits, a reviewed pull request, and a squash merge into `main`.

### 1. Start with an issue

Before writing code, find or open an issue that states the problem and the
approach you plan to take. For anything beyond a typo, wait until a maintainer
has agreed to the approach on the issue. This avoids duplicate work and
changes that do not fit the project's scope. The issue number is the ticket ID
in the pull request title.

### 2. Branch from `main`

ReviewLens uses trunk-based development with two long-lived branches:

| Branch | Role |
| --- | --- |
| `main` | Trunk and default branch. It is always releasable, and every change lands here through a pull request. |
| `production` | Release branch. It holds the most recently released version and only moves through a release pull request from `main` (see [Releases](#releases)). |

Never commit directly to `main` or `production`. Create a short-lived branch
from the current `main` and name it after the kind of change:

| Branch name | Use for |
| --- | --- |
| `feature/<short-description>` | New behavior |
| `fix/<bug-description>` | Bug fixes |
| `chore/<maintenance>` | Maintenance, CI, tooling, and dependencies |
| `docs/<topic>` | Documentation-only changes |

To contribute from a fork, fork `al-dioooo/review-lens` through GitHub, clone
your fork using the URL shown on its page, and add the upstream repository so
you can branch from its current `main`:

```bash
git remote add upstream https://github.com/al-dioooo/review-lens.git
git fetch upstream
git switch -c feature/short-description upstream/main
```

### 3. Commit in small steps

- Make each commit one logical change that you can describe in one sentence,
  usually about 5–100 changed lines. Keep a refactor separate from a feature,
  and a fix separate from reformatting.
- Commit whenever a function, a fix, or a logical step is done, roughly every
  15–60 minutes of active coding. Avoid large commits and "WIP" commits on a
  shared branch.
- Write messages in [Conventional Commits](https://www.conventionalcommits.org/)
  format, `type(scope): description`, for example
  `fix(ingestion): reject NUL bytes in CSV headers`. Use `feat`, `fix`,
  `refactor`, `docs`, `chore`, `test`, `ci`, `build`, `perf`, `style`, or
  `revert`; the scope is optional. Mark a breaking change with `!`, as in
  `feat(api)!: change the result format`.
- Run the [quality checks](#tests-and-quality-checks) before every commit.

### 4. Open a pull request into `main`

- **Title:** a Conventional Commit followed by the issue number,
  `type(scope): description (#<issue>)`, for example
  `fix(ingestion): reject NUL bytes in CSV headers (#42)`. The title becomes
  the commit subject on `main`.
- **Description:** follow the
  [pull request template](.github/PULL_REQUEST_TEMPLATE.md) (Summary, Problem,
  Solution, Test Evidence, Deployment Prerequisite / Breaking Changes, and
  Notes) and link the issue with `Closes #<issue>`. For library, CLI, and
  documentation changes, the test evidence is the commands you ran and their
  results; add screenshots when chart or workbook output changes. Call out any
  privacy or compatibility impact.
- **Size:** solve one problem per pull request and aim for fewer than about 500
  changed lines. Split larger work into stacked pull requests, a chain of small
  pull requests where each one builds on the previous one and they are reviewed
  and merged in order.
- Update documentation and tests with every behavior change, and add a
  `CHANGELOG.md` entry under `[Unreleased]` for user-visible changes.

### 5. Review

- Reviewers check correctness (including edge cases), readability, fit with
  the architecture, meaningful tests, and updated documentation.
- Reviewers start each comment with `required:` for changes that must be
  addressed before merge, or `nit:` for optional suggestions. They explain the
  reasoning behind each comment and ask a question rather than guess when
  something is unclear. Trivial issues do not block a merge.
- Authors respond to every comment: fix it, ask for clarification, or explain
  why they disagree. Do not apply a fix you do not understand. Push follow-ups
  as new commits, then re-request review and point out what changed.

### 6. Merge

A maintainer merges a pull request only when:

- all CI checks pass (a red pull request is never merged);
- every review conversation is resolved;
- the review is done and recorded on the pull request; and
- the title follows the format above.

Pull requests are squash-merged into `main` with the pull request title as the
commit subject, so `main` reads as one Conventional Commit with its issue
number per change:

```bash
gh pr merge <number> --squash --delete-branch --subject "<pull request title>"
```

## Tests and quality checks

Run the smallest relevant test while developing. For example:

```bash
uv run pytest tests/unit/test_ingestion.py -q
```

Before every commit, run the complete local gates. They match the checks in
CI:

```bash
uv sync --all-groups --locked
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
uv run pytest --cov=reviewlens --cov-fail-under=90
```

Coverage must remain at least 90%. When changing packaging or the CLI, also
build the distributions and exercise the installed command in an isolated
environment.

## Code conventions

- Add type hints to all public interfaces and document public behavior.
- Prefer immutable configuration and explicit stage boundaries.
- Keep library calls quiet; return structured diagnostics for non-fatal
  conditions and use the public exception hierarchy for fatal conditions.
- Preserve deterministic ordering and seeded behavior.
- Use Ruff for linting and formatting; do not hand-format around it.

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

## Releases

Maintainers release from `main` when it holds the changes to ship. ReviewLens
follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

1. **Prepare the version on `main`.** Open an issue and a
   `chore(release): prepare vX.Y.Z (#<issue>)` pull request that moves the
   `[Unreleased]` entries in `CHANGELOG.md` under a new `[X.Y.Z]` heading and
   bumps the version everywhere it is pinned: `pyproject.toml`,
   `src/reviewlens/__init__.py`, `uv.lock` (run `uv lock`), and the version
   assertions in `.github/workflows/ci.yml`, the tests, and the docs.
   `git grep -n "<previous version>"` finds them. Merge it like any other pull
   request.
2. **Promote `main` to `production`.** Open a release pull request from `main`
   into `production` with the same issue number, wait for CI, and merge it with
   a **merge commit**, not a squash. A merge commit keeps the exact `main`
   history on `production`, so `production` stays a descendant of `main` and
   the next release pull request merges cleanly. Never delete the head branch
   of this pull request.

   ```bash
   gh pr create --base production --head main --title "chore(release): vX.Y.Z (#<issue>)"
   gh pr merge <number> --merge
   ```

3. **Tag and publish.** Create a GitHub release with a new `vX.Y.Z` tag on
   `production`, using the `CHANGELOG.md` section as the release notes:

   ```bash
   gh release create vX.Y.Z --target production --title vX.Y.Z --notes-file notes.md
   ```

   Publishing the release runs `.github/workflows/publish.yml`. It checks that
   the tag equals `v` plus the package version, builds and validates the
   distributions, and uploads them to PyPI through trusted publishing in the
   `pypi` environment. No PyPI token is stored in the repository.

Urgent fixes take the same path: a `fix/...` pull request into `main`, then a
release. `production` never receives changes that are not already on `main`.

## Reporting security issues

Do not open a public issue for a suspected vulnerability. Follow
[SECURITY.md](SECURITY.md) so the maintainer can coordinate a safe resolution.
