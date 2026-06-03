# Finance OSINT

Finance OSINT is a local-first, git-native evidence graph for retail investors.

The repo is the canonical database. Contributors pull it, add structured data locally, validate it, and submit changes by pull request. There is no server, hosted database, private moderation layer, or hidden agent state.

Licensed under the Apache License, Version 2.0. The repository is public alpha
infrastructure; the `v0.1.0-alpha` tag has not been cut yet.

## Core Layers

```text
Source -> Dataset -> Evidence -> Metric/Event/Claim -> Relationship -> Thesis
                              -> Validation/Challenge/Question
```

- `records/sources/`: provenance metadata for filings, transcripts, pages, datasets, meetings, and observations.
- `records/evidence/`: exact excerpts, locators, observations, or first-hand reports tied to sources.
- `ontology/claim-predicates/`: registered claim predicate vocabulary.
- `ontology/metric-definitions/`: registered metric vocabulary.
- `records/metrics/`: structured numeric observations with provenance.
- `records/events/`: structured time-bound occurrences or expected occurrences.
- `records/datasets/`: metadata about source datasets.
- `records/claims/`: narrow checkable statements backed by evidence.
- `records/validations/`: append-only review records that evaluate support.
- `records/challenges/`: append-only unresolved objections about evidence quality, scope, ontology, materiality, or missing support.
- `records/questions/`: open proof gaps or next investigation targets for humans and agents.
- `records/relationships/`: rich typed graph relationships derived from claims or evidence.
- `records/theses/`: interpretations, forecasts, or arguments built from evidence, claims, metrics, events, datasets, and relationships.
- `ontology/relationship-types/`: the graph ontology. Registered types are canonical; provisional types must declare their proposed definition.
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

Finance OSINT treats contributors and readers as adults. The repo does not
block unusual, speculative, low-trust, promotional, bearish, bullish, or
disputed research views merely because they are uncertain or unpopular. It
requires honest labels: provenance, evidence class, source perspective, source
attribution, support type, risk flags, and open objections must be visible so
readers can decide for themselves.

Atomic contributions are welcome. A PR may add one useful point, such as one
source, one evidence record, one claim tied to existing evidence, one question,
one challenge, one validation, one entity, one metric, or one event. Full
source-to-thesis chains are useful, but they are not required. Each record only
needs to satisfy the dependencies required by its own type, and any missing
downstream proof should be visible as a question, challenge, risk flag, or PR
note.

For a concrete sourced-research batch workflow, see
`docs/research-batch-contribution.md`.

For the public docs/wiki entry point, start with `docs/README.md`.

For release status, lightweight governance, review rubrics, and GitHub launch
guardrails, see:

- `docs/README.md`
- `docs/release-readiness.md`
- `docs/governance.md`
- `docs/review-rubric.md`
- `docs/github-public-launch-checklist.md`
- `docs/first-pr-quickstart.md`

- Public evidence should be source-backed and reviewable.
- New sources should declare `source_perspective` so review output can separate
  company-originated, independent, social, first-hand, anonymous, internal, and
  fixture sources without changing the underlying evidence.
- First-hand evidence must declare access, attribution, public status, and risk flags.
- Anonymous, internal-source, rumor, social, first-hand, or unverifiable reports
  can be recorded, but remain visibly low-trust unless independently supported.
- Claims use `support_type` to describe reasoning distance from evidence.
- Questions are investigation tasks, not truth status. Resolve them by linking evidence, claims, relationships, or theses.
- Relationship types must be registered or marked `provisional:` with a proposed type definition.
- Relationship participants, scope, materiality, and qualifiers must fit the selected relationship type.
- Canonical records do not store truth `status` or `confidence`; tools derive review state locally.

## Local Commands

```bash
uv run fo lint                 # validate schemas, references, and ontology usage
uv run fo lint --json          # machine-readable lint output for agents/CI
uv run fo index build --json   # build .local/index.sqlite from YAML
uv run fo search axt --json    # search indexed records
uv run fo context RECORD --json
uv run fo review RECORD --json
uv run fo diff-review main --json
uv run fo graph build          # build .local/graph.json from current repo data
uv run fo graph neighbors RECORD --json
uv run fo graph inspect axt    # find graph records mentioning a string
uv run fo view build main      # build .local/github-view markdown for GitHub PR review
```

