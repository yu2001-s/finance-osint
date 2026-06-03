from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any

import yaml

from scripts import check_pr_attribution


def run_git(repo: Path, args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout.strip()


def init_repo(repo: Path) -> None:
    run_git(repo, ["init"])
    run_git(repo, ["config", "user.email", "tester@example.com"])
    run_git(repo, ["config", "user.name", "Test User"])
    (repo / "records" / "claims").mkdir(parents=True)


def write_record(repo: Path, relative: str, data: dict[str, Any]) -> None:
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def commit_all(repo: Path, message: str) -> str:
    run_git(repo, ["add", "."])
    run_git(repo, ["commit", "--allow-empty", "-m", message])
    return run_git(repo, ["rev-parse", "--verify", "HEAD^{commit}"])


def claim(record_id: str, submitted_by: str | None = "github:alice") -> dict[str, Any]:
    data: dict[str, Any] = {
        "schema_version": 1,
        "kind": "claim",
        "id": record_id,
        "statement": "Synthetic claim for attribution tests.",
        "support_type": "direct",
        "evidence": ["evidence:test:one"],
    }
    if submitted_by is not None:
        data["submitted_by"] = submitted_by
    return data


class PrAttributionTests(unittest.TestCase):
    def test_new_record_must_match_pr_author(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_repo(repo)
            base = commit_all(repo, "base")
            write_record(
                repo,
                "records/claims/new.yml",
                claim("claim:test:new", submitted_by="github:bob"),
            )
            commit_all(repo, "feature")

            payload = check_pr_attribution.attribution_errors(repo, base, "alice")

        self.assertFalse(payload["ok"])
        self.assertEqual(payload["errors"][0]["code"], "new_record_submitted_by_mismatch")

    def test_new_record_matching_pr_author_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_repo(repo)
            base = commit_all(repo, "base")
            write_record(
                repo,
                "records/claims/new.yml",
                claim("claim:test:new", submitted_by="github:alice"),
            )
            commit_all(repo, "feature")

            payload = check_pr_attribution.attribution_errors(repo, base, "alice")

        self.assertTrue(payload["ok"])
        self.assertEqual(payload["checked_record_count"], 1)

    def test_new_record_missing_submitted_by_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_repo(repo)
            base = commit_all(repo, "base")
            write_record(repo, "records/claims/new.yml", claim("claim:test:new", submitted_by=None))
            commit_all(repo, "feature")

            payload = check_pr_attribution.attribution_errors(repo, base, "alice")

        self.assertFalse(payload["ok"])
        self.assertEqual(payload["errors"][0]["code"], "missing_submitted_by_new_record")

    def test_existing_record_can_keep_original_attribution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_repo(repo)
            write_record(
                repo,
                "records/claims/existing.yml",
                claim("claim:test:existing", submitted_by="github:codex"),
            )
            base = commit_all(repo, "base")
            data = claim("claim:test:existing", submitted_by="github:codex")
            data["statement"] = "Changed by Alice while preserving original attribution."
            write_record(repo, "records/claims/existing.yml", data)
            commit_all(repo, "feature")

            payload = check_pr_attribution.attribution_errors(repo, base, "alice")

        self.assertTrue(payload["ok"])

    def test_existing_record_may_move_attribution_to_pr_author(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_repo(repo)
            write_record(
                repo,
                "records/claims/existing.yml",
                claim("claim:test:existing", submitted_by="github:codex"),
            )
            base = commit_all(repo, "base")
            data = claim("claim:test:existing", submitted_by="github:alice")
            data["statement"] = "Changed by Alice and attributed to Alice."
            write_record(repo, "records/claims/existing.yml", data)
            commit_all(repo, "feature")

            payload = check_pr_attribution.attribution_errors(repo, base, "alice")

        self.assertTrue(payload["ok"])

    def test_existing_record_cannot_move_attribution_to_third_party(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_repo(repo)
            write_record(
                repo,
                "records/claims/existing.yml",
                claim("claim:test:existing", submitted_by="github:codex"),
            )
            base = commit_all(repo, "base")
            data = claim("claim:test:existing", submitted_by="github:bob")
            data["statement"] = "Changed by Alice but attributed to Bob."
            write_record(repo, "records/claims/existing.yml", data)
            commit_all(repo, "feature")

            payload = check_pr_attribution.attribution_errors(repo, base, "alice")

        self.assertFalse(payload["ok"])
        self.assertEqual(payload["errors"][0]["code"], "existing_record_submitted_by_mismatch")

    def test_explicit_automation_exception_allows_named_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_repo(repo)
            base = commit_all(repo, "base")
            write_record(
                repo,
                "records/claims/generated.yml",
                claim("claim:test:generated", submitted_by="github:codex"),
            )
            commit_all(repo, "feature")

            payload = check_pr_attribution.attribution_errors(
                repo,
                base,
                "alice",
                allowed_submitted_by={"github:codex"},
            )

        self.assertTrue(payload["ok"])


if __name__ == "__main__":
    unittest.main()
