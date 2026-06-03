# Governance

Finance OSINT uses lightweight repo governance. The goal is to keep evidence
visible, reviewable, and falsifiable without creating hidden moderation state.

## Maintainer Role

Maintainers review pull requests for structure, provenance, evidence quality,
ontology fit, and repository hygiene. Maintainers do not turn review labels into
canonical truth.

For now, maintainers are the GitHub users with merge rights on the repo.

## GitHub Controls

The GitHub repository is the contribution queue and public audit trail. Before
public launch, maintainers should verify the controls in
`docs/github-public-launch-checklist.md`.

At minimum:

- Protect the default branch.
- Require the `Validate` workflow before merge.
- Require review for CODEOWNERS paths.
- Require conversation resolution before merge.
- Block force pushes and default-branch deletion.
- Route disputes, ontology proposals, source/takedown concerns, and abuse or
  market-integrity concerns through GitHub issue templates.

## Merge Criteria

A PR is mergeable when:

- Required CI passes.
- `fo diff-review` warnings are reviewed and explained.
- Support-affecting information is visible in the repo.
- New claims point to evidence.
- New relationships are supported by claims, evidence, metrics, or events.
- Strong relationships such as `supplier_relationship`, `customer_relationship`,
  `qualified_supplier`, `design_win`, or `manufacturing_partner` are scoped to
  what the source actually supports.
- Open proof gaps are captured as questions or challenges.
- Agent-assisted output has been reviewed by the PR submitter.

## Rejection Criteria

A PR should be rejected or sent back when it:

- Adds hidden source knowledge, hidden agent state, `agent_run`, or
  `generated_by`.
- Adds canonical truth `status` or `confidence`.
- Adds unsupported supplier, customer, design-win, qualified-supplier, BOM, AVL,
  revenue, margin, or valuation-conversion claims.
- Treats social media as proof of underlying company facts without separate
  source-backed evidence.
- Relies on anonymous/internal/rumor evidence as strong support without visible
  limitations.
- Contains possible MNPI, private-source identity leakage, unsupported
  defamatory claims, coordinated promotion, spam, or rumor laundering.
- Uploads secrets, credentials, doxxing material, malware, or large copyrighted
  artifacts.
- Breaks schemas, references, ontology rules, tests, or deterministic review
  checks.

## Ontology Changes

Prefer existing registered terms.

Use provisional terms only when the existing ontology cannot represent the
relationship, claim predicate, or metric definition without losing meaning.

Ontology PRs should include:

- Proposed definition.
- Allowed roles or fields.
- Source requirements.
- At least one concrete example.
- Whether an existing type can cover the case instead.

Maintainers may register, rename, merge, narrow, broaden, or reject provisional
terms.

## Disputes

Do not overwrite sourced records to win an argument.

Use:

- `challenge` for open objections.
- `validation` for review verdicts on support.
- `contradicts`, `supersedes`, `corrects`, `narrows`, or `broadens` when a
  record relationship is explicit.
- `question` for unresolved proof gaps.

The preferred outcome is a better graph, not a deleted debate.
