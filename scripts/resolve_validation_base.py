from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


ZERO_SHA = "0000000000000000000000000000000000000000"


def run_git(root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def git_commit_sha(root: Path, ref: str) -> tuple[str | None, str | None]:
    result = run_git(root, ["rev-parse", "--verify", f"{ref}^{{commit}}"])
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "git rev-parse failed"
        return None, message
    return result.stdout.strip(), None


def resolve_validation_base(
    root: Path,
    event_name: str,
    pull_request_base_sha: str = "",
    push_before_sha: str = "",
    default_base: str = "HEAD",
) -> dict[str, str]:
    event_name = event_name.strip()
    pull_request_base_sha = pull_request_base_sha.strip()
    push_before_sha = push_before_sha.strip()

    base_ref = default_base
    source = "default"
    if event_name in {"pull_request", "pull_request_target"}:
        if not pull_request_base_sha:
            raise RuntimeError("pull_request base SHA is required for PR validation")
        base_ref = pull_request_base_sha
        source = "pull_request.base.sha"
    elif event_name == "push" and push_before_sha:
        base_ref = push_before_sha
        source = "push.before"

    if base_ref == ZERO_SHA:
        parent_sha, _ = git_commit_sha(root, "HEAD^")
        if parent_sha:
            base_ref = "HEAD^"
            source = f"{source}.zero_sha_fallback_head_parent"
        else:
            base_ref = "HEAD"
            source = f"{source}.zero_sha_fallback_head"

    base_sha, error = git_commit_sha(root, base_ref)
    if not base_sha:
        raise RuntimeError(f"failed to resolve validation base `{base_ref}` from {source}: {error}")
    return {
        "base_ref": base_ref,
        "base_sha": base_sha,
        "source": source,
    }


def append_github_outputs(payload: dict[str, str], github_env: str | None, step_summary: str | None) -> None:
    if github_env:
        with Path(github_env).open("a", encoding="utf-8") as handle:
            handle.write(f"BASE_REF={payload['base_sha']}\n")
    if step_summary:
        lines = [
            f"Validation base source: `{payload['source']}`",
            f"Validation base ref: `{payload['base_ref']}`",
            f"Validation base SHA: `{payload['base_sha']}`",
            "",
        ]
        with Path(step_summary).open("a", encoding="utf-8") as handle:
            handle.write("\n".join(lines))


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(str(args.root))
    payload = resolve_validation_base(
        root,
        str(args.event_name),
        pull_request_base_sha=str(args.pull_request_base_sha or ""),
        push_before_sha=str(args.push_before_sha or ""),
        default_base=str(args.default_base),
    )
    return {"command": "resolve-validation-base", "ok": True, **payload}


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve the stable Git base SHA for CI validation.")
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument(
        "--event-name",
        default=os.environ.get("GITHUB_EVENT_NAME", "local"),
        help="GitHub Actions event name, or local",
    )
    parser.add_argument(
        "--pull-request-base-sha",
        default="",
        help="github.event.pull_request.base.sha for PR events",
    )
    parser.add_argument(
        "--push-before-sha",
        default="",
        help="github.event.before for push events",
    )
    parser.add_argument("--default-base", default="HEAD", help="Fallback base ref")
    parser.add_argument("--github-env", default=os.environ.get("GITHUB_ENV"))
    parser.add_argument("--github-step-summary", default=os.environ.get("GITHUB_STEP_SUMMARY"))
    args = parser.parse_args()

    try:
        payload = build_payload(args)
        append_github_outputs(
            {key: str(payload[key]) for key in ("base_ref", "base_sha", "source")},
            str(args.github_env) if args.github_env else None,
            str(args.github_step_summary) if args.github_step_summary else None,
        )
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
