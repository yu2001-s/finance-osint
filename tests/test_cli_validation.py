from __future__ import annotations

import contextlib
import io
import shutil
import tempfile
import unittest
from pathlib import Path

import yaml

from fosint import cli


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIRS = (
    "schemas",
    "relationship-types",
    "entities",
    "sources",
    "evidence",
    "claims",
    "validations",
    "challenges",
    "relationships",
    "theses",
    "debates",
)


def copy_fixture_repo(target: Path) -> Path:
    repo = target / "repo"
    repo.mkdir()
    for dirname in FIXTURE_DIRS:
        source = ROOT / dirname
        if source.exists():
            shutil.copytree(source, repo / dirname)
    return repo


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle)
    assert isinstance(loaded, dict)
    return loaded


def write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, sort_keys=False)


def run_lint(root: Path) -> tuple[int, str]:
    stderr = io.StringIO()
    stdout = io.StringIO()
    with contextlib.redirect_stderr(stderr), contextlib.redirect_stdout(stdout):
        status = cli.run_lint(root)
    return status, stdout.getvalue() + stderr.getvalue()


class CliValidationTests(unittest.TestCase):
    def test_scaffold_lints(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))

            status, output = run_lint(repo)

        self.assertEqual(status, 0, output)
        self.assertIn("OK", output)

    def test_low_trust_only_claim_cannot_be_corroborated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            write_yaml(
                repo / "sources" / "firsthand" / "anonymous-rumor.yml",
                {
                    "kind": "source",
                    "id": "source:firsthand:anonymous-rumor",
                    "source_type": "anonymous_report",
                    "title": "Anonymous rumor fixture",
                    "public_status": "unknown",
                    "accessed_at": "2026-06-02T00:00:00Z",
                    "risk_flags": ["anonymous_source"],
                },
            )
            write_yaml(
                repo / "evidence" / "firsthand" / "anonymous-rumor.yml",
                {
                    "kind": "evidence",
                    "id": "evidence:firsthand:anonymous-rumor",
                    "evidence_class": "E5_unverified_rumor",
                    "source": "source:firsthand:anonymous-rumor",
                    "summary": "Anonymous rumor fixture.",
                    "observed_at": "2026-06-02T00:00:00Z",
                    "submitted_by": "github:tester",
                    "attribution": "anonymous_to_public",
                    "source_access": {
                        "nda_or_confidentiality": "unknown",
                        "recording_available": False,
                        "source_identity_public": False,
                    },
                    "risk_flags": ["anonymous_source", "unverified_rumor"],
                    "status": "attested",
                },
            )
            write_yaml(
                repo / "claims" / "anonymous-correlated-claim.yml",
                {
                    "kind": "claim",
                    "id": "claim:test:anonymous-correlated-claim",
                    "statement": "Anonymous rumor fixture is treated as corroborated.",
                    "subject": "entity:company:EXDEV",
                    "predicate": "has_rumored_issue",
                    "object": True,
                    "status": "corroborated",
                    "confidence": "medium",
                    "evidence": ["evidence:firsthand:anonymous-rumor"],
                },
            )

            status, output = run_lint(repo)

        self.assertEqual(status, 1, output)
        self.assertIn("non-low-trust evidence", output)

    def test_relationship_materiality_level_must_match_type(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            path = repo / "relationships" / "synthetic-exdev-fndwy-x1-supply.yml"
            data = load_yaml(path)
            data["materiality"]["level"] = "existential"
            write_yaml(path, data)

            status, output = run_lint(repo)

        self.assertEqual(status, 1, output)
        self.assertIn("materiality level `existential` is not allowed", output)

    def test_relationship_qualifier_must_match_type(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            path = repo / "relationships" / "synthetic-exdev-fndwy-x1-supply.yml"
            data = load_yaml(path)
            data["qualifiers"] = ["secret_supplier"]
            write_yaml(path, data)

            status, output = run_lint(repo)

        self.assertEqual(status, 1, output)
        self.assertIn("qualifier `secret_supplier` is not allowed", output)

    def test_challenge_references_are_checked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            write_yaml(
                repo / "challenges" / "missing-reference.yml",
                {
                    "kind": "challenge",
                    "id": "challenge:test:missing-reference",
                    "target": "thesis:synthetic:exdev-margin-risk-from-foundry-concentration",
                    "author": "github:tester",
                    "challenge_type": "missing_evidence",
                    "summary": "Fixture challenge with a missing dependency.",
                    "depends_on": {"claims": ["claim:test:does-not-exist"]},
                    "status": "open",
                },
            )

            status, output = run_lint(repo)

        self.assertEqual(status, 1, output)
        self.assertIn("references missing id `claim:test:does-not-exist`", output)


if __name__ == "__main__":
    unittest.main()

