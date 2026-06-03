# Governance And Review

Finance OSINT uses lightweight repo governance. The goal is to keep evidence
visible, reviewable, falsifiable, and useful without creating hidden moderation
state.

## Review Principle

The repository does not suppress unusual, speculative, low-trust, promotional,
bearish, bullish, disputed, anonymous, social, first-hand, rumor, or
unverifiable material merely because it is uncertain or unpopular.

It requires honest labels:

- provenance
- evidence class
- source perspective
- source attribution
- content mode
- support type
- risk flags
- open questions
- open challenges
- limitations

Readers should be able to evaluate the support chain without trusting hidden
context.

## Maintainer Role

Maintainers review pull requests for:

- schema validity
- reference integrity
- ontology fit
- evidence and source preservation
- appropriate support strength
- graph scope and materiality
- contributor attribution
- generated review warnings
- repository hygiene

Maintainers do not turn personal agreement with an investment view into
canonical truth.

## Merge Criteria

A PR is mergeable when:

- required CI passes
- `fo diff-review` warnings are reviewed and explained
- new records use valid `submitted_by` attribution
- claims point to evidence
- metrics and events use structured records when appropriate
- relationships are supported and scoped to the selected type
- open proof gaps are captured as questions or challenges
- support-affecting information is visible in the repo
- agent-assisted output has been checked by the PR submitter

Full source-to-thesis chains are useful but not required for every PR.

## Review Actions

Use the narrowest action that preserves the record:

- Ask for relabeling when evidence class, source perspective, support type, or
  risk flags are too strong or missing.
- Ask for narrowing when a claim, relationship, or thesis says more than the
  evidence supports.
- Ask for a question when the proof gap is useful and unresolved.
- Ask for a challenge when support, scope, materiality, ontology, or freshness
  is contested.
- Ask for a validation when support has been reviewed and should be visible.
- Archive or supersede records when history should remain visible.

## Disputes

Do not overwrite sourced records to win an argument.

Use:

- `challenge` for open objections
- `validation` for support review
- `question` for unresolved proof gaps
- `contradicts`, `supersedes`, `corrects`, `restates`, `narrows`, or `broadens`
  for explicit lifecycle or disagreement links

The preferred outcome is a better graph, not a deleted debate.

## Rejection Boundaries

Reject or remove content that adds:

- hidden source knowledge or hidden agent state
- possible MNPI
- private-source identity leakage
- unsupported defamatory claims
- coordinated promotion or spam
- secrets, credentials, doxxing material, malware, or exploit payloads
- large copyrighted artifacts
- canonical truth `status` or `confidence`

Rumor and anonymous material can be represented only when labeled honestly and
kept visibly low-trust.

## Ontology Governance

Prefer registered terms. Use provisional terms only when existing ontology
cannot represent the case without losing important meaning.

Ontology PRs should include:

- proposed definition
- allowed roles or fields
- source requirements
- at least one concrete example
- comparison with existing ontology terms
- migration expectations if the term is accepted, renamed, merged, or rejected

Maintainers may register, rename, merge, narrow, broaden, or reject proposed
terms.

## GitHub Controls

Pull requests are the contribution queue and public audit trail.

At minimum the repository should require:

- default-branch protection
- fresh validation before merge
- conversation resolution before merge
- no force pushes or default-branch deletion
- issue routing for ontology proposals, source concerns, disputes, abuse,
  defamation, and market-integrity concerns

The local checks in `CONTRIBUTING.md` are the source of truth for PR readiness.
