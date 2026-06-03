# Documentation

This directory is the stable user and contributor documentation for Finance
OSINT. It explains how to use the repository, how the ontology works, and how to
make reviewable contributions.

## Start Here

- `../README.md`: project overview and quick commands.
- `../CONTRIBUTING.md`: pull-request rules and validation checks.
- `first-pr-quickstart.md`: a small first contribution workflow.
- `data-model.md`: record kinds, dependency layers, and canonical paths.
- `ontology.md`: claim predicates, metric definitions, relationship types, and
  proposal rules.
- `research-batch-contribution.md`: source-backed research batch workflow.
- `contracts.md`: CLI, schema, ID, archive, and generated-artifact contracts.
- `governance.md`: review, disputes, abuse boundaries, and merge criteria.
- `maintenance.md`: maintainer commands and generated review artifacts.

## Canonical Data

Canonical current data lives in:

```text
records/
ontology/
schemas/
templates/
```

Archived canonical data, when present, lives under:

```text
archive/records/
archive/ontology/
```

Generated local state lives under `.local/` and must not be committed.
Examples, deferred prototypes, and test fixtures are not loaded by normal
`fo` commands.

## Reading The Repo

Use the same flow for human reading and agent work:

```bash
uv run fo lint --json
uv run fo index build --json
uv run fo search QUERY --json
uv run fo context RECORD_ID --json
uv run fo review RECORD_ID --chain --json
uv run fo graph neighbors RECORD_ID --json
```

`fo review` and `fo diff-review` derive local review state. They do not write
truth labels back to canonical records.

## Writing The Repo

Add records in dependency order:

```text
entity
source
evidence
metric / event / dataset
claim
relationship
question / challenge / validation
thesis
```

If support is incomplete, keep the record narrow and add a question or
challenge. Do not encode investment truth as canonical `status`, `confidence`,
or hidden reviewer notes.

## Example Corpora

`examples/corpus/` contains fictional copyable examples. They demonstrate record
shape and contribution patterns, but they are not canonical market data and
should not be cited by real research records.
