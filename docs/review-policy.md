# Review Policy

The project should preserve disagreement without weakening provenance.

## Merge Bias

- Evidence should be reviewed strictly.
- Claims should be narrow and sourced.
- Validations and challenges should be append-only records rather than destructive edits.
- Relationships should use registered or provisional ontology.
- Metrics and events should preserve point-in-time context.
- Theses may be speculative, but must declare dependencies.
- Unusual or low-trust material should be labeled, challenged, or narrowed
  before it is suppressed. Viewpoint disagreement is not a rejection reason.

Reviewers should distinguish:

- **Allowed but low-trust:** rumor, anonymous, unverifiable, social, private,
  first-hand, speculative, or aggressive material that is labeled honestly.
- **Needs relabeling:** material presented with an evidence class, support type,
  source perspective, or claim strength that overstates the source path.
- **Hard reject:** hidden provenance, fake provenance, unsafe private material,
  private-source identity leakage, possible MNPI, doxxing, malware, spam,
  coordinated promotion, large copyrighted artifacts, or schema-breaking data.

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

Validation verdict meanings:

- `attests`: reviewer confirms a narrow record or evidence object exists as
  described.
- `supports`: dependency path supports the target as written.
- `partially_supports`: dependency path supports only part of the target or
  supports it with material scope limits.
- `disputes`: dependency path contests the target or shows the current wording is
  overbroad.
- `falsifies`: dependency path contradicts the target strongly enough that the
  target should review as contested unless withdrawn or superseded.
- `marks_stale`: dependency path shows the target is outdated for current use.
- `withdraws`: reviewer withdraws a prior target, usually because the submitted
  claim was overbroad, duplicated, or no longer supportable.

Independent support is about resolved evidence/source paths, not vote count.
Prefer validations backed by a distinct evidence path whose source perspective is
`independent_media`, `independent_research`, `government_or_regulator`, or
`court_or_legal_record`. Repeated validations over the same resolved
evidence/source path should be counted as repeated review, not as independent
support.

## Derived State

Canonical records should not store truth `status` or `confidence`. Local tools
derive review labels from the evidence graph, validations, challenges,
contradictions, archive location, freshness, source perspective, and
supersession links. Automatic freshness windows are advisory warnings in v1;
use `marks_stale` validations or open `outdated` challenges to move review state
to stale.
