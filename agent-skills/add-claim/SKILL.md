---
name: add-claim
description: Use when creating a narrow sourced claim from existing evidence, with registered or provisional predicates and explicit support_type.
---

# Add Claim

A claim is a narrow assertion backed by evidence. It is not a thesis and does
not carry truth status.

## Workflow

1. Inspect candidate evidence:

```bash
uv run fo context evidence:... --json
```

2. Check predicate vocabulary:

```bash
uv run fo search claim_predicate --json
```

3. Create the claim from explicit fields:

```bash
uv run fo new claim \
  --statement "Narrow checkable statement." \
  --subject entity:... \
  --predicate disclosed_relationship \
  --object entity:... \
  --support-type direct \
  --evidence evidence:... \
  --submitted-by github:USERNAME \
  --json
```

4. Validate and inspect:

```bash
uv run fo lint --json
uv run fo review claim:... --json
```

## Predicate Guidance

Use registered predicates where possible:

```text
reported_metric
disclosed_relationship
observed_event
management_statement
ownership_disclosure
transaction_disclosure
regulatory_action
legal_action
product_signal
market_signal
source_attestation
forecast_statement
```

Use `provisional:` only when a proposed definition exists.

## Support Type

- `direct`: evidence directly states it.
- `observed`: first-hand observation.
- `inferred`: reasoning from multiple evidence records or explicit methodology.
- `private_attestation`: private/internal source attests to it.
- `rumor`: weak signal only.

## Boundaries

- Do not add `status` or `confidence`.
- Do not phrase investment conclusions as claims.
- Do not create claims without evidence.
