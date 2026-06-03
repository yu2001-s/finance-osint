# Data Model

Finance OSINT is a YAML evidence graph. The record model separates provenance,
observations, assertions, graph edges, review pressure, and interpretation so
readers can inspect the support chain.

## Public Record Kinds

Current v1 record kinds are:

```text
entity
source
evidence
dataset
metric
event
claim
validation
challenge
question
relationship
thesis
claim_predicate
metric_definition
relationship_type
```

Deferred debate prototypes under `examples/deferred/` are not part of the
current public data model.

## Dependency Layers

```text
Source -> Dataset -> Evidence -> Metric / Event / Claim -> Relationship -> Thesis
                                -> Validation / Challenge / Question
```

Use the lower layer when possible. A source-backed number belongs in a metric,
not only in prose. A purchase order or expected ramp belongs in an event. A
supplier, customer, design-win, qualification, or manufacturing edge belongs in
a relationship only when the support chain justifies that exact edge.

## Canonical Paths

Current records live under:

```text
records/entities/
records/sources/
records/evidence/
records/datasets/
records/metrics/
records/events/
records/claims/
records/validations/
records/challenges/
records/questions/
records/relationships/
records/theses/
```

Ontology records live under:

```text
ontology/claim-predicates/
ontology/metric-definitions/
ontology/relationship-types/
```

Archived records keep their canonical ID and move under `archive/records/` or
`archive/ontology/`.

## Record Boundaries

`entity`
  A company, person, product, component, security, listing, market, geography,
  architecture, facility, manufacturing process, commodity, technology,
  regulation, fund, or service.

`source`
  Provenance metadata for a filing, report, transcript, product page, dataset,
  article, public post, meeting, field observation, anonymous report, internal
  report, or other source.

`evidence`
  A bounded excerpt, table, row, locator, observation, translated passage,
  OCR-derived passage, or source-backed report. Evidence is the strict support
  layer.

`dataset`
  Metadata about a collection of source-backed data records.

`metric`
  A structured numeric value with unit, period, value basis, evidence, and
  metric definition.

`event`
  A time-bound occurrence or expected occurrence such as an order, shipment,
  filing, approval, capacity expansion, product launch, or missed milestone.

`claim`
  A narrow checkable assertion backed by evidence. Claims use `support_type` to
  describe reasoning distance from evidence.

`relationship`
  A typed graph connection among entities. Relationship instances are checked
  against registered or proposed relationship-type ontology records.

`question`
  An open proof gap or next investigation target. Questions are not truth
  labels.

`challenge`
  An unresolved objection about contradiction, missing evidence, source quality,
  scope, freshness, ontology fit, materiality, or another issue.

`validation`
  An append-only review record with a verdict such as `supports`, `disputes`,
  `marks_stale`, or `withdraws`.

`thesis`
  A broader interpretation, causal argument, watch item, or forecast built from
  explicit dependencies.

## Identity Model

Do not collapse public-market identity into one company record.

- `company`: the legal issuer or operating company.
- `security`: a share class, ADR/ADS, bond, option, or other instrument.
- `listing`: the venue quote for a security.

Use security and listing records when ticker, exchange, depositary ratio, ISIN,
FIGI, CUSIP, SEDOL, RIC, or local issuer identifiers matter.

## Evidence Classes

Supported evidence classes are:

```text
public_primary
public_secondary
firsthand_public
firsthand_private
anonymous_internal
rumor
```

Low-trust classes are allowed, but they must stay visibly labeled. They should
not be the only path to strong derived review state for claims, relationships,
or theses.

## Source Perspective

Every source declares `source_perspective`. This is provenance metadata, not
truth status. Review output uses it to distinguish company-originated,
counterparty, independent, regulator, legal, social, first-hand, anonymous,
internal, aggregator, synthetic fixture, and unknown support.

Use `unknown` only when the source-side perspective cannot be determined after
review.

## Structured Promotion Rules

Use structured records instead of prose-only claims when the shape is known:

- reported or calculated number: `metric`
- expected or occurred timing: `event`
- source-backed narrow assertion: `claim`
- buyer, seller, supplier, customer, design-in, qualification, component use,
  manufacturing, competitor, ownership, regulatory, technology, or product edge:
  `relationship`
- missing revenue bridge, allocation proof, order value, named customer, timing,
  or materiality support: `question` or `challenge`
- broader investment view: `thesis`

Broad segment revenue is not named-customer allocation proof. Product fit is not
customer revenue proof. Ecosystem adjacency is not a supplier relationship.
Keep those gaps visible.

## Local Derived State

Canonical records do not store truth `status` or `confidence`.

Local tools derive review state from support evidence, source independence,
validation dependency paths, open challenges, contradictions, supersession,
staleness markers, scope limitations, and risk flags.

Generated files:

```text
.local/index.sqlite
.local/graph.json
.local/github-view/
```

These files are rebuildable and ignored by git.