`fo review` is the deterministic truth-surface command. It does not decide
truth. It derives a local label and supporting details from evidence classes,
source independence and source perspective, validation dependency paths, open challenges,
contradictions, supersession, stale markers, and low-trust/private evidence.
Use `fo review RECORD --chain --json` when reviewing a thesis or PR-sensitive
record end to end; it adds a compact source-to-claim chain summary with
dependency counts, source/evidence mix, relationship types, open questions,
open challenges, and risk-flag categories such as social/media, market data,
compiled research, and relationship-promotion pressure.

`fo diff-review BASE` resolves `BASE` to a Git commit SHA, compares the current
working tree against that commit, and summarizes repo-native PR impact: record
deltas, validation errors, evidence mutations, reference impact, derived
review-state movement, graph edge changes, ontology changes, and deterministic
warnings. Warnings are review pressure; schema/reference failures are hard
errors.

`fo lint` also emits advisory `possible_duplicate_*` warnings for current
records that share deterministic signatures such as entity identifiers, source
URLs, evidence locators, claim structure, or relationship structure. These do
not fail lint; contributors should either clarify the distinction or merge and
archive one record with `duplicate_of` or `superseded_by`.

## Supply-Chain Ontology

Prefer precise relationship types when the evidence supports them. The initial
supply-chain set includes:

- `supplier_relationship` / `customer_relationship`: broad buyer-seller edges.
- `qualified_supplier`: supplier approval or qualification by a buyer/OEM.
- `design_win`: designed-in product, component, technology, or service.
- `capacity_expansion_for`: capacity tied to output, market, customer, or time window.
- `uses_component`: product/architecture/component composition or dependency.
- `substitutes_for`: functional or economic substitution.
- `manufacturing_partner`: foundry, contract manufacturing, assembly, packaging, or test.

Use broad relationship types only when the source does not support a narrower
edge. Use `provisional:` for genuinely new relationship semantics.

## Source Preservation

Mutable web-like sources should not rely on `url` alone. Prefer `archive_url`.
If no archive exists, preserve the source with at least one of:

- bounded `evidence.excerpt`
- source `content_hash`
- small referenced `source_artifacts`

Local source artifacts must live under `artifacts/sources/`, must be referenced
by a source or evidence record, must be `png`, `jpg`, `jpeg`, or `pdf`, and must
stay under 2 MB per file. `fo lint` warns for mutable web sources without a
preservation path and fails hard on invalid artifact files.

## Archive Policy

Archive is path-level lifecycle state. Current records live under `records/`;
current ontology registries live under `ontology/`. Archived records live under
`archive/records/` or `archive/ontology/` and keep their canonical ID.

Archived records must include at least one of `superseded_by`, `duplicate_of`,
or `archive_reason`. Current records must not depend on archived records by
default; point them at a current replacement instead. `fo diff-review` warns
when a PR adds or moves records under `archive/`.

## Deterministic Write Helpers

`fo new` creates valid YAML from explicit inputs only. It does not fetch sources,
summarize documents, infer claims, or decide truth.

```bash
uv run fo new claim \
  --statement "AXT discloses indium phosphide substrate products." \
  --subject entity:company:axt-inc \
  --predicate product_signal \
  --object entity:component:indium-phosphide-substrate \
  --support-type direct \
  --evidence evidence:public:axt:fy2025-inp-products \
  --submitted-by github:username \
  --dry-run \
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
fo new question
fo new relationship
fo new thesis
```

## Agent Skills

`AGENTS.md` is a small router for humans and agents. Task-specific workflows
live under `agent-skills/`:

```text
operate-repo
add-entity
add-evidence
add-claim
add-metric-event-dataset
add-relationship
validate-or-challenge
add-question
write-thesis
propose-ontology
migrate-stock-research
```

These skills teach agents how to use deterministic `fo` commands. They are not
canonical data and do not create hidden agent state.

## License

Finance OSINT is licensed under the Apache License, Version 2.0. See `LICENSE`.
