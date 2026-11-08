# 0001. Use `main` as the trunk and `production` as the release branch

- **Status:** Accepted
- **Date:** 2026-11-08
- **Issue:** #16

## Context

ReviewLens v0.1.0 was built on a single long-lived branch, `production`, which
was also the default branch. Feature work, dependency updates, and the 0.1.0
release preparation all merged into it, and CI ran only for it.

The project then adopted a pull request and code review workflow based on
trunk-based development. Work starts from an issue and lives on a short-lived
branch. It lands as a small, reviewed pull request that is squash-merged into a
trunk that is always releasable, and a separate branch holds the version in
production.

Constraints:

- Publishing to PyPI (`.github/workflows/publish.yml`) is triggered by a
  published GitHub release and builds from the release tag. It does not depend
  on any branch name.
- `pyproject.toml` links the changelog on `production`, and the open
  Dependabot pull requests had been opened against it.
- The repository has a single maintainer, so the process has to stay light.

## Decision

- We created `main` from `production` at commit `e9722df` and made it the
  default branch and the trunk. Every change reaches `main` through a pull
  request from a short-lived `feature/`, `fix/`, `chore/`, or `docs/` branch.
  Pull requests are squash-merged, with the pull request title
  (`type(scope): description (#issue)`) as the commit subject.
- We keep `production` as the release branch. It holds the most recently
  released version and changes only through a release pull request from
  `main`. That pull request is merged with a merge commit, not a squash, so
  `production` keeps the exact history of `main` and stays a descendant of it.
  Nothing is committed to `production` directly, and urgent fixes go through
  `main` first.
- A release is a `vX.Y.Z` tag on `production` plus a GitHub release.
  Publishing the release runs the unchanged `publish.yml`, which checks the tag
  against the package version and uploads to PyPI through trusted publishing.
- CI runs for pushes and pull requests on both branches. `main` is protected by
  a repository ruleset that requires a pull request, the CI and PR conventions
  status checks, and resolved conversations, and that blocks force pushes and
  deletion.

## Consequences

- Contributors, Dependabot, and the default branch all point to `main`, and
  `production` keeps its existing meaning. Links to `production`, such as the
  changelog URL in the package metadata, still show the released version.
- The publishing workflow and the PyPI trusted-publisher configuration need no
  changes.
- `main` reads as one Conventional Commit with an issue number per change,
  which makes history easy to follow and individual changes easy to revert.
- A release pull request shows exactly what changed since the last release,
  and promotion never conflicts as long as `production` only moves through
  these merges.
- There are two long-lived branches to keep green, and each release needs an
  extra pull request.
- The repository must allow both squash merges (for normal pull requests) and
  merge commits (for release pull requests), and maintainers must pick the
  right method. Squash-merging a release would detach `production` from
  `main`'s history and make the next release pull request conflict.
- Release tags point at merge commits on `production`, which are not ancestors
  of `main`. `git describe` on `main` does not see them. Use
  `git log vX.Y.Z..main` to list unreleased changes.
- Version numbers pinned in CI, tests, and docs must be bumped on `main` before
  promotion, because `publish.yml` rejects a tag that does not match the
  package version.

## Alternatives considered

- **Keep `production` as the trunk and document the mapping.** This would have
  been the least disruptive option. However, `production` would then carry
  unreleased work under a name that suggests the opposite, and no branch would
  show the released version.
- **Rename `production` to `main` and add a new `release` branch.** This
  matches the workflow's default names, but it would have broken existing
  links, the base branch of open pull requests, and existing clones and forks.
  It would also have reused a familiar branch name with a different meaning.
- **Squash-merge release pull requests into `production`.** This keeps
  `production` history short, but `production` would stop being a descendant of
  `main`. Every later release pull request would then show already-released
  commits and risk conflicts.
