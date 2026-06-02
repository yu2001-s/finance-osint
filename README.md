# Finance OSINT

Finance OSINT is a local-first, git-native evidence graph for retail investors.

The repo is the canonical database. Contributors pull it, add structured data locally, validate it, and submit changes by pull request. There is no server, hosted database, private moderation layer, or hidden agent state.

## Core Layers

```text
Source -> Dataset -> Evidence -> Metric/Event/Claim -> Relationship -> Thesis
                              -> Validation/Challenge
```

- `sources/`: provenance metadata for filings, transcripts, pages, datasets, meetings, and observations.
- `evidence/`: exact excerpts, locators, observations, or first-hand reports tied to sources.
- `claim-predicates/`: registered claim predicate vocabulary.
- `metric-definitions/`: registered metric vocabulary.
- `metrics/`: structured numeric observations with provenance.
- `events/`: structured time-bound occurrences or expected occurrences.
- `datasets/`: metadata about source datasets.
- `claims/`: narrow checkable statements backed by evidence.
- `validations/`: append-only review records that evaluate support.
- `challenges/`: append-only unresolved objections about evidence quality, scope, ontology, materiality, or missing support.
- `relationships/`: rich typed graph relationships derived from claims or evidence.
- `theses/`: interpretations, forecasts, or arguments built from evidence, claims, metrics, events, datasets, and relationships.
- `relationship-types/`: the graph ontology. Registered types are canonical; provisional types must declare their proposed definition.
- `schemas/`: JSON Schemas enforced locally and in CI.

Examples are separate from canonical data. Prototype debate examples live under
`examples/deferred/`; copyable full corpus examples live under
`examples/corpus/`. Normal `fo` commands do not load those records.

## Quick Start

```bash
uv sync
uv run fo lint
uv run fo lint --json
uv run fo index build --json
uv run fo graph build
```

Generated graph files go into `.local/` and are intentionally ignored by git.

If you cannot use `uv`, the fallback is:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
fo lint
```

## Contribution Policy

Evidence is the strict layer. Claims, relationships, theses, validations, and challenges can be contested, but they must preserve their dependency chain.

- Public evidence should be source-backed and reviewable.
- First-hand evidence must declare access, attribution, public status, and risk flags.
- Anonymous or internal-source reports can be recorded, but remain visibly low-trust unless independently supported.
- Claims use `support_type` to describe reasoning distance from evidence.
- Relationship types must be registered or marked `provisional:` with a proposed type definition.
- Relationship participants, scope, materiality, and qualifiers must fit the selected relationship type.
- Canonical records do not store truth `status` or `confidence`; tools derive review state locally.

## Local Commands

```bash
uv run fo lint                 # validate schemas, references, and ontology usage
uv run fo lint --json          # machine-readable lint output for agents/CI
uv run fo index build --json   # build .local/index.sqlite from YAML
uv run fo search exdev --json  # search indexed records
uv run fo context RECORD --json
uv run fo review RECORD --json
uv run fo diff-review main --json
uv run fo graph build          # build .local/graph.json from current repo data
uv run fo graph neighbors RECORD --json
uv run fo graph inspect exdev  # find graph records mentioning a string
```

`fo review` is the deterministic truth-surface command. It does not decide
truth. It derives a local label and supporting details from evidence classes,
source independence, validation dependency paths, open challenges,
contradictions, supersession, stale markers, and low-trust/private evidence.

`fo diff-review BASE` compares the current working tree against a Git base ref
and summarizes repo-native PR impact: record deltas, validation errors, evidence
mutations, reference impact, derived review-state movement, graph edge changes,
ontology changes, and deterministic warnings. Warnings are review pressure;
schema/reference failures are hard errors.

## Deterministic Write Helpers

`fo new` creates valid YAML from explicit inputs only. It does not fetch sources,
summarize documents, infer claims, or decide truth.

```bash
uv run fo new claim \
  --statement "EXDEV uses FNDWY for the X1 processor." \
  --subject entity:company:exdev \
  --predicate disclosed_relationship \
  --object entity:company:fndwy \
  --support-type direct \
  --evidence evidence:synthetic:exdev-fy2025-supplier-note \
  --submitted-by github:username \
  --json
```

Supported constructors:

```text
fo new entity
fo new source
fo new evidence
fo new claim
fo new metric
fo new event
fo new dataset
fo new validation
fo new challenge
fo new relationship
fo new thesis
```

## Agent Skills

`AGENTS.md` is a small router for humans and agents. Task-specific workflows
live under `agent-skills/`:

```text
operate-repo
add-evidence
add-claim
add-relationship
validate-or-challenge
write-thesis
```

These skills teach agents how to use deterministic `fo` commands. They are not
canonical data and do not create hidden agent state.
