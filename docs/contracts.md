# CLI And Schema Contracts

This page documents the stable implementation contracts contributors need when
using the repository.

## Canonical State

Canonical state is:

```text
records/**/*.yml
ontology/**/*.yml
schemas/*.schema.json
templates/*.yaml.template
Git history
```

Derived state is rebuildable:

```text
.local/index.sqlite
.local/graph.json
.local/github-view/
```

Derived state must not become the write source of truth.

## Schema Version

Every canonical YAML record includes:

```yaml
schema_version: 1
```

Version `1` is the public contract version used by the current schemas.

## Required Fields

Current schema-required fields:

| Kind | Required fields |
| --- | --- |
| `entity` | `schema_version`, `kind`, `id`, `entity_type`, `name` |
| `source` | `schema_version`, `kind`, `id`, `source_type`, `title`, `public_status`, `source_perspective`, `accessed_at`, `content_mode` |
| `evidence` | `schema_version`, `kind`, `id`, `evidence_class`, `source`, `summary`, `content_mode`, `submitted_by`, `observed_at`, `source_attribution` |
| `dataset` | `schema_version`, `kind`, `id`, `title`, `dataset_type`, `publisher`, `coverage`, `access`, `sources`, `content_mode` |
| `metric` | `schema_version`, `kind`, `id`, `entity`, `metric_definition`, `value`, `unit`, `period`, `value_basis`, `evidence`, `submitted_by` |
| `event` | `schema_version`, `kind`, `id`, `event_type`, `event_state`, `title`, `entities`, `evidence`, `submitted_by` |
| `claim` | `schema_version`, `kind`, `id`, `statement`, `subject`, `predicate`, `support_type`, `evidence`, `submitted_by` |
| `relationship` | `schema_version`, `kind`, `id`, `type`, `participants`, `derived_from`, `submitted_by` |
| `question` | `schema_version`, `kind`, `id`, `question`, `entities`, `proof_type`, `priority`, `submitted_by` |
| `challenge` | `schema_version`, `kind`, `id`, `target`, `submitted_by`, `challenge_type`, `summary` |
| `validation` | `schema_version`, `kind`, `id`, `target`, `submitted_by`, `verdict`, `summary`, `depends_on` |
| `thesis` | `schema_version`, `kind`, `id`, `title`, `summary`, `depends_on`, `submitted_by` |
| `claim_predicate` | `schema_version`, `kind`, `id`, `name`, `state`, `ontology_version` |
| `metric_definition` | `schema_version`, `kind`, `id`, `name`, `state`, `ontology_version` |
| `relationship_type` | `schema_version`, `kind`, `id`, `label`, `description`, `state`, `ontology_version`, `directional`, `roles` |

Schemas are the final authority. Run `uv run fo lint --json` after edits.

## CLI Commands

Validation:

```bash
uv run fo lint --json
uv run fo lint --current-only --json
```

Constructors:

```bash
uv run fo new entity --help
uv run fo new source --help
uv run fo new evidence --help
uv run fo new metric --help
uv run fo new event --help
uv run fo new dataset --help
uv run fo new claim --help
uv run fo new relationship --help
uv run fo new question --help
uv run fo new challenge --help
uv run fo new validation --help
uv run fo new thesis --help
```

Local read artifacts and queries:

```bash
uv run fo index build --json
uv run fo search QUERY --json
uv run fo context RECORD_ID --json
uv run fo review RECORD_ID --chain --json
uv run fo graph build --json
uv run fo graph neighbors RECORD_ID --json
uv run fo graph inspect TERM
```

PR review:

```bash
uv run fo diff-review BASE --json
uv run fo view build BASE --json
uv run fo view build BASE --check --json
```

## IDs And References

Record IDs are explicit strings with stable prefixes, for example:

```text
entity:company:axt-inc
source:public:axt:fy2025-form-10-k
evidence:public:axt:fy2025-inp-products
claim:axt:makes-inp-substrates
relationship:axt:manufactures-inp-substrates
thesis:axt-sumitomo:inp-substrate-bottleneck-watch
```

References must point to existing IDs. `fo lint` validates references,
duplicates, ontology usage, archive dependencies, artifact paths, and schema
shape.

## Banned Or Misused Fields

Do not add hidden agent provenance or canonical truth labels:

```text
status
confidence
generated_by
agent_run
model
prompt
completion_id
trace_id
hidden reviewer notes
```

Use `submitted_by` for contribution accountability and structured records for
support, dispute, freshness, supersession, or withdrawal.

Do not use `author` for contribution ownership. Lint rejects `author` on
claim, relationship, thesis, metric, event, dataset, evidence, validation,
challenge, and question records. If a source document has a content author,
represent that as source metadata or attribution, not submitter identity.

## Archive Contract

Archive is path-level lifecycle state. Archived records move under:

```text
archive/records/
archive/ontology/
```

Archived records keep their canonical ID and include at least one of:

```text
superseded_by
duplicate_of
archive_reason
```

Current records should not depend on archived records unless the link is a
lifecycle relationship such as `supersedes`, `corrects`, `restates`, `narrows`,
`broadens`, or `contradicts`.

## Source Artifact Contract

Local source artifacts:

- must live under `artifacts/sources/`
- must be referenced by a source or evidence record
- must use `png`, `jpg`, `jpeg`, or `pdf`
- must be 2 MB or smaller per file

Use artifacts only when source preservation cannot be handled by archive URLs,
content hashes, or bounded excerpts.
