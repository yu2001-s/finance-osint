# Finance OSINT

Finance OSINT is a local-first evidence graph for public-market research. The
repository is the database: contributors add YAML records, validate them
locally, and submit changes by pull request.

The project stores provenance, evidence, structured observations, graph
relationships, review pressure, and theses. It does not store canonical truth
status, confidence scores, hidden moderation decisions, or private agent state.
Review state is derived locally from the records.

## Repository Map

```text
records/       Canonical source, evidence, metric, event, claim, relationship,
               validation, challenge, question, entity, dataset, and thesis data.
ontology/      Registered and proposed claim predicates, relationship types,
               and metric definitions.
schemas/       JSON Schemas for every canonical record kind.
templates/     Copyable YAML templates.
fosint/        The `fo` command-line tool.
scripts/       CI and maintainer validation helpers.
docs/          User and contributor documentation.
examples/      Fictional example corpora and deferred prototypes.
tests/         Unit tests and synthetic fixtures.
```

Only `records/` and `ontology/` are canonical data. Files under `.local/`,
`examples/`, and `tests/fixtures/` are generated, illustrative, or test-only.

## Data Flow

```text
Source -> Dataset -> Evidence -> Metric / Event / Claim -> Relationship -> Thesis
                                -> Validation / Challenge / Question
```

Start from sources and evidence. Promote stronger objects only when the support
chain justifies them. If the chain is incomplete, record the gap as a question,
challenge, scoped claim, or thesis limitation rather than stretching the data.

## Quick Start

Install the local tooling:

```bash
uv sync
```

Validate and build local read artifacts:

```bash
uv run fo lint --json
uv run fo index build --json
uv run fo graph build --json
```

Search and inspect records:

```bash
uv run fo search axt --json
uv run fo context entity:company:axt-inc --json
uv run fo review thesis:axt-sumitomo:inp-substrate-bottleneck-watch --chain --json
uv run fo graph neighbors entity:company:axt-inc --json
```

Generated files are written under `.local/` and are ignored by git.

If you cannot use `uv`:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
fo lint --json
```

## Contributing

Atomic contributions are welcome. A useful pull request can add one source, one
piece of evidence, one metric, one claim, one relationship, one question, one
challenge, or one validation.

Before opening a pull request, run:

```bash
uv run fo lint --json
uv run python -m unittest discover -s tests
uv run fo index build --json
uv run fo graph build --json
uv run fo diff-review BASE --json
uv run fo view build BASE --json
```

Use `BASE` as the branch point or pull-request base, for example `main` or
`origin/main`.

New canonical records must use your GitHub identity:

```yaml
submitted_by: github:your-login
```

See `CONTRIBUTING.md` and `docs/research-batch-contribution.md` for the full
workflow.

## Documentation

Start with `docs/README.md`.

The stable docs cover:

- first-time setup and first PRs
- the record model and ontology
- how to author source-backed research batches
- CLI commands and schema contracts
- review, governance, archive, and dispute handling
- maintainer checks and generated artifacts

## Non-Goals

Finance OSINT is not an investment recommendation service, a hosted database, a
moderation backend, a private expert network, or an agent memory store. The repo
keeps the evidence chain visible so readers can evaluate the work themselves.

## License

Finance OSINT is licensed under the Apache License, Version 2.0. See `LICENSE`.
