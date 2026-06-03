# Pull Request

## Change Type

- [ ] Source / evidence
- [ ] Claim
- [ ] Metric / event / dataset
- [ ] Relationship / relationship type
- [ ] Validation / challenge
- [ ] Thesis
- [ ] Docs / tooling / tests

## Summary

Briefly describe what changed and why.

## Contribution Shape

Atomic contributions are welcome. A PR does not need to add a complete
source-to-thesis chain when it adds a useful, correctly labeled point.

- Atomic record, partial chain, or full chain:
- What this PR adds:
- What remains missing or intentionally out of scope:

## Evidence And Provenance

List the main source/evidence records this PR depends on:

- Source IDs:
- Evidence IDs:
- `source_attribution`:
- `content_mode`:
- `support_type` for claims:

## Labeling Standard

Finance OSINT allows unusual, speculative, low-trust, promotional, bearish,
bullish, disputed, anonymous, rumor, social, first-hand, and unverifiable
material when it is labeled honestly. This PR should make the evidence chain,
uncertainty, and objections visible rather than asking reviewers to trust hidden
context.

- Low-trust or unverifiable material included:
- Labels used to make limits visible:
- Any claim, relationship, or thesis narrowed because support is weak:
- Questions or challenges added for unresolved proof gaps:

## Graph / Review Impact

- New or changed entity IDs:
- New or changed relationship IDs:
- New or changed thesis IDs:
- Contradicts / supersedes / duplicate_of links:
- Open questions added or addressed:
- Open challenges added or addressed:

## Source-To-Claim Chain Review

For every changed thesis or relationship, run `uv run fo review ID --chain --json`
after `uv run fo index build --json`, or review the generated
`github-view` artifact / `.local/ci/github-view/pr-review.md`, and summarize:

- Reviewed IDs:
- Source/evidence mix:
- Claim / metric / event / relationship chain:
- Relationship-promotion pressure:
- What remains unproven:
- Generated GitHub-view artifact:

## Diff-Review Warnings

Run `uv run fo diff-review BASE --json` and summarize every warning. Warnings
are review pressure even when CI passes.

- Warning codes:
- Evidence mutations or deletions:
- Low-trust, private, anonymous, or rumor evidence:
- Mutable source preservation warnings:
- Ontology changes:
- Review-state movement:
- Archive additions or moves:
- Why each warning is acceptable or how this PR addresses it:

## CI Timing / Scale Impact

For tooling, schema, graph/index, or large data PRs, summarize generated CI
reports:

- Timing report path or artifact:
- Steps over advisory budget:
- 10k scale smoke result:
- Query-plan or generated-artifact concerns:

## Contributor Check

- [ ] I ran `uv run fo lint --json`.
- [ ] I ran `uv run python -m unittest discover -s tests`.
- [ ] I ran `uv run fo index build --json`.
- [ ] I ran `uv run fo review ID --chain --json` for changed records/theses/relationships.
- [ ] I ran `uv run fo graph build --json`.
- [ ] I ran `uv run fo diff-review BASE --json`.
- [ ] For changed theses/relationships, I reviewed `uv run fo view build BASE --json` output or the CI `github-view` artifact.
- [ ] For tooling/schema/index/graph changes, I reviewed the timing and scale-smoke reports.
- [ ] I reviewed and explained every `fo diff-review` warning.
- [ ] All support-affecting information is visible in the repo.
- [ ] I did not add hidden source knowledge, hidden agent state, canonical `status`, or canonical `confidence`.
- [ ] I labeled social, rumor, anonymous, private-source, first-hand, or unverifiable material honestly and did not present it as stronger support than it is.
- [ ] Any revenue, valuation, customer-allocation, supplier, qualified-supplier, design-win, BOM, or AVL leap has an explicit question or challenge unless directly supported.
- [ ] I checked any agent-assisted output and take responsibility for this PR.
