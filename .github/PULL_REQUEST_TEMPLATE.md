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

## Evidence And Provenance

List the main source/evidence records this PR depends on:

- Source IDs:
- Evidence IDs:
- `source_attribution`:
- `content_mode`:
- `support_type` for claims:

## Graph / Review Impact

- New or changed entity IDs:
- New or changed relationship IDs:
- New or changed thesis IDs:
- Contradicts / supersedes / duplicate_of links:
- Open questions added or addressed:
- Open challenges added or addressed:

## Source-To-Claim Chain Review

For every changed thesis or relationship, run `uv run fo review ID --chain --json`
after `uv run fo index build --json` and summarize:

- Reviewed IDs:
- Source/evidence mix:
- Claim / metric / event / relationship chain:
- Relationship-promotion pressure:
- What remains unproven:

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

## Contributor Check

- [ ] I ran `uv run fo lint --json`.
- [ ] I ran `uv run python -m unittest discover -s tests`.
- [ ] I ran `uv run fo index build --json`.
- [ ] I ran `uv run fo review ID --chain --json` for changed records/theses/relationships.
- [ ] I ran `uv run fo graph build --json`.
- [ ] I ran `uv run fo diff-review BASE --json`.
- [ ] I reviewed and explained every `fo diff-review` warning.
- [ ] All support-affecting information is visible in the repo.
- [ ] I did not add hidden source knowledge, hidden agent state, canonical `status`, or canonical `confidence`.
- [ ] I did not treat social, rumor, anonymous, or private-source material as proof of underlying company facts without separate source-backed evidence.
- [ ] Any revenue, valuation, customer-allocation, supplier, qualified-supplier, design-win, BOM, or AVL leap has an explicit question or challenge unless directly supported.
- [ ] I checked any agent-assisted output and take responsibility for this PR.
