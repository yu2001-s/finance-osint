---
name: add-metric-event-dataset
description: Use when adding structured numeric facts, reported guidance, order values, backlog, shipments, capacity, valuation snapshots, events, or datasets.
---

# Add Metric Event Dataset

Use structured records before prose claims when the source contains numbers,
dates, order announcements, guidance, shipments, capacity, or datasets.

## Metric Workflow

1. Check for the metric definition:

```bash
uv run fo search metric_definition --json
```

2. Create the metric from explicit evidence:

```bash
uv run fo new metric \
  --entity entity:company:example \
  --metric-definition metric_definition:revenue \
  --value 1000000 \
  --unit USD \
  --period start=2026-01-01 \
  --period end=2026-03-31 \
  --value-basis reported \
  --evidence evidence:... \
  --submitted-by github:USERNAME \
  --json
```

Use `value_basis` narrowly:

```text
reported  source reports the number
observed  contributor/source observed the value directly
derived   calculated from explicit source-backed inputs
estimated explicit estimate/consensus/model source, not contributor forecast
restated  source-backed restatement of an earlier value
```

## Event Workflow

Use events for order announcements, shipments, product launches, guidance
updates, missed catalysts, legal/regulatory actions, and other dated facts.

```bash
uv run fo new event \
  --event-type commercial_order \
  --event-state occurred \
  --title "Example order announcement" \
  --entity entity:company:seller \
  --entity entity:company:buyer \
  --occurred-at "YYYY-MM-DD" \
  --evidence evidence:... \
  --submitted-by github:USERNAME \
  --json
```

For expected catalysts, use exact dates only when the source gives exact dates.
If the source gives a window or an inferred timing range, put that under
`period` or `properties` instead of inventing an exact `expected_at`.

Suggested `properties` keys when useful:

```yaml
date_type: window
timing_basis: company_guided
timing_confidence: guided
```

## Dataset Workflow

Use datasets for reusable tables or source collections, not for one-off excerpts.

```bash
uv run fo new dataset \
  --title "Example dataset" \
  --dataset-type source_collection \
  --publisher "Example Publisher" \
  --coverage entity=entity:company:example \
  --access public=true \
  --source source:... \
  --content-mode external_link \
  --submitted-by github:USERNAME \
  --json
```

## Boundaries

- Company guidance is source-backed data. Contributor forecasts belong in theses.
- Pipeline, backlog, bookings, order value, and revenue are different metrics.
- If a metric definition is missing, stop and use `propose-ontology`; do not
  bury numeric facts in claim prose.
