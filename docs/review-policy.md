# Review Policy

The project should preserve disagreement without weakening provenance.

## Merge Bias

- Evidence should be reviewed strictly.
- Claims should be narrow and sourced.
- Validations and challenges should be append-only records rather than destructive edits.
- Relationships should use registered or provisional ontology.
- Metrics and events should preserve point-in-time context.
- Theses may be speculative, but must declare dependencies.

## First-Hand Information

First-hand, private, anonymous, and rumor reports are allowed when they declare:

- evidence class
- source attribution
- public or nonpublic status through the source
- access conditions
- verification status when known
- risk flags

Anonymous or internal-source reports should stay visibly low-trust unless
independently supported by public or otherwise stronger evidence.

Low-trust evidence may support investigation and theses. It should not be the
sole support path for strong derived review states.

## Source Perspective

`source_perspective` classifies the source-side viewpoint, not credibility.
Examples include `company_self`, `counterparty_self`, `independent_media`,
`independent_research`, `government_or_regulator`, `social_media_author`,
`firsthand_observer`, `anonymous_source`, `internal_source`, and
`synthetic_fixture`.

Review output should expose perspective buckets and counts. When support exists
only through company/counterparty-originated sources and has no independent
source, tools may add the derived flag `company_originated_only_support`. This
does not change the canonical record and does not by itself falsify support.

## Validation and Challenge Norm

Use validations for targeted review outcomes:

- attests
- supports
- partially_supports
- disputes
- falsifies
- marks_stale
- withdraws

Use challenges for open objections:

- contradiction
- missing_evidence
- source_quality
- scope_error
- outdated
- ontology_issue
- materiality_dispute
- other

Validation evaluates support. Challenge records unresolved pressure.

## Derived State

Canonical records should not store truth `status` or `confidence`. Local tools
derive review labels from the evidence graph, validations, challenges,
contradictions, archive location, freshness, source perspective, and
supersession links.
