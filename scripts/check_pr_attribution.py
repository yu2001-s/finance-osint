from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


RECORD_PATH_PREFIXES = ("records/", "archive/records/")
RECORD_SUFFIXES = (".yml", ".yaml")


@dataclass(frozen=True)
class ChangedPath:
    status: str
    current_path: str | None
    base_path: str | None


def git_output(repo: Path, args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout


def git_output_bytes(repo: Path, args: list[str]) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", "replace").strip()
        raise RuntimeError(message or f"git {' '.join(args)} failed")
    return result.stdout


def is_record_path(path: str) -> bool:
    return path.endswith(RECORD_SUFFIXES) and path.startswith(RECORD_PATH_PREFIXES)


def parse_name_status_z(raw: bytes) -> list[ChangedPath]:
    parts = raw.rstrip(b"\0").split(b"\0") if raw else []
    decoded = [part.decode("utf-8", "surrogateescape") for part in parts]
    changes: list[ChangedPath] = []
    index = 0
    while index < len(decoded):
        status = decoded[index]
        index += 1
        if not status:
            continue
        code = status[0]
        if code in {"R", "C"}:
            old_path = decoded[index]
            new_path = decoded[index + 1]
            index += 2
            changes.append(ChangedPath(status=code, current_path=new_path, base_path=old_path))
        else:
            path = decoded[index]
            index += 1
            current_path = None if code == "D" else path
            base_path = None if code == "A" else path
            changes.append(ChangedPath(status=code, current_path=current_path, base_path=base_path))
    return changes


def load_yaml_text(text: str) -> dict[str, Any] | None:
    loaded = yaml.safe_load(text)
    return loaded if isinstance(loaded, dict) else None


def load_worktree_record(repo: Path, relative_path: str) -> dict[str, Any] | None:
    path = repo / relative_path
    if not path.exists():
        return None
    return load_yaml_text(path.read_text(encoding="utf-8"))


def load_git_record(repo: Path, ref: str, relative_path: str) -> dict[str, Any] | None:
    try:
        text = git_output(repo, ["show", f"{ref}:{relative_path}"])
    except RuntimeError:
        return None
    return load_yaml_text(text)


def base_record_map(repo: Path, base_ref: str) -> dict[str, dict[str, Any]]:
    raw = git_output_bytes(
        repo,
        [
            "ls-tree",
            "-r",
            "-z",
            "--name-only",
            base_ref,
            "--",
            "records",
            "archive/records",
        ],
    )
    paths = [
        part.decode("utf-8", "surrogateescape")
        for part in raw.rstrip(b"\0").split(b"\0")
        if part
    ]
    records: dict[str, dict[str, Any]] = {}
    for path in paths:
        if not is_record_path(path):
            continue
        data = load_git_record(repo, base_ref, path)
        if not data:
            continue
        record_id = data.get("id")
        if isinstance(record_id, str):
            records[record_id] = data
    return records


def changed_record_paths(repo: Path, base_ref: str, head_ref: str) -> list[ChangedPath]:
    raw = git_output_bytes(
        repo,
        [
            "diff",
            "--name-status",
            "-z",
            base_ref,
            head_ref,
            "--",
            "records",
            "archive/records",
        ],
    )
    return parse_name_status_z(raw)


def attribution_errors(
    repo: Path,
    base_ref: str,
    pr_author: str,
    *,
    head_ref: str = "HEAD",
    allowed_submitted_by: set[str] | None = None,
) -> dict[str, Any]:
    allowed = allowed_submitted_by or set()
    expected = f"github:{pr_author}"
    base_records = base_record_map(repo, base_ref)
    errors: list[dict[str, Any]] = []
    checked_records = 0

    for change in changed_record_paths(repo, base_ref, head_ref):
        if not change.current_path or not is_record_path(change.current_path):
            continue
        current = load_worktree_record(repo, change.current_path)
        if not current:
            continue
        record_id = current.get("id")
        if not isinstance(record_id, str):
            continue
        checked_records += 1
        submitted_by = current.get("submitted_by")
        base = base_records.get(record_id)
        base_submitted_by = base.get("submitted_by") if base else None

        if base is None:
            if submitted_by is None:
                errors.append(
                    {
                        "code": "missing_submitted_by_new_record",
                        "path": change.current_path,
                        "id": record_id,
                        "expected": expected,
                        "message": "New database records must declare submitted_by.",
                    }
                )
            elif submitted_by != expected and submitted_by not in allowed:
                errors.append(
                    {
                        "code": "new_record_submitted_by_mismatch",
                        "path": change.current_path,
                        "id": record_id,
                        "submitted_by": submitted_by,
                        "expected": expected,
                        "message": "New database records must be attributed to the PR author.",
                    }
                )
            continue

        submitted_by_changed_to_unapproved_identity = (
            submitted_by != base_submitted_by
            and submitted_by != expected
            and submitted_by not in allowed
        )
        if submitted_by_changed_to_unapproved_identity:
            errors.append(
                {
                    "code": "existing_record_submitted_by_mismatch",
                    "path": change.current_path,
                    "id": record_id,
                    "base_submitted_by": base_submitted_by,
                    "submitted_by": submitted_by,
                    "expected": expected,
                    "message": (
                        "Existing record attribution may remain unchanged or move to "
                        "the PR author, not to another identity."
                    ),
                }
            )

    return {
        "schema_version": 1,
        "command": "check-pr-attribution",
        "ok": not errors,
        "base": base_ref,
        "head": head_ref,
        "pr_author": pr_author,
        "expected_submitted_by": expected,
        "allowed_submitted_by": sorted(allowed),
        "checked_record_count": checked_records,
        "errors": errors,
    }


def print_human(payload: dict[str, Any]) -> None:
    if payload["ok"]:
        print(
            "PR attribution OK: "
            f"{payload['checked_record_count']} changed database records checked for "
            f"{payload['expected_submitted_by']}"
        )
        return
    print(
        "PR attribution failed: "
        f"{len(payload['errors'])} error(s) for expected "
        f"{payload['expected_submitted_by']}",
        file=sys.stderr,
    )
    for error in payload["errors"]:
        print(
            f"- {error['path']}: {error['code']}: {error['message']}",
            file=sys.stderr,
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ensure changed database records are attributed to the GitHub PR author."
    )
    parser.add_argument("base", help="Git base ref or SHA")
    parser.add_argument("--head", default="HEAD", help="Git head ref or SHA to compare")
    parser.add_argument("--pr-author", required=True, help="GitHub pull request author login")
    parser.add_argument(
        "--allow-submitted-by",
        action="append",
        default=[],
        help="Explicit maintainer-approved submitted_by identity, e.g. github:codex",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args()

    payload = attribution_errors(
        Path.cwd(),
        str(args.base),
        str(args.pr_author),
        head_ref=str(args.head),
        allowed_submitted_by=set(args.allow_submitted_by),
    )
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print_human(payload)
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
