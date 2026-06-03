from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts import resolve_validation_base as resolver


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


def commit_file(repo: Path, value: str, message: str) -> str:
    (repo / "fixture.txt").write_text(value + "\n", encoding="utf-8")
    run_git(repo, ["add", "fixture.txt"])
    run_git(repo, ["commit", "-m", message])
    return run_git(repo, ["rev-parse", "--verify", "HEAD^{commit}"])


class ValidationBaseResolutionTests(unittest.TestCase):
    def test_local_default_resolves_head(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_repo(repo)
            head_sha = commit_file(repo, "base", "base commit")

            payload = resolver.resolve_validation_base(repo, event_name="local")

        self.assertEqual(payload["base_ref"], "HEAD")
        self.assertEqual(payload["base_sha"], head_sha)
        self.assertEqual(payload["source"], "default")

    def test_push_uses_before_sha(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_repo(repo)
            before_sha = commit_file(repo, "base", "base commit")
            commit_file(repo, "next", "next commit")

            payload = resolver.resolve_validation_base(
                repo,
                event_name="push",
                push_before_sha=before_sha,
            )

        self.assertEqual(payload["base_ref"], before_sha)
        self.assertEqual(payload["base_sha"], before_sha)
        self.assertEqual(payload["source"], "push.before")

    def test_push_zero_sha_falls_back_to_parent_when_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_repo(repo)
            parent_sha = commit_file(repo, "base", "base commit")
            commit_file(repo, "next", "next commit")

            payload = resolver.resolve_validation_base(
                repo,
                event_name="push",
                push_before_sha=resolver.ZERO_SHA,
            )

        self.assertEqual(payload["base_ref"], "HEAD^")
        self.assertEqual(payload["base_sha"], parent_sha)
        self.assertEqual(payload["source"], "push.before.zero_sha_fallback_head_parent")

    def test_push_zero_sha_falls_back_to_head_for_initial_commit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_repo(repo)
            head_sha = commit_file(repo, "base", "base commit")

            payload = resolver.resolve_validation_base(
                repo,
                event_name="push",
                push_before_sha=resolver.ZERO_SHA,
            )

        self.assertEqual(payload["base_ref"], "HEAD")
        self.assertEqual(payload["base_sha"], head_sha)
        self.assertEqual(payload["source"], "push.before.zero_sha_fallback_head")

    def test_pull_request_uses_github_base_sha(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_repo(repo)
            base_sha = commit_file(repo, "base", "base commit")
            commit_file(repo, "feature", "feature commit")

            payload = resolver.resolve_validation_base(
                repo,
                event_name="pull_request",
                pull_request_base_sha=base_sha,
            )

        self.assertEqual(payload["base_ref"], base_sha)
        self.assertEqual(payload["base_sha"], base_sha)
        self.assertEqual(payload["source"], "pull_request.base.sha")


if __name__ == "__main__":
    unittest.main()
