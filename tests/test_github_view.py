from __future__ import annotations

import contextlib
import io
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

from fosint import cli


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIRS = ("schemas", "ontology", "records")


def copy_fixture_repo(target: Path) -> Path:
    repo = target / "repo"
    repo.mkdir()
    for dirname in FIXTURE_DIRS:
        shutil.copytree(ROOT / dirname, repo / dirname)
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


def init_git_repo(repo: Path) -> None:
    commands = (
        ["git", "init"],
        ["git", "config", "user.email", "tester@example.com"],
        ["git", "config", "user.name", "Test User"],
        ["git", "add", "."],
        ["git", "commit", "-m", "base fixture"],
    )
    for command in commands:
        subprocess.run(command, cwd=repo, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def git_sha(repo: Path, ref: str = "HEAD") -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--verify", f"{ref}^{{commit}}"],
        cwd=repo,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout.strip()


def commit_all(repo: Path, message: str) -> None:
    for command in (["git", "add", "."], ["git", "commit", "-m", message]):
        subprocess.run(command, cwd=repo, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def run_view_build(repo: Path, output_dir: Path, check: bool = False) -> int:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        return cli.run_view_build(repo, output_dir, base_ref="HEAD", json_output=True, check=check)


class GitHubViewTests(unittest.TestCase):
    def test_github_view_builds_deterministic_pr_chain_markdown_for_impacted_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            init_git_repo(repo)
            base_sha = git_sha(repo)
            evidence_path = (
                repo
                / "records"
                / "evidence"
                / "public"
                / "synthetic-exdev-fy2025-supplier-note.yml"
            )
            evidence = load_yaml(evidence_path)
            evidence["excerpt"] = "Updated evidence excerpt for impacted GitHub view test."
            write_yaml(evidence_path, evidence)

            output_dir = repo / ".local" / "github-view"
            status = run_view_build(repo, output_dir)
            first_render = {
                path.relative_to(output_dir): path.read_text(encoding="utf-8")
                for path in sorted(output_dir.rglob("*.md"))
            }
            status_again = run_view_build(repo, output_dir, check=True)
            status_third = run_view_build(repo, output_dir)
            second_render = {
                path.relative_to(output_dir): path.read_text(encoding="utf-8")
                for path in sorted(output_dir.rglob("*.md"))
            }

        self.assertEqual(status, 0)
        self.assertEqual(status_again, 0)
        self.assertEqual(status_third, 0)
        self.assertEqual(first_render, second_render)
        page_name = (
            Path("chains")
            / "thesis"
            / f"{cli.generated_view_slug('thesis:synthetic:exdev-margin-risk-from-foundry-concentration')}.md"
        )
        self.assertIn(Path("index.md"), first_render)
        self.assertIn(Path("pr-review.md"), first_render)
        self.assertIn(page_name, first_render)
        chain_page = first_render[page_name]
        self.assertIn("Derived review state is deterministic local output, not canonical truth.", chain_page)
        self.assertIn("thesis:synthetic:exdev-margin-risk-from-foundry-concentration", chain_page)
        self.assertIn("## Source Evidence", chain_page)
        self.assertIn("evidence:synthetic:exdev-fy2025-supplier-note", chain_page)
        self.assertIn("source:public:synthetic:exdev-fy2025-report", chain_page)
        self.assertIn("records/theses/synthetic-exdev-margin-risk-from-foundry-concentration.yml", chain_page)
        self.assertNotIn(str(ROOT), chain_page)
        self.assertNotIn(str(repo), chain_page)
        self.assertNotIn(".local/index.sqlite", chain_page)
        self.assertNotIn('{"', chain_page)
        pr_review = first_render[Path("pr-review.md")]
        self.assertIn("Base ref: `HEAD`", pr_review)
        self.assertIn(f"Base SHA: `{base_sha}`", pr_review)
        self.assertIn("## Changed Or Impacted Thesis/Relationship Chains", pr_review)
        self.assertIn("evidence:synthetic:exdev-fy2025-supplier-note", pr_review)

    def test_github_view_build_cleans_stale_chain_pages(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            init_git_repo(repo)
            thesis_path = (
                repo
                / "records"
                / "theses"
                / "synthetic-exdev-margin-risk-from-foundry-concentration.yml"
            )
            thesis = load_yaml(thesis_path)
            thesis["summary"] = thesis["summary"] + " GitHub view cleanup change."
            write_yaml(thesis_path, thesis)
            output_dir = repo / ".local" / "github-view"

            self.assertEqual(run_view_build(repo, output_dir), 0)
            self.assertTrue((output_dir / "chains").exists())

            commit_all(repo, "commit changed thesis")
            self.assertEqual(run_view_build(repo, output_dir), 0)

            markdown_paths = sorted(path.relative_to(output_dir) for path in output_dir.rglob("*.md"))

        self.assertEqual(markdown_paths, [Path("index.md"), Path("pr-review.md")])


if __name__ == "__main__":
    unittest.main()
