# Architecture decision records

This directory is the ReviewLens decision log. An architecture decision record
(ADR) captures one significant decision: its context, the decision itself, and
its consequences. Later contributors can then see why the project works the
way it does without reconstructing old discussions.

## When to write one

Write an ADR when a change:

- alters a public contract, such as the Python API, the CLI, the workbook
  layout, the input data format, or the supported Python and platform range;
- adds or replaces a core dependency or algorithm;
- changes how the project is built, tested, branched, or released; or
- makes a trade-off that reviewers are likely to question later.

Small, easily reversed choices belong in the pull request description instead.

## How to add one

1. Copy [template.md](template.md) to `NNNN-short-title.md`, using the next
   free four-digit number.
2. Open an issue and a pull request for it like any other change, for example
   `docs(adr): record the export format decision (#42)`. The status starts as
   `Proposed`. Change it to `Accepted` in the same pull request once reviewers
   agree, before it merges.
3. Add the record to the index below.
4. Do not rewrite an accepted ADR. To change a decision, write a new ADR and
   mark the old one `Superseded by NNNN`.

## Index

No decisions have been recorded yet.
