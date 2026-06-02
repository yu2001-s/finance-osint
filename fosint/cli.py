from __future__ import annotations

import argparse
import json
import re
import sqlite3
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
    from jsonschema import Draft202012Validator
except ImportError as exc:  # pragma: no cover
    print(f"Missing dependency: {exc.name}. Run `pip install -e .` first.", file=sys.stderr)
    raise SystemExit(2) from exc


SCHEMA_BY_KIND = {
    "entity": "entity.schema.json",
    "source": "source.schema.json",
    "evidence": "evidence.schema.json",
    "claim_predicate": "claim-predicate.schema.json",
    "metric_definition": "metric-definition.schema.json",
    "metric": "metric.schema.json",
    "event": "event.schema.json",
    "dataset": "dataset.schema.json",
    "claim": "claim.schema.json",
    "validation": "validation.schema.json",
    "challenge": "challenge.schema.json",
    "question": "question.schema.json",
    "relationship_type": "relationship-type.schema.json",
    "relationship": "relationship.schema.json",
    "thesis": "thesis.schema.json",
}

REF_PREFIXES = (
    "entity:",
    "source:",
    "evidence:",
    "claim_predicate:",
    "metric_definition:",
    "metric:",
    "event:",
    "dataset:",
    "claim:",
    "validation:",
    "challenge:",
    "question:",
    "relationship:",
    "rel:",
    "thesis:",
    "debate:",
    "arg:",
    "resolution:",
)

SKIP_PARTS = {".git", ".local", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache"}
DATA_DIRS = (
    "relationship-types",
    "claim-predicates",
    "metric-definitions",
    "entities",
    "sources",
    "evidence",
    "datasets",
    "metrics",
    "events",
    "claims",
    "validations",
    "challenges",
    "questions",
    "relationships",
    "theses",
)

EVIDENCE_CLASSES_REQUIRING_ACCESS = {
    "firsthand_public",
    "firsthand_private",
    "anonymous_internal",
    "rumor",
}
LOW_TRUST_EVIDENCE_CLASSES = {"anonymous_internal", "rumor"}
OLD_EVIDENCE_CLASSES = {
    "E0_public_primary",
    "E1_public_secondary",
    "E2_firsthand_public",
    "E3_firsthand_private",
    "E4_anonymous_internal",
    "E5_unverified_rumor",
}
NO_TRUTH_FIELDS_KINDS = {"claim", "relationship", "thesis", "metric", "event", "evidence"}
NO_AUTHOR_FIELD_KINDS = {"validation", "challenge", "thesis"}
SUPPORTING_VERDICTS = {"attests", "supports"}
PARTIAL_VERDICTS = {"partially_supports"}
CONTESTING_VERDICTS = {"disputes", "falsifies"}
STALE_VERDICTS = {"marks_stale"}
WITHDRAWAL_VERDICTS = {"withdraws"}
STALE_CHALLENGE_TYPES = {"outdated"}
SCOPE_CHALLENGE_TYPES = {"scope_error", "materiality_dispute"}
PRIVATE_EVIDENCE_CLASSES = {"firsthand_private", "anonymous_internal"}
STALE_RISK_FLAGS = {"stale", "outdated", "needs_refresh", "staleness_risk"}
SCOPE_RISK_FLAGS = {"scope_limit", "scope_limitation", "scope_error", "materiality_dispute"}
DEPENDENCY_KEYS = ("evidence", "claims", "relationships", "theses", "metrics", "events", "datasets")
LINK_FIELDS = (
    "contradicts",
    "supersedes",
    "corrects",
    "restates",
    "narrows",
    "broadens",
)
REVIEWABLE_KINDS = {"evidence", "claim", "relationship", "thesis", "metric", "event", "dataset"}
ONTOLOGY_KINDS = {"claim_predicate", "relationship_type", "metric_definition"}
EVIDENCE_INTEGRITY_FIELDS = {
    "source",
    "evidence_class",
    "summary",
    "content_mode",
    "excerpt",
    "locator",
    "observed_at",
    "source_attribution",
    "source_access",
    "verification_status",
}
MUTABLE_WEB_SOURCE_TYPES = {"web_page", "news_article", "research_report"}
INDEPENDENT_SOURCE_PERSPECTIVES = {
    "independent_media",
    "independent_research",
    "government_or_regulator",
    "court_or_legal_record",
}
COMPANY_ORIGINATED_SOURCE_PERSPECTIVES = {"company_self", "counterparty_self"}
OTHER_SOURCE_PERSPECTIVES = {
    "social_media_author",
    "firsthand_observer",
    "anonymous_source",
    "internal_source",
    "aggregator",
    "synthetic_fixture",
    "unknown",
}
SOURCE_PERSPECTIVES = sorted(
    INDEPENDENT_SOURCE_PERSPECTIVES
    | COMPANY_ORIGINATED_SOURCE_PERSPECTIVES
    | OTHER_SOURCE_PERSPECTIVES
)
ARTIFACTS_ROOT = Path("artifacts")
SOURCE_ARTIFACTS_ROOT = Path("artifacts/sources")
SOURCE_ARTIFACT_SUFFIXES = {".png", ".jpg", ".jpeg", ".pdf"}
MAX_SOURCE_ARTIFACT_BYTES = 2 * 1024 * 1024
ARCHIVE_REQUIRED_FIELDS = ("superseded_by", "duplicate_of", "archive_reason")
CURRENT_TO_ARCHIVE_ALLOWED_FIELDS = {
    "supersedes",
    "corrects",
    "restates",
    "narrows",
    "broadens",
    "contradicts",
}
DUPLICATE_ENTITY_IDENTIFIER_KEYS = ("cik", "lei", "isin", "figi", "ticker")
DUPLICATE_WARNING_HINT = (
    "If duplicate, keep one canonical record and move obsolete records under archive/ "
    "with duplicate_of or superseded_by. If distinct, add clarifying fields such as "
    "exchange, period, scope, locator, or methodology."
)


@dataclass(frozen=True)
class Record:
    path: Path
    data: dict[str, Any]

    @property
    def id(self) -> str:
        return str(self.data.get("id", ""))

    @property
    def kind(self) -> str:
        return str(self.data.get("kind", ""))


def repo_root() -> Path:
    current = Path.cwd()
    for path in [current, *current.parents]:
        if (path / "pyproject.toml").exists() and (path / "schemas").exists():
            return path
    return current


def iter_yaml_files(root: Path, include_archive: bool = True) -> list[Path]:
    files: list[Path] = []
    for dirname in DATA_DIRS:
        directory = root / dirname
        if not directory.exists():
            continue
        for path in directory.rglob("*"):
            if any(part in SKIP_PARTS for part in path.parts):
                continue
            if path.is_file() and path.suffix in {".yml", ".yaml"}:
                files.append(path)
    if include_archive:
        archive = root / "archive"
        if archive.exists():
            for path in archive.rglob("*"):
                if any(part in SKIP_PARTS for part in path.parts):
                    continue
                if path.is_file() and path.suffix in {".yml", ".yaml"}:
                    files.append(path)
    return sorted(files)


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle)
    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise ValueError("YAML document must be an object")
    return loaded


def load_records(root: Path, include_archive: bool = True) -> tuple[list[Record], list[str]]:
    records: list[Record] = []
    errors: list[str] = []
    for path in iter_yaml_files(root, include_archive=include_archive):
        try:
            records.append(Record(path=path, data=load_yaml(path)))
        except Exception as exc:
            errors.append(f"{path.relative_to(root)}: failed to load YAML: {exc}")
    return records, errors


def load_schemas(root: Path) -> dict[str, Draft202012Validator]:
    validators: dict[str, Draft202012Validator] = {}
    for kind, filename in SCHEMA_BY_KIND.items():
        with (root / "schemas" / filename).open("r", encoding="utf-8") as handle:
            schema = json.load(handle)
        validators[kind] = Draft202012Validator(schema)
    return validators


def format_error_path(error: Any) -> str:
    if not error.path:
        return "$"
    return "$." + ".".join(str(part) for part in error.path)


def validate_schemas(
    root: Path, records: list[Record], validators: dict[str, Draft202012Validator]
) -> list[str]:
    errors: list[str] = []
    for record in records:
        relative = record.path.relative_to(root)
        kind = record.data.get("kind")
        if kind not in validators:
            errors.append(f"{relative}: unknown or missing kind `{kind}`")
            continue
        for error in sorted(validators[kind].iter_errors(record.data), key=lambda item: item.path):
            errors.append(f"{relative}: {format_error_path(error)}: {error.message}")
    return errors


def build_id_map(root: Path, records: list[Record]) -> tuple[dict[str, Record], list[str]]:
    id_map: dict[str, Record] = {}
    errors: list[str] = []
    for record in records:
        record_id = record.id
        if not record_id:
            continue
        if record_id in id_map:
            errors.append(
                f"{record.path.relative_to(root)}: duplicate id `{record_id}` already used by "
                f"{id_map[record_id].path.relative_to(root)}"
            )
            continue
        id_map[record_id] = record
    return id_map, errors


def walk_strings(value: Any, path: tuple[str, ...] = ()) -> list[tuple[tuple[str, ...], str]]:
    found: list[tuple[tuple[str, ...], str]] = []
    if isinstance(value, str):
        found.append((path, value))
    elif isinstance(value, dict):
        for key, child in value.items():
            found.extend(walk_strings(child, (*path, str(key))))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(walk_strings(child, (*path, str(index))))
    return found


def is_reference(value: str) -> bool:
    return value.startswith(REF_PREFIXES)


def validate_references(root: Path, records: list[Record], id_map: dict[str, Record]) -> list[str]:
    errors: list[str] = []
    for record in records:
        for path, value in walk_strings(record.data):
            if path == ("id",):
                continue
            if not is_reference(value):
                continue
            if value not in id_map:
                dotted = ".".join(path) or "$"
                errors.append(
                    f"{record.path.relative_to(root)}: {dotted} references missing id `{value}`"
                )
    return errors


def registered_relationship_types(records: list[Record]) -> dict[str, Record]:
    return {
        record.id: record
        for record in records
        if record.kind == "relationship_type" and record.data.get("state") == "registered"
    }


def proposed_relationship_types(records: list[Record]) -> dict[str, Record]:
    return {
        record.id: record
        for record in records
        if record.kind == "relationship_type" and record.data.get("state") == "proposed"
    }


def registered_claim_predicates(records: list[Record]) -> dict[str, Record]:
    return {
        str(record.data.get("name")): record
        for record in records
        if record.kind == "claim_predicate" and record.data.get("state") == "registered"
    }


def proposed_claim_predicates(records: list[Record]) -> dict[str, Record]:
    return {
        str(record.data.get("name")): record
        for record in records
        if record.kind == "claim_predicate" and record.data.get("state") == "proposed"
    }


def entity_type_for(record_id: str, id_map: dict[str, Record]) -> str | None:
    record = id_map.get(record_id)
    if not record or record.kind != "entity":
        return None
    return str(record.data.get("entity_type"))


def as_string_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def as_reference_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if not isinstance(value, list):
        return []
    found: list[str] = []
    for item in value:
        if isinstance(item, str):
            found.append(item)
        elif isinstance(item, dict) and isinstance(item.get("id"), str):
            found.append(str(item["id"]))
    return found


def evidence_class_for(record_id: str, id_map: dict[str, Record]) -> str | None:
    record = id_map.get(record_id)
    if not record or record.kind != "evidence":
        return None
    return str(record.data.get("evidence_class"))


def evidence_ids_for_claim(record: Record) -> list[str]:
    return as_reference_list(record.data.get("evidence"))


def evidence_ids_for_relationship(record: Record, id_map: dict[str, Record]) -> list[str]:
    derived_from = record.data.get("derived_from", {})
    if not isinstance(derived_from, dict):
        return []

    evidence_ids = as_string_list(derived_from.get("evidence"))
    for claim_id in as_string_list(derived_from.get("claims")):
        claim = id_map.get(claim_id)
        if claim and claim.kind == "claim":
            evidence_ids.extend(evidence_ids_for_claim(claim))
    return sorted(set(evidence_ids))


def evidence_ids_for_validation(record: Record, id_map: dict[str, Record]) -> list[str]:
    depends_on = record.data.get("depends_on", {})
    if not isinstance(depends_on, dict):
        return []

    evidence_ids = as_string_list(depends_on.get("evidence"))
    for claim_id in as_string_list(depends_on.get("claims")):
        claim = id_map.get(claim_id)
        if claim and claim.kind == "claim":
            evidence_ids.extend(evidence_ids_for_claim(claim))
    for relationship_id in as_string_list(depends_on.get("relationships")):
        relationship = id_map.get(relationship_id)
        if relationship and relationship.kind == "relationship":
            evidence_ids.extend(evidence_ids_for_relationship(relationship, id_map))
    return sorted(set(evidence_ids))


def evidence_support_classes(evidence_ids: list[str], id_map: dict[str, Record]) -> set[str]:
    return {
        evidence_class
        for evidence_id in evidence_ids
        if (evidence_class := evidence_class_for(evidence_id, id_map))
    }


def has_non_low_trust_support(evidence_ids: list[str], id_map: dict[str, Record]) -> bool:
    classes = evidence_support_classes(evidence_ids, id_map)
    return any(evidence_class not in LOW_TRUST_EVIDENCE_CLASSES for evidence_class in classes)


def normalize_qualifiers(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    if isinstance(value, dict):
        return [str(key) for key, enabled in value.items() if enabled]
    return []


def validate_relationships(
    root: Path, records: list[Record], id_map: dict[str, Record]
) -> list[str]:
    errors: list[str] = []
    registered = registered_relationship_types(records)
    proposed = proposed_relationship_types(records)

    for record in records:
        if record.kind != "relationship":
            continue

        relative = record.path.relative_to(root)
        rel_type = str(record.data.get("type", ""))
        type_def: Record | None = None

        if rel_type.startswith("provisional:"):
            proposed_id = rel_type.split(":", 1)[1]
            proposed_path = record.data.get("proposed_type_definition")
            if not proposed_path:
                errors.append(f"{relative}: provisional type `{rel_type}` needs proposed_type_definition")
            else:
                definition_path = root / str(proposed_path)
                if not definition_path.exists():
                    errors.append(
                        f"{relative}: proposed_type_definition `{proposed_path}` does not exist"
                    )
            if proposed_id not in proposed:
                errors.append(
                    f"{relative}: provisional type `{rel_type}` has no proposed relationship_type record"
                )
            else:
                type_def = proposed[proposed_id]
        else:
            if rel_type not in registered:
                errors.append(f"{relative}: relationship type `{rel_type}` is not registered")
            else:
                type_def = registered[rel_type]

        if type_def is None:
            continue

        role_defs = {
            role.get("name"): role
            for role in type_def.data.get("roles", [])
            if isinstance(role, dict) and isinstance(role.get("name"), str)
        }
        participants = record.data.get("participants", [])
        role_counts: dict[str, int] = {}
        if not isinstance(participants, list):
            continue

        for participant in participants:
            if not isinstance(participant, dict):
                continue
            role = str(participant.get("role", ""))
            participant_id = participant.get("entity")
            role_counts[role] = role_counts.get(role, 0) + 1

            if role not in role_defs:
                errors.append(
                    f"{relative}: participant role `{role}` is not allowed by type `{rel_type}`"
                )
                continue
            if not isinstance(participant_id, str) or not participant_id.startswith("entity:"):
                errors.append(
                    f"{relative}: participant `{role}` must reference an entity id, got "
                    f"`{participant_id}`"
                )
                continue
            actual_entity_type = entity_type_for(participant_id, id_map)
            allowed_entity_types = role_defs[role].get("allowed_entity_types", [])
            if actual_entity_type and actual_entity_type not in allowed_entity_types:
                errors.append(
                    f"{relative}: `{participant_id}` has entity_type `{actual_entity_type}`, "
                    f"but role `{role}` expects one of {allowed_entity_types}"
                )

        for role_name, role_def in role_defs.items():
            count = role_counts.get(str(role_name), 0)
            min_count = int(role_def.get("min", 0))
            max_count = role_def.get("max")
            if role_def.get("required") and count < min_count:
                errors.append(
                    f"{relative}: relationship type `{rel_type}` requires at least "
                    f"{min_count} participant(s) for role `{role_name}`"
                )
            if isinstance(max_count, int) and count > max_count:
                errors.append(
                    f"{relative}: relationship type `{rel_type}` allows at most "
                    f"{max_count} participant(s) for role `{role_name}`"
                )

        allowed_scope = set(type_def.data.get("allowed_scope", []))
        scope = record.data.get("scope", {})
        if allowed_scope and isinstance(scope, dict):
            for key in scope:
                if key not in allowed_scope:
                    errors.append(
                        f"{relative}: scope `{key}` is not allowed by "
                        f"relationship type `{rel_type}`"
                    )

        allowed_qualifiers = set(type_def.data.get("allowed_qualifiers", []))
        if allowed_qualifiers:
            for qualifier in normalize_qualifiers(record.data.get("qualifiers")):
                if qualifier not in allowed_qualifiers:
                    errors.append(
                        f"{relative}: qualifier `{qualifier}` is not allowed by "
                        f"relationship type `{rel_type}`"
                    )

        allowed_materiality = type_def.data.get("materiality", {}).get("allowed_values", [])
        materiality_level = record.data.get("materiality", {}).get("level")
        if allowed_materiality and materiality_level and materiality_level not in allowed_materiality:
            errors.append(
                f"{relative}: materiality level `{materiality_level}` is not allowed by "
                f"relationship type `{rel_type}`"
            )

        if type_def.data.get("evidence_required"):
            derived_from = record.data.get("derived_from", {})
            has_claims = bool(derived_from.get("claims"))
            has_evidence = bool(derived_from.get("evidence"))
            if not has_claims and not has_evidence:
                errors.append(f"{relative}: relationship type `{rel_type}` requires evidence or claims")

    return errors


def evidence_items_have_methodology(record: Record) -> bool:
    evidence = record.data.get("evidence")
    if not isinstance(evidence, list):
        return False
    return any(isinstance(item, dict) and bool(item.get("methodology")) for item in evidence)


def validate_claim_predicates(root: Path, records: list[Record]) -> list[str]:
    errors: list[str] = []
    registered = registered_claim_predicates(records)
    proposed = proposed_claim_predicates(records)

    for record in records:
        if record.kind != "claim":
            continue

        relative = record.path.relative_to(root)
        predicate = str(record.data.get("predicate", ""))
        predicate_def: Record | None = None

        if predicate.startswith("provisional:"):
            proposed_name = predicate.split(":", 1)[1]
            proposed_path = record.data.get("proposed_predicate_definition")
            if not proposed_path:
                errors.append(
                    f"{relative}: provisional predicate `{predicate}` needs "
                    "proposed_predicate_definition"
                )
            else:
                definition_path = root / str(proposed_path)
                if not definition_path.exists():
                    errors.append(
                        f"{relative}: proposed_predicate_definition `{proposed_path}` does not exist"
                    )
            if proposed_name not in proposed:
                errors.append(
                    f"{relative}: provisional predicate `{predicate}` has no proposed "
                    "claim_predicate record"
                )
            else:
                predicate_def = proposed[proposed_name]
        else:
            if predicate not in registered:
                errors.append(f"{relative}: claim predicate `{predicate}` is not registered")
            else:
                predicate_def = registered[predicate]

        if predicate_def is None:
            continue

        allowed_support = predicate_def.data.get("allowed_support_type", [])
        support_type = record.data.get("support_type")
        if allowed_support and support_type not in allowed_support:
            errors.append(
                f"{relative}: support_type `{support_type}` is not allowed by predicate "
                f"`{predicate}`"
            )

    return errors


def validate_evidence_policy(
    root: Path, records: list[Record], id_map: dict[str, Record]
) -> list[str]:
    errors: list[str] = []

    for record in records:
        relative = record.path.relative_to(root)

        for path, value in walk_strings(record.data):
            if value == "anonymous_to_maintainers":
                dotted = ".".join(path) or "$"
                errors.append(f"{relative}: {dotted} uses hidden attribution `anonymous_to_maintainers`")

        if record.kind in NO_TRUTH_FIELDS_KINDS:
            for field in ("status", "confidence"):
                if field in record.data:
                    errors.append(
                        f"{relative}: canonical `{record.kind}` records must not store `{field}`; "
                        "derive review state locally"
                    )

        if record.kind == "validation" and "confidence" in record.data:
            errors.append(
                f"{relative}: validation records must not store `confidence`; derive review state locally"
            )

        if record.kind == "challenge" and "status" in record.data:
            errors.append(
                f"{relative}: challenge records must not store `status`; use addressed_by, "
                "withdrawn_by, or superseded_by"
            )

        if record.kind in NO_AUTHOR_FIELD_KINDS and "author" in record.data:
            errors.append(f"{relative}: use `submitted_by`, not `author`")

        if record.kind == "evidence":
            evidence_class = str(record.data.get("evidence_class", ""))
            if evidence_class in OLD_EVIDENCE_CLASSES:
                errors.append(f"{relative}: use plain v1 evidence_class labels, not `{evidence_class}`")
            if evidence_class in EVIDENCE_CLASSES_REQUIRING_ACCESS:
                if "source_attribution" not in record.data:
                    errors.append(f"{relative}: evidence must declare source_attribution")
                if not isinstance(record.data.get("source_access"), dict):
                    errors.append(f"{relative}: evidence must declare source_access")
                if "risk_flags" not in record.data:
                    errors.append(f"{relative}: evidence must declare risk_flags")
            if evidence_class in LOW_TRUST_EVIDENCE_CLASSES and not record.data.get("risk_flags"):
                errors.append(f"{relative}: low-trust evidence must include at least one risk_flag")

        if record.kind == "claim":
            support_type = str(record.data.get("support_type", ""))
            evidence_ids = evidence_ids_for_claim(record)
            evidence_classes = evidence_support_classes(evidence_ids, id_map)
            methodology_present = bool(record.data.get("methodology")) or evidence_items_have_methodology(
                record
            )

            if support_type == "direct" and evidence_classes and evidence_classes <= {"rumor"}:
                errors.append(
                    f"{relative}: direct support_type cannot rely only on rumor evidence"
                )
            if support_type == "inferred" and len(evidence_ids) < 2 and not methodology_present:
                errors.append(
                    f"{relative}: inferred support_type needs multiple evidence records or methodology"
                )
            if support_type == "private_attestation" and not (
                evidence_classes & {"firsthand_private", "anonymous_internal"}
            ):
                errors.append(
                    f"{relative}: private_attestation support_type needs firsthand_private or "
                    "anonymous_internal evidence"
                )
            if support_type == "rumor" and "rumor" not in evidence_classes:
                errors.append(f"{relative}: rumor support_type needs rumor evidence")

    return errors


def source_artifact_refs(record: Record) -> list[str]:
    value = record.data.get("source_artifacts", [])
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def is_safe_relative_path(path_text: str) -> bool:
    path = Path(path_text)
    return not path.is_absolute() and ".." not in path.parts


def is_allowed_source_artifact_path(path_text: str) -> bool:
    path = Path(path_text)
    return (
        is_safe_relative_path(path_text)
        and len(path.parts) >= 3
        and Path(*path.parts[:2]) == SOURCE_ARTIFACTS_ROOT
        and path.suffix.lower() in SOURCE_ARTIFACT_SUFFIXES
    )


def referenced_source_artifacts(records: list[Record]) -> set[str]:
    refs: set[str] = set()
    for record in records:
        refs.update(source_artifact_refs(record))
    return refs


def source_artifact_files(root: Path) -> list[Path]:
    artifacts = root / ARTIFACTS_ROOT
    if not artifacts.exists():
        return []
    return sorted(path for path in artifacts.rglob("*") if path.is_file())


def validate_source_artifacts(root: Path, records: list[Record]) -> list[str]:
    errors: list[str] = []
    refs = referenced_source_artifacts(records)

    for record in records:
        if "source_artifacts" in record.data and record.kind not in {"source", "evidence"}:
            errors.append(
                f"{record.path.relative_to(root)}: source_artifacts is only allowed on "
                "source or evidence records"
            )
        for artifact in source_artifact_refs(record):
            if not is_allowed_source_artifact_path(artifact):
                errors.append(
                    f"{record.path.relative_to(root)}: source_artifacts path `{artifact}` must "
                    "stay under artifacts/sources/ and use png, jpg, jpeg, or pdf"
                )
                continue
            artifact_path = root / artifact
            if not artifact_path.exists():
                errors.append(
                    f"{record.path.relative_to(root)}: source_artifacts path `{artifact}` does not exist"
                )
                continue
            if artifact_path.stat().st_size > MAX_SOURCE_ARTIFACT_BYTES:
                errors.append(
                    f"{artifact}: source artifact exceeds {MAX_SOURCE_ARTIFACT_BYTES} bytes"
                )

    for artifact_path in source_artifact_files(root):
        relative = artifact_path.relative_to(root)
        relative_text = str(relative)
        if len(relative.parts) < 2 or Path(*relative.parts[:2]) != SOURCE_ARTIFACTS_ROOT:
            errors.append(f"{relative_text}: artifact files must live under artifacts/sources/")
            continue
        if artifact_path.suffix.lower() not in SOURCE_ARTIFACT_SUFFIXES:
            errors.append(
                f"{relative_text}: source artifact file type must be png, jpg, jpeg, or pdf"
            )
            continue
        if relative_text not in refs:
            errors.append(f"{relative_text}: source artifact is not referenced by any source/evidence record")
        if artifact_path.stat().st_size > MAX_SOURCE_ARTIFACT_BYTES:
            errors.append(f"{relative_text}: source artifact exceeds {MAX_SOURCE_ARTIFACT_BYTES} bytes")

    return sorted(set(errors))


def source_has_preservation(record: Record, evidence_records: list[Record]) -> bool:
    if record.data.get("archive_url") or record.data.get("content_hash") or source_artifact_refs(record):
        return True
    for evidence in evidence_records:
        if evidence.data.get("source") != record.id:
            continue
        if evidence.data.get("excerpt") or source_artifact_refs(evidence):
            return True
    return False


def lint_warning(
    root: Path,
    record: Record,
    code: str,
    message: str,
    hint: str | None = None,
    related_ids: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "code": code,
        "path": str(record.path.relative_to(root)),
        "json_pointer": None,
        "message": message,
        "hint": hint,
        "record_id": record.id or None,
        "related_ids": related_ids or [],
    }


def preservation_policy_warnings(root: Path, records: list[Record]) -> list[dict[str, Any]]:
    evidence_records = [record for record in records if record.kind == "evidence"]
    warnings: list[dict[str, Any]] = []
    for record in records:
        if record.kind != "source":
            continue
        source_type = str(record.data.get("source_type", ""))
        if source_type not in MUTABLE_WEB_SOURCE_TYPES:
            continue
        if source_has_preservation(record, evidence_records):
            continue
        warnings.append(
            lint_warning(
                root,
                record,
                "mutable_source_without_preservation",
                "Mutable web-like source has no archive_url, content_hash, source_artifacts, "
                "or linked evidence excerpt.",
                "Add archive_url when possible; otherwise add bounded evidence excerpt, "
                "content_hash, or a small referenced source_artifacts file.",
            )
        )
    return warnings


def normalize_duplicate_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        text = str(value)
    else:
        text = json_dumps(value)
    return re.sub(r"\s+", " ", text.strip().lower())


def normalize_duplicate_name(value: Any) -> str:
    text = normalize_duplicate_text(value)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_duplicate_url(value: Any) -> str:
    text = normalize_duplicate_text(value)
    if not text:
        return ""
    text = re.sub(r"#.*$", "", text)
    return text.rstrip("/")


def duplicate_scalar_values(value: Any) -> list[str]:
    if isinstance(value, list):
        texts = [
            normalize_duplicate_text(item)
            for item in value
            if isinstance(item, (str, int, float, bool))
        ]
        return sorted({text for text in texts if text})
    text = normalize_duplicate_text(value)
    return [text] if text else []


def duplicate_resolved(record: Record) -> bool:
    state = record.data.get("state")
    return bool(
        record.data.get("duplicate_of")
        or record.data.get("superseded_by")
        or record.data.get("withdrawn_by")
        or state in {"merged", "retired"}
    )


def add_duplicate_signature(
    groups: dict[tuple[str, ...], list[Record]],
    record: Record,
    code: str,
    message: str,
    signature: tuple[str, ...],
) -> None:
    if not record.id or not signature or any(part == "" for part in signature):
        return
    groups.setdefault((code, message, *signature), []).append(record)


def add_entity_duplicate_signatures(
    groups: dict[tuple[str, ...], list[Record]], record: Record
) -> None:
    entity_type = normalize_duplicate_text(record.data.get("entity_type"))
    name = normalize_duplicate_name(record.data.get("name"))
    if entity_type and name:
        add_duplicate_signature(
            groups,
            record,
            "possible_duplicate_entity_name",
            "Possible duplicate entity: same normalized name and entity_type.",
            (entity_type, name),
        )

    identifiers = record.data.get("identifiers", {})
    if not isinstance(identifiers, dict):
        return
    for key in DUPLICATE_ENTITY_IDENTIFIER_KEYS:
        for value in duplicate_scalar_values(identifiers.get(key)):
            add_duplicate_signature(
                groups,
                record,
                "possible_duplicate_entity_identifier",
                f"Possible duplicate entity: same {key} and entity_type.",
                (entity_type, key, value),
            )


def add_source_duplicate_signatures(
    groups: dict[tuple[str, ...], list[Record]], record: Record
) -> None:
    source_fields = (
        ("url", "possible_duplicate_source_url", "Possible duplicate source: same URL."),
        (
            "archive_url",
            "possible_duplicate_source_archive_url",
            "Possible duplicate source: same archive_url.",
        ),
        (
            "accession_number",
            "possible_duplicate_source_accession",
            "Possible duplicate source: same accession_number.",
        ),
        (
            "content_hash",
            "possible_duplicate_source_content_hash",
            "Possible duplicate source: same content_hash.",
        ),
    )
    for field, code, message in source_fields:
        values = duplicate_scalar_values(record.data.get(field))
        if field in {"url", "archive_url"}:
            values = [normalize_duplicate_url(value) for value in values]
        for value in values:
            if value:
                add_duplicate_signature(groups, record, code, message, (field, value))


def add_evidence_duplicate_signatures(
    groups: dict[tuple[str, ...], list[Record]], record: Record
) -> None:
    source = normalize_duplicate_text(record.data.get("source"))
    locator = record.data.get("locator")
    if source and isinstance(locator, dict) and locator:
        add_duplicate_signature(
            groups,
            record,
            "possible_duplicate_evidence_locator",
            "Possible duplicate evidence: same source and locator.",
            (source, json_dumps(locator)),
        )

    excerpt = normalize_duplicate_text(record.data.get("excerpt"))
    if source and len(excerpt) >= 20:
        add_duplicate_signature(
            groups,
            record,
            "possible_duplicate_evidence_excerpt",
            "Possible duplicate evidence: same source and normalized excerpt.",
            (source, excerpt),
        )


def add_claim_duplicate_signatures(
    groups: dict[tuple[str, ...], list[Record]], record: Record
) -> None:
    subject = normalize_duplicate_text(record.data.get("subject"))
    predicate = normalize_duplicate_text(record.data.get("predicate"))
    evidence_signature = "\x1f".join(sorted(set(evidence_ids_for_claim(record))))
    add_duplicate_signature(
        groups,
        record,
        "possible_duplicate_claim_core",
        "Possible duplicate claim: same subject, predicate, object, scope, and evidence set.",
        (
            subject,
            predicate,
            json_dumps(record.data.get("object")),
            json_dumps(record.data.get("qualifiers", {})),
            json_dumps(record.data.get("time_scope", {})),
            json_dumps(record.data.get("period", {})),
            json_dumps(record.data.get("as_of")),
            evidence_signature,
        ),
    )

    statement = normalize_duplicate_name(record.data.get("statement"))
    if statement:
        add_duplicate_signature(
            groups,
            record,
            "possible_duplicate_claim_statement",
            "Possible duplicate claim: same normalized statement.",
            (statement,),
        )


def add_relationship_duplicate_signatures(
    groups: dict[tuple[str, ...], list[Record]], record: Record
) -> None:
    participants = "\x1f".join(
        f"{role}={entity_id}" for role, entity_id in sorted(relationship_participant_items(record))
    )
    add_duplicate_signature(
        groups,
        record,
        "possible_duplicate_relationship_core",
        "Possible duplicate relationship: same type, participants, scope, direction, and time.",
        (
            normalize_duplicate_text(record.data.get("type")),
            participants,
            json_dumps(record.data.get("scope", {})),
            json_dumps(record.data.get("direction", {})),
            json_dumps(record.data.get("time_scope", {})),
            json_dumps(record.data.get("effective_at")),
        ),
    )


def duplicate_detection_warnings(root: Path, records: list[Record]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, ...], list[Record]] = {}
    for record in records:
        if not record.id or is_archived_path(root, record.path) or duplicate_resolved(record):
            continue
        if record.kind == "entity":
            add_entity_duplicate_signatures(groups, record)
        elif record.kind == "source":
            add_source_duplicate_signatures(groups, record)
        elif record.kind == "evidence":
            add_evidence_duplicate_signatures(groups, record)
        elif record.kind == "claim":
            add_claim_duplicate_signatures(groups, record)
        elif record.kind == "relationship":
            add_relationship_duplicate_signatures(groups, record)

    warnings: list[dict[str, Any]] = []
    for key in sorted(groups):
        code, message, *_ = key
        unique_records = {
            record.id: record
            for record in groups[key]
            if record.id and not duplicate_resolved(record)
        }
        if len(unique_records) < 2:
            continue
        group = sorted(unique_records.values(), key=lambda item: item.id)
        primary = group[0]
        warnings.append(
            lint_warning(
                root,
                primary,
                code,
                message,
                DUPLICATE_WARNING_HINT,
                [record.id for record in group[1:]],
            )
        )
    return sorted(warnings, key=lambda item: (item["path"], item["code"], item["related_ids"]))


def validate_archive_policy(root: Path, records: list[Record], id_map: dict[str, Record]) -> list[str]:
    errors: list[str] = []
    archived_ids = {
        record.id
        for record in records
        if record.id and is_archived_path(root, record.path)
    }
    open_challenge_targets = {
        str(record.data.get("target"))
        for record in records
        if record.kind == "challenge" and is_open_challenge(record_doc(root, record, include_data=True))
    }

    for record in records:
        relative = record.path.relative_to(root)
        is_archived = is_archived_path(root, record.path)

        if is_archived and not any(record.data.get(field) for field in ARCHIVE_REQUIRED_FIELDS):
            errors.append(
                f"{relative}: archived records must include superseded_by, duplicate_of, "
                "or archive_reason"
            )

        if is_archived and record.id in open_challenge_targets and not any(
            record.data.get(field) for field in ARCHIVE_REQUIRED_FIELDS
        ):
            errors.append(
                f"{relative}: archived record has open challenges and needs superseded_by, "
                "duplicate_of, or archive_reason"
            )

        if is_archived:
            continue

        for path, value in walk_strings(record.data):
            if path == ("id",) or not is_reference(value) or value not in archived_ids:
                continue
            if path and path[0] in CURRENT_TO_ARCHIVE_ALLOWED_FIELDS:
                continue
            dotted = ".".join(path) or "$"
            errors.append(
                f"{relative}: current record field `{dotted}` references archived record `{value}`; "
                "use a current replacement or pass --include-archive in read commands"
            )

    return errors


def record_label(record: Record) -> str:
    for key in ("name", "title", "statement", "question", "summary", "label"):
        value = record.data.get(key)
        if isinstance(value, str) and value:
            return value
    return record.id


def build_graph_data(root: Path, records: list[Record]) -> dict[str, Any]:
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    for record in records:
        if not record.id:
            continue
        nodes.append(
            {
                "id": record.id,
                "kind": record.kind,
                "label": record_label(record),
                "path": str(record.path.relative_to(root)),
            }
        )

        if record.kind == "relationship":
            participants = record.data.get("participants", [])
            if isinstance(participants, list):
                participant_items = [
                    (str(item.get("role")), item.get("entity"))
                    for item in participants
                    if isinstance(item, dict)
                ]
            elif isinstance(participants, dict):
                participant_items = list(participants.items())
            else:
                participant_items = []
            for role, participant_id in participant_items:
                if isinstance(participant_id, str) and is_reference(participant_id):
                    edges.append(
                        {
                            "from": participant_id,
                            "to": record.id,
                            "type": f"participant:{role}",
                        }
                    )

        if record.kind == "claim":
            subject = record.data.get("subject")
            obj = record.data.get("object")
            predicate = record.data.get("predicate", "claims")
            if isinstance(subject, str) and is_reference(subject):
                edges.append({"from": subject, "to": record.id, "type": "subject"})
            if isinstance(obj, str) and is_reference(obj):
                edges.append({"from": record.id, "to": obj, "type": str(predicate)})

        for path, value in walk_strings(record.data):
            if path and path[-1] == "id":
                continue
            if is_reference(value):
                edges.append(
                    {
                        "from": record.id,
                        "to": value,
                        "type": "references",
                        "field": ".".join(path),
                    }
                )

    unique_edges = []
    seen_edges: set[tuple[str, str, str, str]] = set()
    for edge in edges:
        key = (
            str(edge.get("from")),
            str(edge.get("to")),
            str(edge.get("type")),
            str(edge.get("field", "")),
        )
        if key in seen_edges:
            continue
        seen_edges.add(key)
        unique_edges.append(edge)

    return {
        "schema_version": 1,
        "node_count": len(nodes),
        "edge_count": len(unique_edges),
        "nodes": nodes,
        "edges": unique_edges,
    }


INDEX_SCHEMA_SQL = """
create table records (
  id text primary key,
  kind text not null,
  schema_version integer,
  path text not null,
  archived integer not null default 0,
  label text,
  json text not null
);

create table refs (
  source_id text not null,
  target_id text not null,
  field_path text not null
);

create table edges (
  source_id text not null,
  target_id text not null,
  edge_type text not null,
  field_path text
);

create table entities (
  id text primary key,
  entity_type text not null,
  name text not null,
  ticker text,
  cik text
);

create table identifiers (
  record_id text not null,
  id_type text not null,
  id_value text not null
);

create table evidence (
  id text primary key,
  evidence_class text not null,
  source_id text,
  content_mode text,
  observed_at text
);

create table claims (
  id text primary key,
  predicate text not null,
  support_type text not null,
  subject text,
  object text,
  period_start text,
  period_end text,
  as_of text
);

create table relationships (
  id text primary key,
  relationship_type text not null,
  primary_subject text,
  effective_at text,
  period_start text,
  period_end text
);

create table relationship_participants (
  relationship_id text not null,
  role text not null,
  entity_id text not null
);

create table relationship_scope (
  relationship_id text not null,
  scope_type text not null,
  scope_id text not null
);

create table metrics (
  id text primary key,
  entity_id text not null,
  metric_definition text not null,
  value real,
  unit text,
  value_basis text,
  period_start text,
  period_end text,
  as_of text
);

create table events (
  id text primary key,
  event_type text not null,
  event_state text,
  occurred_at text,
  effective_at text
);

create table validations (
  id text primary key,
  target_id text not null,
  verdict text not null,
  submitted_by text
);

create table challenges (
  id text primary key,
  target_id text not null,
  challenge_type text not null,
  submitted_by text
);

create table predicate_definitions (
  id text primary key,
  ontology_version integer,
  json text not null
);

create table metric_definitions (
  id text primary key,
  ontology_version integer,
  json text not null
);

create table relationship_type_definitions (
  id text primary key,
  ontology_version integer,
  json text not null
);

create virtual table records_fts using fts5(
  id unindexed,
  kind unindexed,
  label,
  body
);

create index refs_source_idx on refs(source_id);
create index refs_target_idx on refs(target_id);
create index edges_source_idx on edges(source_id);
create index edges_target_idx on edges(target_id);
create index records_kind_idx on records(kind, archived);
create index validations_target_idx on validations(target_id);
create index challenges_target_idx on challenges(target_id);
"""


def index_path(root: Path) -> Path:
    return root / ".local" / "index.sqlite"


def json_dumps(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str, ensure_ascii=False)


def as_scalar_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    return json_dumps(value)


def is_archived_path(root: Path, path: Path) -> bool:
    try:
        relative = path.relative_to(root)
    except ValueError:
        relative = path
    return bool(relative.parts and relative.parts[0] == "archive")


def period_range(data: dict[str, Any]) -> tuple[str | None, str | None]:
    for key in ("time_scope", "period"):
        value = data.get(key)
        if isinstance(value, dict):
            start = value.get("start") or value.get("period_start")
            end = value.get("end") or value.get("period_end")
            if start is not None or end is not None:
                return as_scalar_text(start), as_scalar_text(end)
    return None, None


def reference_values(value: Any) -> list[str]:
    return sorted({text for _, text in walk_strings(value) if is_reference(text)})


def record_ref_rows(record: Record) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    if not record.id:
        return rows
    for path, value in walk_strings(record.data):
        if path == ("id",):
            continue
        if is_reference(value):
            rows.append((record.id, value, ".".join(path)))
    return rows


def relationship_participant_items(record: Record) -> list[tuple[str, str]]:
    participants = record.data.get("participants", [])
    if not isinstance(participants, list):
        return []
    items: list[tuple[str, str]] = []
    for participant in participants:
        if not isinstance(participant, dict):
            continue
        role = participant.get("role")
        entity = participant.get("entity")
        if isinstance(role, str) and isinstance(entity, str):
            items.append((role, entity))
    return items


def relationship_primary_subject(record: Record) -> str | None:
    participants = relationship_participant_items(record)
    preferred_roles = (
        "buyer",
        "customer",
        "dependent",
        "exposed_entity",
        "owner",
        "product",
        "seller",
        "supplier",
    )
    for preferred in preferred_roles:
        for role, entity_id in participants:
            if role == preferred:
                return entity_id
    return participants[0][1] if participants else None


def create_index_database(root: Path, records: list[Record]) -> dict[str, Any]:
    output_path = index_path(root)
    output_path.parent.mkdir(exist_ok=True)
    if output_path.exists():
        output_path.unlink()

    graph = build_graph_data(root, records)
    sorted_records = sorted(records, key=lambda item: item.id)

    with sqlite3.connect(output_path) as conn:
        conn.executescript(INDEX_SCHEMA_SQL)
        for record in sorted_records:
            if not record.id:
                continue
            relative_path = str(record.path.relative_to(root))
            body = json_dumps(record.data)
            conn.execute(
                """
                insert into records(id, kind, schema_version, path, archived, label, json)
                values (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.id,
                    record.kind,
                    record.data.get("schema_version"),
                    relative_path,
                    1 if is_archived_path(root, record.path) else 0,
                    record_label(record),
                    body,
                ),
            )
            conn.execute(
                "insert into records_fts(id, kind, label, body) values (?, ?, ?, ?)",
                (record.id, record.kind, record_label(record), body),
            )
            conn.executemany(
                "insert into refs(source_id, target_id, field_path) values (?, ?, ?)",
                record_ref_rows(record),
            )

            data = record.data
            if record.kind == "entity":
                identifiers = data.get("identifiers", {})
                ticker = identifiers.get("ticker") if isinstance(identifiers, dict) else None
                cik = identifiers.get("cik") if isinstance(identifiers, dict) else None
                conn.execute(
                    "insert into entities(id, entity_type, name, ticker, cik) values (?, ?, ?, ?, ?)",
                    (
                        record.id,
                        str(data.get("entity_type")),
                        str(data.get("name")),
                        as_scalar_text(ticker),
                        as_scalar_text(cik),
                    ),
                )
                if isinstance(identifiers, dict):
                    for id_type in sorted(identifiers):
                        id_value = identifiers[id_type]
                        values = id_value if isinstance(id_value, list) else [id_value]
                        for value in values:
                            conn.execute(
                                "insert into identifiers(record_id, id_type, id_value) values (?, ?, ?)",
                                (record.id, str(id_type), as_scalar_text(value) or ""),
                            )

            elif record.kind == "evidence":
                conn.execute(
                    """
                    insert into evidence(id, evidence_class, source_id, content_mode, observed_at)
                    values (?, ?, ?, ?, ?)
                    """,
                    (
                        record.id,
                        str(data.get("evidence_class")),
                        as_scalar_text(data.get("source")),
                        as_scalar_text(data.get("content_mode")),
                        as_scalar_text(data.get("observed_at")),
                    ),
                )

            elif record.kind == "claim":
                period_start, period_end = period_range(data)
                conn.execute(
                    """
                    insert into claims(
                      id, predicate, support_type, subject, object, period_start, period_end, as_of
                    )
                    values (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record.id,
                        str(data.get("predicate")),
                        str(data.get("support_type")),
                        as_scalar_text(data.get("subject")),
                        as_scalar_text(data.get("object")),
                        period_start,
                        period_end,
                        as_scalar_text(data.get("as_of")),
                    ),
                )

            elif record.kind == "relationship":
                period_start, period_end = period_range(data)
                conn.execute(
                    """
                    insert into relationships(
                      id, relationship_type, primary_subject, effective_at, period_start, period_end
                    )
                    values (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record.id,
                        str(data.get("type")),
                        relationship_primary_subject(record),
                        as_scalar_text(data.get("effective_at")),
                        period_start,
                        period_end,
                    ),
                )
                conn.executemany(
                    """
                    insert into relationship_participants(relationship_id, role, entity_id)
                    values (?, ?, ?)
                    """,
                    [(record.id, role, entity_id) for role, entity_id in relationship_participant_items(record)],
                )
                scope = data.get("scope", {})
                if isinstance(scope, dict):
                    for scope_type in sorted(scope):
                        for scope_id in reference_values(scope[scope_type]):
                            conn.execute(
                                """
                                insert into relationship_scope(relationship_id, scope_type, scope_id)
                                values (?, ?, ?)
                                """,
                                (record.id, str(scope_type), scope_id),
                            )

            elif record.kind == "metric":
                period_start, period_end = period_range(data)
                conn.execute(
                    """
                    insert into metrics(
                      id, entity_id, metric_definition, value, unit, value_basis,
                      period_start, period_end, as_of
                    )
                    values (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record.id,
                        str(data.get("entity")),
                        str(data.get("metric_definition")),
                        data.get("value"),
                        as_scalar_text(data.get("unit")),
                        as_scalar_text(data.get("value_basis")),
                        period_start,
                        period_end,
                        as_scalar_text(data.get("as_of")),
                    ),
                )

            elif record.kind == "event":
                conn.execute(
                    """
                    insert into events(id, event_type, event_state, occurred_at, effective_at)
                    values (?, ?, ?, ?, ?)
                    """,
                    (
                        record.id,
                        str(data.get("event_type")),
                        as_scalar_text(data.get("event_state")),
                        as_scalar_text(data.get("occurred_at")),
                        as_scalar_text(data.get("effective_at")),
                    ),
                )

            elif record.kind == "validation":
                conn.execute(
                    "insert into validations(id, target_id, verdict, submitted_by) values (?, ?, ?, ?)",
                    (
                        record.id,
                        str(data.get("target")),
                        str(data.get("verdict")),
                        as_scalar_text(data.get("submitted_by")),
                    ),
                )

            elif record.kind == "challenge":
                conn.execute(
                    """
                    insert into challenges(id, target_id, challenge_type, submitted_by)
                    values (?, ?, ?, ?)
                    """,
                    (
                        record.id,
                        str(data.get("target")),
                        str(data.get("challenge_type")),
                        as_scalar_text(data.get("submitted_by")),
                    ),
                )

            elif record.kind == "claim_predicate":
                conn.execute(
                    "insert into predicate_definitions(id, ontology_version, json) values (?, ?, ?)",
                    (record.id, data.get("ontology_version"), body),
                )

            elif record.kind == "metric_definition":
                conn.execute(
                    "insert into metric_definitions(id, ontology_version, json) values (?, ?, ?)",
                    (record.id, data.get("ontology_version"), body),
                )

            elif record.kind == "relationship_type":
                conn.execute(
                    """
                    insert into relationship_type_definitions(id, ontology_version, json)
                    values (?, ?, ?)
                    """,
                    (record.id, data.get("ontology_version"), body),
                )

        conn.executemany(
            "insert into edges(source_id, target_id, edge_type, field_path) values (?, ?, ?, ?)",
            [
                (
                    str(edge.get("from")),
                    str(edge.get("to")),
                    str(edge.get("type")),
                    as_scalar_text(edge.get("field")),
                )
                for edge in graph["edges"]
            ],
        )
        conn.commit()

    return {
        "index_path": str(output_path),
        "records_indexed": len([record for record in records if record.id]),
        "edge_count": int(graph["edge_count"]),
        "ref_count": sum(len(record_ref_rows(record)) for record in records),
    }


def connect_index(root: Path) -> sqlite3.Connection:
    db_path = index_path(root)
    if not db_path.exists():
        raise FileNotFoundError(f"{db_path.relative_to(root)} does not exist; run `fo index build`")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def row_to_record(row: sqlite3.Row, include_data: bool = False) -> dict[str, Any]:
    record = {
        "id": row["id"],
        "kind": row["kind"],
        "schema_version": row["schema_version"],
        "path": row["path"],
        "archived": bool(row["archived"]),
        "label": row["label"],
    }
    if include_data:
        record["data"] = json.loads(row["json"])
    return record


def indexed_record(conn: sqlite3.Connection, record_id: str) -> dict[str, Any] | None:
    row = conn.execute("select * from records where id = ?", (record_id,)).fetchone()
    if row is None:
        return None
    return row_to_record(row, include_data=True)


def fetch_records(
    conn: sqlite3.Connection, record_ids: list[str], include_data: bool = False
) -> list[dict[str, Any]]:
    if not record_ids:
        return []
    rows = conn.execute(
        f"select * from records where id in ({','.join('?' for _ in record_ids)}) order by kind, id",
        record_ids,
    ).fetchall()
    return [row_to_record(row, include_data=include_data) for row in rows]


def load_index_record_map(conn: sqlite3.Connection) -> dict[str, Record]:
    rows = conn.execute("select id, path, json from records order by id").fetchall()
    return {
        str(row["id"]): Record(path=Path(str(row["path"])), data=json.loads(str(row["json"])))
        for row in rows
    }


def result_envelope(
    command: str,
    root: Path,
    ok: bool = True,
    errors: list[dict[str, Any]] | None = None,
    warnings: list[dict[str, Any]] | None = None,
    **payload: Any,
) -> dict[str, Any]:
    return {
        "ok": ok,
        "command": command,
        "repo_root": str(root),
        "warnings": warnings or [],
        "errors": errors or [],
        **payload,
    }


def print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True, default=str))


def command_error(code: str, message: str, hint: str | None = None) -> dict[str, Any]:
    return {
        "code": code,
        "path": "",
        "json_pointer": None,
        "message": message,
        "hint": hint,
        "record_id": None,
        "related_ids": [],
    }


def fts_query(query: str) -> str:
    return " ".join(re.findall(r"[A-Za-z0-9_]+", query.lower()))


def search_rows(
    conn: sqlite3.Connection,
    query: str,
    include_archive: bool = False,
    limit: int = 20,
) -> list[sqlite3.Row]:
    archive_clause = "" if include_archive else "and r.archived = 0"
    query_text = fts_query(query)
    if query_text:
        try:
            return conn.execute(
                f"""
                select r.*
                from records_fts
                join records r on r.id = records_fts.id
                where records_fts match ? {archive_clause}
                order by r.kind, r.id
                limit ?
                """,
                (query_text, limit),
            ).fetchall()
        except sqlite3.OperationalError:
            pass

    like = f"%{query.lower()}%"
    return conn.execute(
        f"""
        select r.*
        from records r
        where lower(r.id || ' ' || coalesce(r.label, '') || ' ' || r.json) like ?
        {archive_clause}
        order by r.kind, r.id
        limit ?
        """,
        (like, limit),
    ).fetchall()


def related_record_ids(conn: sqlite3.Connection, record_id: str) -> list[str]:
    rows = conn.execute(
        """
        select target_id as id from refs where source_id = ?
        union
        select source_id as id from refs where target_id = ?
        union
        select target_id as id from edges where source_id = ?
        union
        select source_id as id from edges where target_id = ?
        order by id
        """,
        (record_id, record_id, record_id, record_id),
    ).fetchall()
    return [str(row["id"]) for row in rows if str(row["id"]) != record_id]


def target_review_records(
    conn: sqlite3.Connection, table_name: str, target_id: str
) -> list[dict[str, Any]]:
    rows = conn.execute(
        f"""
        select r.*
        from {table_name} t
        join records r on r.id = t.id
        where t.target_id = ?
        order by r.id
        """,
        (target_id,),
    ).fetchall()
    return [row_to_record(row, include_data=True) for row in rows]


def outgoing_refs(conn: sqlite3.Connection, record_id: str) -> list[dict[str, str]]:
    rows = conn.execute(
        "select target_id, field_path from refs where source_id = ? order by field_path, target_id",
        (record_id,),
    ).fetchall()
    return [{"target_id": row["target_id"], "field_path": row["field_path"]} for row in rows]


def incoming_refs(conn: sqlite3.Connection, record_id: str) -> list[dict[str, str]]:
    rows = conn.execute(
        "select source_id, field_path from refs where target_id = ? order by source_id, field_path",
        (record_id,),
    ).fetchall()
    return [{"source_id": row["source_id"], "field_path": row["field_path"]} for row in rows]


def graph_edge_rows(conn: sqlite3.Connection, record_id: str) -> list[dict[str, str | None]]:
    rows = conn.execute(
        """
        select source_id, target_id, edge_type, field_path
        from edges
        where source_id = ? or target_id = ?
        order by source_id, target_id, edge_type, field_path
        """,
        (record_id, record_id),
    ).fetchall()
    return [
        {
            "source_id": row["source_id"],
            "target_id": row["target_id"],
            "edge_type": row["edge_type"],
            "field_path": row["field_path"],
        }
        for row in rows
    ]


def evidence_ids_for_record(
    record: Record, id_map: dict[str, Record], seen: set[str] | None = None
) -> list[str]:
    seen = set(seen or set())
    if record.id in seen:
        return []
    seen.add(record.id)

    if record.kind == "evidence":
        return [record.id]
    if record.kind == "claim":
        return evidence_ids_for_claim(record)
    if record.kind == "relationship":
        return evidence_ids_for_relationship(record, id_map)
    if record.kind in {"metric", "event"}:
        return as_reference_list(record.data.get("evidence"))
    if record.kind == "validation":
        return evidence_ids_for_validation(record, id_map)
    if record.kind == "challenge":
        depends_on = record.data.get("depends_on", {})
        if isinstance(depends_on, dict):
            return evidence_ids_from_dependencies(dependency_ids(depends_on), id_map, seen)
    if record.kind == "thesis":
        depends_on = record.data.get("depends_on", {})
        if isinstance(depends_on, dict):
            return evidence_ids_from_dependencies(dependency_ids(depends_on), id_map, seen)
    return []


def dependency_ids(value: Any) -> dict[str, list[str]]:
    if not isinstance(value, dict):
        return {key: [] for key in DEPENDENCY_KEYS}
    return {key: sorted(set(as_reference_list(value.get(key)))) for key in DEPENDENCY_KEYS}


def evidence_ids_from_dependencies(
    dependencies: dict[str, list[str]],
    id_map: dict[str, Record],
    seen: set[str] | None = None,
) -> list[str]:
    seen = set(seen or set())
    evidence_ids: set[str] = set(dependencies.get("evidence", []))
    for key in ("claims", "relationships", "theses", "metrics", "events"):
        for record_id in dependencies.get(key, []):
            record = id_map.get(record_id)
            if record:
                evidence_ids.update(evidence_ids_for_record(record, id_map, seen))
    return sorted(evidence_ids)


def is_open_challenge(record: dict[str, Any]) -> bool:
    data = record.get("data", {})
    return not any(data.get(key) for key in ("addressed_by", "withdrawn_by", "superseded_by"))


def sorted_counts(values: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return {key: counts[key] for key in sorted(counts)}


def risk_flags_for(data: dict[str, Any]) -> list[str]:
    return sorted({str(flag) for flag in data.get("risk_flags", []) if isinstance(flag, str)})


def source_id_for_evidence(record_id: str, id_map: dict[str, Record]) -> str | None:
    record = id_map.get(record_id)
    if record and record.kind == "evidence":
        source_id = record.data.get("source")
        return str(source_id) if isinstance(source_id, str) else None
    return None


def source_perspective_for_source(source_id: str, id_map: dict[str, Record]) -> str:
    record = id_map.get(source_id)
    if not record or record.kind != "source":
        return "unknown"
    perspective = record.data.get("source_perspective")
    return str(perspective) if isinstance(perspective, str) and perspective else "unknown"


def source_perspective_summary(
    source_ids: list[str], id_map: dict[str, Record]
) -> dict[str, Any]:
    unique_source_ids = sorted(set(source_ids))
    perspective_by_source = {
        source_id: source_perspective_for_source(source_id, id_map)
        for source_id in unique_source_ids
    }
    independent_ids = sorted(
        source_id
        for source_id, perspective in perspective_by_source.items()
        if perspective in INDEPENDENT_SOURCE_PERSPECTIVES
    )
    company_originated_ids = sorted(
        source_id
        for source_id, perspective in perspective_by_source.items()
        if perspective in COMPANY_ORIGINATED_SOURCE_PERSPECTIVES
    )
    unknown_ids = sorted(
        source_id
        for source_id, perspective in perspective_by_source.items()
        if perspective == "unknown"
    )
    other_ids = sorted(
        source_id
        for source_id in unique_source_ids
        if source_id not in independent_ids
        and source_id not in company_originated_ids
        and source_id not in unknown_ids
    )
    return {
        "source_perspective_counts": sorted_counts(list(perspective_by_source.values())),
        "source_perspective_by_source": perspective_by_source,
        "independent_source_count": len(independent_ids),
        "independent_source_ids": independent_ids,
        "company_originated_source_count": len(company_originated_ids),
        "company_originated_source_ids": company_originated_ids,
        "other_source_ids": other_ids,
        "unknown_perspective_source_ids": unknown_ids,
    }


def record_stub(record: Record) -> dict[str, Any]:
    return {
        "id": record.id,
        "kind": record.kind,
        "label": record_label(record),
        "path": str(record.path),
    }


def evidence_summary(evidence_ids: list[str], id_map: dict[str, Record]) -> dict[str, Any]:
    unique_ids = sorted(set(evidence_ids))
    items: list[dict[str, Any]] = []
    class_values: list[str] = []
    source_ids: list[str] = []
    risk_flags: list[str] = []

    for evidence_id in unique_ids:
        record = id_map.get(evidence_id)
        if not record or record.kind != "evidence":
            continue
        evidence_class = str(record.data.get("evidence_class", ""))
        source_id = source_id_for_evidence(evidence_id, id_map)
        if evidence_class:
            class_values.append(evidence_class)
        if source_id:
            source_ids.append(source_id)
        risk_flags.extend(risk_flags_for(record.data))
        items.append(
            {
                "id": evidence_id,
                "evidence_class": evidence_class,
                "source_id": source_id,
                "content_mode": record.data.get("content_mode"),
                "observed_at": record.data.get("observed_at"),
                "risk_flags": risk_flags_for(record.data),
            }
        )

    evidence_per_source = sorted_counts(source_ids)
    perspective_summary = source_perspective_summary(source_ids, id_map)
    low_trust_ids = [
        item["id"] for item in items if item["evidence_class"] in LOW_TRUST_EVIDENCE_CLASSES
    ]
    private_ids = [item["id"] for item in items if item["evidence_class"] in PRIVATE_EVIDENCE_CLASSES]

    return {
        "evidence_ids": unique_ids,
        "evidence_count": len(items),
        "evidence_class_counts": sorted_counts(class_values),
        "low_trust_evidence_ids": sorted(low_trust_ids),
        "private_evidence_ids": sorted(private_ids),
        "source_independence": {
            "unique_source_count": len(set(source_ids)),
            "source_ids": sorted(set(source_ids)),
            "evidence_per_source": evidence_per_source,
            "reused_source_ids": sorted(
                source_id for source_id, count in evidence_per_source.items() if count > 1
            ),
            **perspective_summary,
        },
        "risk_flags": sorted(set(risk_flags)),
        "items": items,
    }


def validation_path_summary(record: dict[str, Any], id_map: dict[str, Record]) -> dict[str, Any]:
    data = record.get("data", {})
    dependencies = dependency_ids(data.get("depends_on", {}))
    evidence_ids = evidence_ids_from_dependencies(dependencies, id_map)
    source_ids = sorted(
        {
            source_id
            for evidence_id in evidence_ids
            if (source_id := source_id_for_evidence(evidence_id, id_map))
        }
    )
    dependency_parts = [
        f"{key}:{record_id}"
        for key in DEPENDENCY_KEYS
        for record_id in dependencies.get(key, [])
    ]
    signature = "|".join(dependency_parts) or "empty"
    return {
        "id": record["id"],
        "verdict": data.get("verdict"),
        "submitted_by": data.get("submitted_by"),
        "dependency_signature": signature,
        "dependencies": dependencies,
        "evidence_ids": evidence_ids,
        "source_ids": source_ids,
        "risk_flags": risk_flags_for(data),
    }


def summarize_validations(
    validations: list[dict[str, Any]], id_map: dict[str, Record]
) -> dict[str, Any]:
    paths = [validation_path_summary(validation, id_map) for validation in validations]
    signature_counts = sorted_counts([str(path["dependency_signature"]) for path in paths])
    repeated_signatures = {
        signature: count for signature, count in signature_counts.items() if count > 1
    }
    supporting = [
        path
        for path in paths
        if path["verdict"] in SUPPORTING_VERDICTS or path["verdict"] in PARTIAL_VERDICTS
    ]
    contesting = [path for path in paths if path["verdict"] in CONTESTING_VERDICTS]
    stale = [path for path in paths if path["verdict"] in STALE_VERDICTS]
    withdrawals = [path for path in paths if path["verdict"] in WITHDRAWAL_VERDICTS]

    return {
        "total_count": len(paths),
        "by_verdict": sorted_counts([str(path["verdict"]) for path in paths]),
        "supporting_count": len(supporting),
        "contesting_count": len(contesting),
        "stale_count": len(stale),
        "withdrawal_count": len(withdrawals),
        "unique_dependency_path_count": len(signature_counts),
        "repeated_dependency_path_count": sum(count - 1 for count in repeated_signatures.values()),
        "repeated_dependency_paths": repeated_signatures,
        "support_evidence_ids": sorted(
            {evidence_id for path in supporting for evidence_id in path["evidence_ids"]}
        ),
        "contesting_validation_ids": [path["id"] for path in contesting],
        "stale_validation_ids": [path["id"] for path in stale],
        "withdrawal_validation_ids": [path["id"] for path in withdrawals],
        "risk_flags": sorted({flag for path in paths for flag in path["risk_flags"]}),
        "paths": paths,
    }


def challenge_path_summary(record: dict[str, Any], id_map: dict[str, Record]) -> dict[str, Any]:
    data = record.get("data", {})
    dependencies = dependency_ids(data.get("depends_on", {}))
    evidence_ids = evidence_ids_from_dependencies(dependencies, id_map)
    return {
        "id": record["id"],
        "challenge_type": data.get("challenge_type"),
        "submitted_by": data.get("submitted_by"),
        "open": is_open_challenge(record),
        "closure": {
            "addressed_by": data.get("addressed_by"),
            "withdrawn_by": data.get("withdrawn_by"),
            "superseded_by": data.get("superseded_by"),
        },
        "dependencies": dependencies,
        "evidence_ids": evidence_ids,
        "risk_flags": risk_flags_for(data),
    }


def summarize_challenges(
    challenges: list[dict[str, Any]], id_map: dict[str, Record]
) -> dict[str, Any]:
    paths = [challenge_path_summary(challenge, id_map) for challenge in challenges]
    open_paths = [path for path in paths if path["open"]]
    closed_paths = [path for path in paths if not path["open"]]
    return {
        "total_count": len(paths),
        "open_count": len(open_paths),
        "closed_count": len(closed_paths),
        "by_type": sorted_counts([str(path["challenge_type"]) for path in paths]),
        "open_by_type": sorted_counts([str(path["challenge_type"]) for path in open_paths]),
        "open_challenge_ids": [path["id"] for path in open_paths],
        "closed_challenge_ids": [path["id"] for path in closed_paths],
        "contradiction_challenge_ids": [
            path["id"] for path in paths if path["challenge_type"] == "contradiction"
        ],
        "stale_challenge_ids": [
            path["id"] for path in paths if path["challenge_type"] in STALE_CHALLENGE_TYPES
        ],
        "scope_challenge_ids": [
            path["id"] for path in paths if path["challenge_type"] in SCOPE_CHALLENGE_TYPES
        ],
        "challenge_evidence_ids": sorted(
            {evidence_id for path in paths for evidence_id in path["evidence_ids"]}
        ),
        "risk_flags": sorted({flag for path in paths for flag in path["risk_flags"]}),
        "items": paths,
    }


def records_linking_to(
    target_id: str, id_map: dict[str, Record], field_names: tuple[str, ...]
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for record in sorted(id_map.values(), key=lambda item: item.id):
        if record.id == target_id:
            continue
        for field_name in field_names:
            if target_id in as_reference_list(record.data.get(field_name)):
                records.append({**record_stub(record), "field": field_name})
    return records


def contradiction_summary(
    target: Record,
    challenges_summary: dict[str, Any],
    id_map: dict[str, Record],
) -> dict[str, Any]:
    outgoing_ids = sorted(set(as_reference_list(target.data.get("contradicts"))))
    contradicting_evidence_ids = sorted(
        set(as_reference_list(target.data.get("contradicting_evidence")))
    )
    incoming = records_linking_to(target.id, id_map, ("contradicts",))
    challenge_ids = challenges_summary["contradiction_challenge_ids"]
    return {
        "has_contradiction": bool(outgoing_ids or contradicting_evidence_ids or incoming or challenge_ids),
        "outgoing_contradicts": outgoing_ids,
        "incoming_contradicts": incoming,
        "contradicting_evidence_ids": contradicting_evidence_ids,
        "challenge_ids": challenge_ids,
    }


def supersession_summary(target: Record, target_archived: bool, id_map: dict[str, Record]) -> dict[str, Any]:
    outgoing = {
        "supersedes": sorted(set(as_reference_list(target.data.get("supersedes")))),
        "superseded_by": as_reference_list(target.data.get("superseded_by")),
        "duplicate_of": as_reference_list(target.data.get("duplicate_of")),
        "corrects": sorted(set(as_reference_list(target.data.get("corrects")))),
        "restates": sorted(set(as_reference_list(target.data.get("restates")))),
        "narrows": sorted(set(as_reference_list(target.data.get("narrows")))),
        "broadens": sorted(set(as_reference_list(target.data.get("broadens")))),
        "withdrawn_by": as_reference_list(target.data.get("withdrawn_by")),
    }
    incoming = records_linking_to(target.id, id_map, LINK_FIELDS)
    incoming_superseding = [
        item for item in incoming if item["field"] in {"supersedes", "corrects", "narrows", "broadens"}
    ]
    return {
        "archived": target_archived,
        "archive_reason": target.data.get("archive_reason"),
        "outgoing": outgoing,
        "incoming_links": incoming,
        "incoming_superseding_records": incoming_superseding,
        "has_superseding_record": bool(
            outgoing["superseded_by"]
            or outgoing["duplicate_of"]
            or incoming_superseding
            or (target_archived and (outgoing["superseded_by"] or outgoing["duplicate_of"]))
        ),
        "withdrawn_by": outgoing["withdrawn_by"],
    }


def staleness_summary(
    target: Record,
    support_summary: dict[str, Any],
    validation_summary: dict[str, Any],
    challenge_summary: dict[str, Any],
) -> dict[str, Any]:
    all_flags = set(risk_flags_for(target.data))
    all_flags.update(support_summary["risk_flags"])
    all_flags.update(validation_summary["risk_flags"])
    all_flags.update(challenge_summary["risk_flags"])
    stale_risk_flags = sorted(flag for flag in all_flags if flag.lower() in STALE_RISK_FLAGS)
    return {
        "has_staleness_risk": bool(
            stale_risk_flags
            or validation_summary["stale_validation_ids"]
            or challenge_summary["stale_challenge_ids"]
        ),
        "stale_validation_ids": validation_summary["stale_validation_ids"],
        "stale_challenge_ids": challenge_summary["stale_challenge_ids"],
        "stale_risk_flags": stale_risk_flags,
        "time_window_policy": "explicit_signals_only",
    }


def scope_summary(
    target: Record,
    validation_summary: dict[str, Any],
    challenge_summary: dict[str, Any],
) -> dict[str, Any]:
    risk_flags = set(risk_flags_for(target.data))
    risk_flags.update(validation_summary["risk_flags"])
    risk_flags.update(challenge_summary["risk_flags"])
    scope_risk_flags = sorted(flag for flag in risk_flags if flag.lower() in SCOPE_RISK_FLAGS)
    return {
        "has_scope_limitation": bool(
            validation_summary["by_verdict"].get("partially_supports", 0)
            or challenge_summary["scope_challenge_ids"]
            or scope_risk_flags
        ),
        "partial_validation_ids": [
            path["id"] for path in validation_summary["paths"] if path["verdict"] in PARTIAL_VERDICTS
        ],
        "scope_challenge_ids": challenge_summary["scope_challenge_ids"],
        "scope_risk_flags": scope_risk_flags,
    }


def derive_review_state(
    target_kind: str,
    support_summary: dict[str, Any],
    validation_summary: dict[str, Any],
    challenge_summary: dict[str, Any],
    contradiction: dict[str, Any],
    supersession: dict[str, Any],
    staleness: dict[str, Any],
    scope: dict[str, Any],
) -> dict[str, Any]:
    flags: list[str] = []

    if challenge_summary["open_count"]:
        flags.append("has_open_challenge")
    if support_summary["low_trust_evidence_ids"]:
        flags.append("has_low_trust_support")
    if support_summary["private_evidence_ids"]:
        flags.append("has_private_support")
    source_independence = support_summary["source_independence"]
    if (
        target_kind != "evidence"
        and support_summary["evidence_ids"]
        and source_independence["company_originated_source_count"]
        and not source_independence["independent_source_count"]
    ):
        flags.append("company_originated_only_support")
    if contradiction["has_contradiction"]:
        flags.append("has_contradiction")
    if scope["has_scope_limitation"]:
        flags.append("has_scope_limitation")
    if staleness["has_staleness_risk"]:
        flags.append("has_staleness_risk")
    if supersession["has_superseding_record"]:
        flags.append("has_superseding_record")

    has_support = bool(support_summary["evidence_ids"])
    has_non_low_trust_support = bool(
        set(support_summary["evidence_ids"]) - set(support_summary["low_trust_evidence_ids"])
    )

    if supersession["withdrawn_by"] or validation_summary["withdrawal_validation_ids"]:
        primary_label = "withdrawn"
    elif supersession["has_superseding_record"]:
        primary_label = "superseded"
    elif staleness["has_staleness_risk"]:
        primary_label = "stale"
    elif (
        challenge_summary["open_count"]
        or validation_summary["contesting_validation_ids"]
        or contradiction["has_contradiction"]
    ):
        primary_label = "contested"
    elif has_support and not has_non_low_trust_support:
        primary_label = "low_trust_only"
    elif scope["has_scope_limitation"]:
        primary_label = "partially_supported"
    elif has_non_low_trust_support:
        primary_label = "supported"
    else:
        primary_label = "unreviewed"

    return {"primary_label": primary_label, "flags": sorted(set(flags))}


def build_review_analysis(
    target: Record,
    validations: list[dict[str, Any]],
    challenges: list[dict[str, Any]],
    id_map: dict[str, Record],
    target_archived: bool,
) -> dict[str, Any]:
    target_evidence_ids = evidence_ids_for_record(target, id_map)
    validation_summary = summarize_validations(validations, id_map)
    challenge_summary = summarize_challenges(challenges, id_map)
    support_ids = sorted(set(target_evidence_ids + validation_summary["support_evidence_ids"]))
    support_summary = evidence_summary(support_ids, id_map)
    target_evidence_summary = evidence_summary(target_evidence_ids, id_map)
    review_evidence_summary = evidence_summary(
        sorted(
            set(
                validation_summary["support_evidence_ids"]
                + challenge_summary["challenge_evidence_ids"]
            )
        ),
        id_map,
    )
    contradictions = contradiction_summary(target, challenge_summary, id_map)
    supersession = supersession_summary(target, target_archived, id_map)
    staleness = staleness_summary(target, support_summary, validation_summary, challenge_summary)
    scope = scope_summary(target, validation_summary, challenge_summary)
    review_state = derive_review_state(
        target.kind,
        support_summary,
        validation_summary,
        challenge_summary,
        contradictions,
        supersession,
        staleness,
        scope,
    )
    return {
        "review_state": review_state,
        "support_summary": support_summary,
        "target_evidence_summary": target_evidence_summary,
        "review_evidence_summary": review_evidence_summary,
        "validation_summary": validation_summary,
        "challenge_summary": challenge_summary,
        "contradiction_summary": contradictions,
        "supersession_summary": supersession,
        "staleness_summary": staleness,
        "scope_summary": scope,
    }


def json_error(error: str) -> dict[str, Any]:
    path = ""
    message = error
    if ": " in error:
        maybe_path, maybe_message = error.split(": ", 1)
        if "/" in maybe_path or maybe_path.endswith((".yml", ".yaml")):
            path = maybe_path
            message = maybe_message
    return {
        "code": "validation_error",
        "path": path,
        "json_pointer": None,
        "message": message,
        "hint": None,
        "record_id": None,
        "related_ids": [],
    }


def validate_repo(root: Path, current_only: bool = False) -> tuple[list[Record], list[str]]:
    validators = load_schemas(root)
    records, load_errors = load_records(root, include_archive=not current_only)
    id_map, id_errors = build_id_map(root, records)

    errors: list[str] = []
    errors.extend(load_errors)
    errors.extend(validate_schemas(root, records, validators))
    errors.extend(id_errors)
    errors.extend(validate_references(root, records, id_map))
    errors.extend(validate_claim_predicates(root, records))
    errors.extend(validate_relationships(root, records, id_map))
    errors.extend(validate_evidence_policy(root, records, id_map))
    errors.extend(validate_source_artifacts(root, records))
    errors.extend(validate_archive_policy(root, records, id_map))
    return records, errors


def relative_path(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def record_doc(root: Path, record: Record, include_data: bool = False) -> dict[str, Any]:
    doc = {
        "id": record.id,
        "kind": record.kind,
        "schema_version": record.data.get("schema_version"),
        "path": relative_path(root, record.path),
        "archived": is_archived_path(root, record.path),
        "label": record_label(record),
    }
    if include_data:
        doc["data"] = record.data
    return doc


def record_map(records: list[Record]) -> dict[str, Record]:
    return {record.id: record for record in records if record.id}


def is_record_yaml_path(path: str) -> bool:
    relative = Path(path)
    if relative.suffix not in {".yml", ".yaml"}:
        return False
    return bool(relative.parts) and relative.parts[0] in {*DATA_DIRS, "archive"}


def run_git(root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def git_lines(root: Path, args: list[str]) -> tuple[list[str], str | None]:
    result = run_git(root, args)
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "git command failed"
        return [], message
    return [line for line in result.stdout.splitlines() if line], None


def load_records_from_git(root: Path, base_ref: str) -> tuple[list[Record], list[str]]:
    paths, error = git_lines(root, ["ls-tree", "-r", "--name-only", base_ref])
    if error:
        return [], [f"failed to list `{base_ref}`: {error}"]

    records: list[Record] = []
    errors: list[str] = []
    for path_text in sorted(path for path in paths if is_record_yaml_path(path)):
        result = run_git(root, ["show", f"{base_ref}:{path_text}"])
        if result.returncode != 0:
            message = result.stderr.strip() or result.stdout.strip() or "git show failed"
            errors.append(f"{path_text}: failed to read `{base_ref}`: {message}")
            continue
        try:
            loaded = yaml.safe_load(result.stdout)
            if loaded is None:
                loaded = {}
            if not isinstance(loaded, dict):
                raise ValueError("YAML document must be an object")
            records.append(Record(path=root / path_text, data=loaded))
        except Exception as exc:
            errors.append(f"{path_text}: failed to load YAML from `{base_ref}`: {exc}")
    return records, errors


def changed_git_paths(root: Path, base_ref: str) -> tuple[list[dict[str, Any]], str | None]:
    rows, error = git_lines(root, ["diff", "--name-status", base_ref, "--"])
    if error:
        return [], error

    changes: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    for row in rows:
        parts = row.split("\t")
        if not parts:
            continue
        status = parts[0]
        if status.startswith("R") and len(parts) >= 3:
            old_path, new_path = parts[1], parts[2]
            if is_record_yaml_path(old_path) or is_record_yaml_path(new_path):
                changes.append({"status": "R", "old_path": old_path, "path": new_path})
                seen_paths.add(new_path)
            continue
        if len(parts) >= 2:
            path = parts[1]
            if is_record_yaml_path(path):
                changes.append({"status": status[:1], "path": path})
                seen_paths.add(path)

    untracked, untracked_error = git_lines(root, ["ls-files", "--others", "--exclude-standard"])
    if untracked_error:
        return changes, untracked_error
    for path in sorted(path for path in untracked if is_record_yaml_path(path)):
        if path not in seen_paths:
            changes.append({"status": "A", "path": path, "untracked": True})
    return sorted(changes, key=lambda item: (item.get("path", ""), item.get("old_path", ""))), None


def record_signature(record: Record) -> str:
    return json_dumps(record.data)


def delta_item(root: Path, record: Record, previous: Record | None = None) -> dict[str, Any]:
    item = record_doc(root, record)
    if previous is not None:
        previous_path = relative_path(root, previous.path)
        if previous_path != item["path"]:
            item["previous_path"] = previous_path
            item["path_changed"] = True
    return item


def summarize_record_delta(
    root: Path, base_records: list[Record], current_records: list[Record]
) -> dict[str, Any]:
    before = record_map(base_records)
    after = record_map(current_records)
    added: list[dict[str, Any]] = []
    modified: list[dict[str, Any]] = []
    deleted: list[dict[str, Any]] = []
    renamed: list[dict[str, Any]] = []

    for record_id in sorted(set(after) - set(before)):
        added.append(delta_item(root, after[record_id]))
    for record_id in sorted(set(before) - set(after)):
        deleted.append(delta_item(root, before[record_id]))
    for record_id in sorted(set(before) & set(after)):
        old = before[record_id]
        new = after[record_id]
        data_changed = record_signature(old) != record_signature(new)
        path_changed = relative_path(root, old.path) != relative_path(root, new.path)
        if data_changed:
            modified.append(delta_item(root, new, previous=old if path_changed else None))
        elif path_changed:
            renamed.append(delta_item(root, new, previous=old))

    counts = {
        "added": sorted_counts([item["kind"] for item in added]),
        "modified": sorted_counts([item["kind"] for item in modified]),
        "deleted": sorted_counts([item["kind"] for item in deleted]),
        "renamed": sorted_counts([item["kind"] for item in renamed]),
    }
    return {
        "counts": counts,
        "total": {
            "added": len(added),
            "modified": len(modified),
            "deleted": len(deleted),
            "renamed": len(renamed),
        },
        "added": added,
        "modified": modified,
        "deleted": deleted,
        "renamed": renamed,
    }


def refs_for_records(records: list[Record]) -> dict[str, set[str]]:
    refs: dict[str, set[str]] = {}
    for record in records:
        if record.id:
            refs[record.id] = {target for _, target, _ in record_ref_rows(record)}
    return refs


def records_referencing(records: list[Record], target_ids: set[str]) -> list[dict[str, Any]]:
    impacted: list[dict[str, Any]] = []
    for record in sorted(records, key=lambda item: item.id):
        if not record.id or record.id in target_ids:
            continue
        referenced = sorted(ref for _, ref, _ in record_ref_rows(record) if ref in target_ids)
        if referenced:
            impacted.append(
                {
                    "id": record.id,
                    "kind": record.kind,
                    "label": record_label(record),
                    "path": str(record.path),
                    "referenced_changed_ids": referenced,
                }
            )
    return impacted


def reference_impact(
    base_records: list[Record],
    current_records: list[Record],
    changed_ids: set[str],
    deleted_ids: set[str],
) -> dict[str, Any]:
    before_refs = refs_for_records(base_records)
    after_refs = refs_for_records(current_records)
    deleted_still_referenced = sorted(
        {
            target_id
            for refs in after_refs.values()
            for target_id in refs
            if target_id in deleted_ids
        }
    )
    return {
        "changed_ids": sorted(changed_ids),
        "before_incoming": records_referencing(base_records, changed_ids),
        "after_incoming": records_referencing(current_records, changed_ids),
        "deleted_ids_still_referenced": deleted_still_referenced,
    }


def graph_edge_key(edge: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(edge.get("from")),
        str(edge.get("to")),
        str(edge.get("type")),
        str(edge.get("field", "")),
    )


def graph_impact(root: Path, base_records: list[Record], current_records: list[Record]) -> dict[str, Any]:
    before_graph = build_graph_data(root, base_records)
    after_graph = build_graph_data(root, current_records)
    before_edges = {graph_edge_key(edge): edge for edge in before_graph["edges"]}
    after_edges = {graph_edge_key(edge): edge for edge in after_graph["edges"]}
    added_keys = sorted(set(after_edges) - set(before_edges))
    removed_keys = sorted(set(before_edges) - set(after_edges))
    return {
        "before_node_count": before_graph["node_count"],
        "after_node_count": after_graph["node_count"],
        "before_edge_count": before_graph["edge_count"],
        "after_edge_count": after_graph["edge_count"],
        "added_edge_count": len(added_keys),
        "removed_edge_count": len(removed_keys),
        "added_edges": [after_edges[key] for key in added_keys],
        "removed_edges": [before_edges[key] for key in removed_keys],
    }


def field_changes(before: dict[str, Any], after: dict[str, Any], fields: set[str]) -> list[str]:
    return sorted(field for field in fields if before.get(field) != after.get(field))


def warning_item(
    code: str,
    message: str,
    record_id: str | None = None,
    related_ids: list[str] | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "code": code,
        "message": message,
        "record_id": record_id,
        "related_ids": related_ids or [],
        "details": details or {},
    }


def evidence_integrity_warnings(
    base_records: list[Record], current_records: list[Record], delta: dict[str, Any]
) -> list[dict[str, Any]]:
    before = record_map(base_records)
    after = record_map(current_records)
    warnings: list[dict[str, Any]] = []

    for item in delta["deleted"]:
        if item["kind"] == "evidence":
            warnings.append(
                warning_item(
                    "deletes_canonical_evidence",
                    "Canonical evidence record was deleted.",
                    item["id"],
                )
            )

    for item in delta["modified"]:
        record_id = item["id"]
        old = before.get(record_id)
        new = after.get(record_id)
        if not old or not new or new.kind != "evidence":
            continue
        changed_fields = field_changes(old.data, new.data, EVIDENCE_INTEGRITY_FIELDS)
        if changed_fields:
            warnings.append(
                warning_item(
                    "modifies_canonical_evidence",
                    "Canonical evidence fields changed.",
                    record_id,
                    details={"fields": changed_fields},
                )
            )
    return warnings


def ontology_impact(delta: dict[str, Any]) -> dict[str, Any]:
    items = [
        item
        for section in ("added", "modified", "deleted", "renamed")
        for item in delta[section]
        if item["kind"] in ONTOLOGY_KINDS
    ]
    return {
        "changed": items,
        "changed_count": len(items),
        "by_kind": sorted_counts([item["kind"] for item in items]),
    }


def review_record_dict(root: Path, record: Record) -> dict[str, Any]:
    return record_doc(root, record, include_data=True)


def review_records_for_target(
    records: list[Record], target_id: str, kind: str, root: Path
) -> list[dict[str, Any]]:
    return [
        review_record_dict(root, record)
        for record in sorted(records, key=lambda item: item.id)
        if record.kind == kind and record.data.get("target") == target_id
    ]


def review_snapshot_for_records(
    root: Path, records: list[Record], record_id: str
) -> dict[str, Any] | None:
    id_map = record_map(records)
    target = id_map.get(record_id)
    if not target or target.kind not in REVIEWABLE_KINDS:
        return None
    analysis = build_review_analysis(
        target,
        review_records_for_target(records, record_id, "validation", root),
        review_records_for_target(records, record_id, "challenge", root),
        id_map,
        target_archived=is_archived_path(root, target.path),
    )
    return {
        "id": target.id,
        "kind": target.kind,
        "path": relative_path(root, target.path),
        "review_state": analysis["review_state"],
        "support_evidence_count": analysis["support_summary"]["evidence_count"],
        "support_source_count": analysis["support_summary"]["source_independence"][
            "unique_source_count"
        ],
        "open_challenge_count": analysis["challenge_summary"]["open_count"],
        "repeated_validation_path_count": analysis["validation_summary"][
            "repeated_dependency_path_count"
        ],
        "low_trust_evidence_ids": analysis["support_summary"]["low_trust_evidence_ids"],
        "private_evidence_ids": analysis["support_summary"]["private_evidence_ids"],
    }


def review_snapshot_key(snapshot: dict[str, Any] | None) -> dict[str, Any] | None:
    if snapshot is None:
        return None
    return {
        "review_state": snapshot["review_state"],
        "support_evidence_count": snapshot["support_evidence_count"],
        "support_source_count": snapshot["support_source_count"],
        "open_challenge_count": snapshot["open_challenge_count"],
        "repeated_validation_path_count": snapshot["repeated_validation_path_count"],
        "low_trust_evidence_ids": snapshot["low_trust_evidence_ids"],
        "private_evidence_ids": snapshot["private_evidence_ids"],
    }


def review_impact_ids(
    base_records: list[Record],
    current_records: list[Record],
    delta: dict[str, Any],
    reference_summary: dict[str, Any],
) -> set[str]:
    ids = set(reference_summary["changed_ids"])
    before = record_map(base_records)
    after = record_map(current_records)

    for item in [*delta["added"], *delta["modified"], *delta["deleted"], *delta["renamed"]]:
        record = after.get(item["id"]) or before.get(item["id"])
        if record and record.kind in {"validation", "challenge"}:
            target = record.data.get("target")
            if isinstance(target, str):
                ids.add(target)

    for section in ("before_incoming", "after_incoming"):
        for item in reference_summary[section]:
            ids.add(item["id"])
    return ids


def review_state_impact(
    root: Path,
    base_records: list[Record],
    current_records: list[Record],
    delta: dict[str, Any],
    reference_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    impacts: list[dict[str, Any]] = []
    for record_id in sorted(review_impact_ids(base_records, current_records, delta, reference_summary)):
        before = review_snapshot_for_records(root, base_records, record_id)
        after = review_snapshot_for_records(root, current_records, record_id)
        if review_snapshot_key(before) == review_snapshot_key(after):
            continue
        if before is None and after is None:
            continue
        impacts.append({"id": record_id, "before": before, "after": after})
    return impacts


def changed_record_ids(delta: dict[str, Any]) -> set[str]:
    return {
        item["id"]
        for section in ("added", "modified", "deleted", "renamed")
        for item in delta[section]
    }


def diff_review_warnings(
    root: Path,
    base_records: list[Record],
    current_records: list[Record],
    delta: dict[str, Any],
    review_impacts: list[dict[str, Any]],
    ontology: dict[str, Any],
) -> list[dict[str, Any]]:
    before = record_map(base_records)
    after = record_map(current_records)
    warnings = evidence_integrity_warnings(base_records, current_records, delta)

    for item in [*delta["added"], *delta["modified"], *delta["renamed"]]:
        record = after.get(item["id"])
        if record and is_archived_path(root, record.path):
            previous_path = item.get("previous_path")
            was_archived = (
                bool(previous_path)
                and Path(str(previous_path)).parts
                and Path(str(previous_path)).parts[0] == "archive"
            )
            code = "adds_archived_record" if not previous_path else "moves_record_to_archive"
            if previous_path and was_archived:
                code = "updates_archived_record"
            warnings.append(
                warning_item(
                    code,
                    "Record is under archive/ and excluded from current read views by default.",
                    record.id,
                    details={
                        "path": relative_path(root, record.path),
                        "previous_path": previous_path,
                    },
                )
            )

    for item in [*delta["added"], *delta["modified"]]:
        record = after.get(item["id"])
        if not record:
            continue
        data = record.data

        if record.kind == "evidence":
            evidence_class = data.get("evidence_class")
            if evidence_class in LOW_TRUST_EVIDENCE_CLASSES:
                warnings.append(
                    warning_item(
                        "adds_or_updates_low_trust_evidence",
                        f"Evidence uses low-trust class `{evidence_class}`.",
                        record.id,
                    )
                )
            if evidence_class in PRIVATE_EVIDENCE_CLASSES:
                warnings.append(
                    warning_item(
                        "adds_or_updates_private_evidence",
                        f"Evidence uses private/internal class `{evidence_class}`.",
                        record.id,
                    )
                )

        if record.kind == "challenge" and is_open_challenge(review_record_dict(root, record)):
            warnings.append(
                warning_item(
                    "adds_or_updates_open_challenge",
                    "Record adds or updates an open challenge.",
                    record.id,
                    related_ids=[str(data.get("target"))] if data.get("target") else [],
                )
            )
            if data.get("challenge_type") == "contradiction":
                warnings.append(
                    warning_item(
                        "adds_or_updates_contradiction_challenge",
                        "Record adds or updates a contradiction challenge.",
                        record.id,
                        related_ids=[str(data.get("target"))] if data.get("target") else [],
                    )
                )

        if record.kind in REVIEWABLE_KINDS and (
            as_reference_list(data.get("contradicts"))
            or as_reference_list(data.get("contradicting_evidence"))
        ):
            warnings.append(
                warning_item(
                    "adds_or_updates_contradiction_link",
                    "Record declares contradiction linkage.",
                    record.id,
                    related_ids=as_reference_list(data.get("contradicts"))
                    + as_reference_list(data.get("contradicting_evidence")),
                )
            )

        if record.kind == "claim" and str(data.get("predicate", "")).startswith("provisional:"):
            warnings.append(
                warning_item(
                    "uses_provisional_claim_predicate",
                    "Claim uses a provisional predicate.",
                    record.id,
                )
            )
        if record.kind == "relationship" and str(data.get("type", "")).startswith("provisional:"):
            warnings.append(
                warning_item(
                    "uses_provisional_relationship_type",
                    "Relationship uses a provisional type.",
                    record.id,
                )
            )

    for item in delta["deleted"]:
        if item["kind"] == "evidence":
            continue
        record = before.get(item["id"])
        if record and record.kind in REVIEWABLE_KINDS:
            warnings.append(
                warning_item(
                    "deletes_reviewable_record",
                    "Reviewable record was deleted.",
                    record.id,
                )
            )

    for item in ontology["changed"]:
        warnings.append(
            warning_item(
                "changes_ontology",
                "Ontology registry record changed.",
                item["id"],
                details={"kind": item["kind"], "path": item["path"]},
            )
        )

    for impact in review_impacts:
        before_state = impact["before"]["review_state"] if impact["before"] else None
        after_state = impact["after"]["review_state"] if impact["after"] else None
        if before_state != after_state:
            warnings.append(
                warning_item(
                    "review_state_changed",
                    "Derived review state changed.",
                    impact["id"],
                    details={"before": before_state, "after": after_state},
                )
            )
        if impact["after"] and impact["after"]["review_state"]["primary_label"] == "low_trust_only":
            warnings.append(
                warning_item(
                    "low_trust_only_review_state",
                    "Record derives to low_trust_only.",
                    impact["id"],
                )
            )
        if impact["after"] and impact["after"]["repeated_validation_path_count"]:
            warnings.append(
                warning_item(
                    "repeated_validation_path",
                    "Record has repeated validation dependency paths.",
                    impact["id"],
                    details={
                        "repeated_validation_path_count": impact["after"][
                            "repeated_validation_path_count"
                        ]
                    },
                )
            )

    unique: dict[tuple[str, str | None, str], dict[str, Any]] = {}
    for item in warnings:
        key = (item["code"], item["record_id"], json_dumps(item["details"]))
        unique[key] = item
    return [unique[key] for key in sorted(unique)]


def build_diff_review(root: Path, base_ref: str) -> tuple[dict[str, Any], int]:
    base_records, base_errors = load_records_from_git(root, base_ref)
    path_changes, path_error = changed_git_paths(root, base_ref)
    if path_error:
        base_errors.append(f"failed to diff `{base_ref}`: {path_error}")

    current_records, validation_errors = validate_repo(root, current_only=False)
    if base_errors:
        errors = [
            command_error("git_range_error", error, "Check that the base ref exists.")
            for error in base_errors
        ]
        return (
            result_envelope(
                "diff-review",
                root,
                ok=False,
                errors=errors,
                base=base_ref,
                changed_paths=path_changes,
            ),
            2,
        )

    delta = summarize_record_delta(root, base_records, current_records)
    changed_ids = changed_record_ids(delta)
    deleted_ids = {item["id"] for item in delta["deleted"]}
    refs = reference_impact(base_records, current_records, changed_ids, deleted_ids)
    reviews = review_state_impact(root, base_records, current_records, delta, refs)
    ontology = ontology_impact(delta)
    graph = graph_impact(root, base_records, current_records)
    warnings = diff_review_warnings(root, base_records, current_records, delta, reviews, ontology)
    errors = [json_error(error) for error in validation_errors]
    status = 1 if errors else 0

    return (
        result_envelope(
            "diff-review",
            root,
            ok=not errors,
            warnings=warnings,
            errors=errors,
            base=base_ref,
            changed_paths=path_changes,
            record_delta=delta,
            reference_impact=refs,
            review_state_impact=reviews,
            graph_impact=graph,
            ontology_impact=ontology,
        ),
        status,
    )


def run_diff_review(root: Path, base_ref: str = "HEAD", json_output: bool = False) -> int:
    payload, status = build_diff_review(root, base_ref)
    if json_output:
        print_json(payload)
        return status

    delta = payload.get("record_delta", {})
    total = delta.get("total", {})
    print(f"Diff review vs {base_ref}")
    print(
        "records: "
        f"+{total.get('added', 0)} "
        f"~{total.get('modified', 0)} "
        f"-{total.get('deleted', 0)} "
        f"renamed {total.get('renamed', 0)}"
    )
    if payload["errors"]:
        print(f"errors: {len(payload['errors'])}")
        for error in payload["errors"]:
            print(f"  {error['message']}")
    if payload["warnings"]:
        print(f"warnings: {len(payload['warnings'])}")
        for warning in payload["warnings"]:
            suffix = f" ({warning['record_id']})" if warning.get("record_id") else ""
            print(f"  {warning['code']}{suffix}: {warning['message']}")
    reviews = payload.get("review_state_impact", [])
    if reviews:
        print(f"review impacts: {len(reviews)}")
        for item in reviews:
            before = item["before"]["review_state"]["primary_label"] if item["before"] else "missing"
            after = item["after"]["review_state"]["primary_label"] if item["after"] else "missing"
            print(f"  {item['id']}: {before} -> {after}")
    return status


def slugify(value: str, max_length: int = 96) -> str:
    lowered = value.lower()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    lowered = re.sub(r"-+", "-", lowered).strip("-")
    return (lowered or "record")[:max_length].strip("-") or "record"


def id_slug(record_id: str) -> str:
    return slugify(record_id.split(":", 1)[1] if ":" in record_id else record_id)


def ensure_id(prefix: str, explicit_id: str | None, seed: str) -> str:
    if explicit_id:
        if not explicit_id.startswith(f"{prefix}:"):
            raise ValueError(f"id `{explicit_id}` must start with `{prefix}:`")
        return explicit_id
    return f"{prefix}:{slugify(seed)}"


def generated_record_path(root: Path, dirname: str, record_id: str, explicit_path: str | None) -> Path:
    if explicit_path:
        path = Path(explicit_path)
        return path if path.is_absolute() else root / path
    return root / dirname / "generated" / f"{id_slug(record_id)}.yml"


def parse_key_values(values: list[str] | None) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for item in values or []:
        if "=" not in item:
            raise ValueError(f"`{item}` must use key=value")
        key, value = item.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"`{item}` has an empty key")
        parsed[key] = value.strip()
    return parsed


def parse_participants(values: list[str] | None) -> list[dict[str, str]]:
    participants: list[dict[str, str]] = []
    for item in values or []:
        if "=" not in item:
            raise ValueError(f"`{item}` must use role=entity:id")
        role, entity_id = item.split("=", 1)
        participants.append({"role": role.strip(), "entity": entity_id.strip()})
    return participants


def parse_json_object(value: str | None, field_name: str) -> dict[str, Any] | None:
    if not value:
        return None
    try:
        loaded = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{field_name} must be a JSON object: {exc.msg}") from exc
    if not isinstance(loaded, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return loaded


def build_depends_on(args: argparse.Namespace) -> dict[str, list[str]]:
    return {
        "evidence": sorted(args.evidence or []),
        "claims": sorted(args.claim or []),
        "relationships": sorted(args.relationship or []),
        "theses": sorted(args.thesis or []),
        "metrics": sorted(args.metric or []),
        "events": sorted(args.event or []),
        "datasets": sorted(getattr(args, "dataset", []) or []),
    }


def add_optional_common_fields(data: dict[str, Any], args: argparse.Namespace) -> None:
    if getattr(args, "created_at", None):
        data["created_at"] = args.created_at
    risk_flags = sorted(set(getattr(args, "risk_flag", None) or []))
    if risk_flags:
        data["risk_flags"] = risk_flags


def validate_new_record(root: Path, path: Path, data: dict[str, Any]) -> list[str]:
    records, load_errors = load_records(root)
    try:
        relative = path.relative_to(root)
    except ValueError:
        relative = path
    new_record = Record(path=path, data=data)
    validators = load_schemas(root)

    errors = list(load_errors)
    for existing in records:
        if existing.id == new_record.id:
            errors.append(
                f"{relative}: duplicate id `{new_record.id}` already used by "
                f"{existing.path.relative_to(root)}"
            )
    kind = data.get("kind")
    if kind not in validators:
        errors.append(f"{relative}: unknown or missing kind `{kind}`")
    else:
        for error in sorted(validators[kind].iter_errors(data), key=lambda item: item.path):
            errors.append(f"{relative}: {format_error_path(error)}: {error.message}")

    combined = records + [new_record]
    id_map, id_errors = build_id_map(root, combined)
    errors.extend(id_errors)
    errors.extend(validate_references(root, [new_record], id_map))
    errors.extend(validate_claim_predicates(root, combined))
    errors.extend(validate_relationships(root, combined, id_map))
    errors.extend(validate_evidence_policy(root, [new_record], id_map))
    errors.extend(validate_source_artifacts(root, combined))
    errors.extend(validate_archive_policy(root, combined, id_map))
    return errors


def write_record_file(path: Path, data: dict[str, Any], overwrite: bool = False) -> None:
    if path.exists() and not overwrite:
        raise FileExistsError(f"{path} already exists; pass --overwrite to replace it")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, sort_keys=False, allow_unicode=False)


def run_new_record(
    root: Path,
    command: str,
    path: Path,
    data: dict[str, Any],
    json_output: bool = False,
    overwrite: bool = False,
) -> int:
    try:
        relative_path = path.relative_to(root)
    except ValueError:
        error = command_error("path_outside_repo", f"{path} is outside the repository")
        if json_output:
            print_json(result_envelope(command, root, ok=False, errors=[error], record=data))
        else:
            print(f"ERROR {error['message']}", file=sys.stderr)
        return 1

    if path.exists() and not overwrite:
        error = command_error("file_exists", f"{relative_path} already exists")
        if json_output:
            print_json(result_envelope(command, root, ok=False, errors=[error], record=data))
        else:
            print(f"ERROR {error['message']}", file=sys.stderr)
        return 1

    errors = validate_new_record(root, path, data)
    if errors:
        if json_output:
            print_json(
                result_envelope(
                    command,
                    root,
                    ok=False,
                    errors=[json_error(error) for error in errors],
                    record=data,
                )
            )
        else:
            for error in errors:
                print(f"ERROR {error}", file=sys.stderr)
        return 1

    try:
        write_record_file(path, data, overwrite=overwrite)
    except OSError as exc:
        error = command_error("write_failed", str(exc))
        if json_output:
            print_json(result_envelope(command, root, ok=False, errors=[error], record=data))
        else:
            print(f"ERROR {error['message']}", file=sys.stderr)
        return 1

    result = {
        "created": True,
        "path": str(relative_path),
        "id": data["id"],
        "record": data,
        "next_commands": ["uv run fo lint --json"],
    }
    if json_output:
        print_json(result_envelope(command, root, **result))
    else:
        print(f"Created {result['path']}")
        print("Run: uv run fo lint --json")
    return 0


def run_new_source(root: Path, args: argparse.Namespace) -> int:
    record_id = ensure_id(
        "source",
        args.id,
        f"{args.public_status} {args.source_type} {args.title}",
    )
    data: dict[str, Any] = {
        "schema_version": 1,
        "kind": "source",
        "id": record_id,
        "source_type": args.source_type,
        "title": args.title,
        "public_status": args.public_status,
        "source_perspective": getattr(args, "source_perspective", "unknown"),
        "accessed_at": args.accessed_at,
        "content_mode": args.content_mode,
        "submitted_by": args.submitted_by,
    }
    for field in ("publisher", "url", "archive_url", "published_at", "provenance"):
        value = getattr(args, field)
        if value:
            data[field] = value
    source_artifacts = sorted(set(getattr(args, "source_artifact", []) or []))
    if source_artifacts:
        data["source_artifacts"] = source_artifacts
    add_optional_common_fields(data, args)
    path = generated_record_path(root, "sources", record_id, args.path)
    return run_new_record(root, "new source", path, data, args.json, args.overwrite)


def run_new_evidence(root: Path, args: argparse.Namespace) -> int:
    record_id = ensure_id("evidence", args.id, f"{args.source} {args.summary}")
    data: dict[str, Any] = {
        "schema_version": 1,
        "kind": "evidence",
        "id": record_id,
        "evidence_class": args.evidence_class,
        "source": args.source,
        "summary": args.summary,
        "content_mode": args.content_mode,
        "observed_at": args.observed_at,
        "submitted_by": args.submitted_by,
        "source_attribution": args.source_attribution,
    }
    if args.excerpt:
        data["excerpt"] = args.excerpt
    locator = parse_key_values(args.locator)
    if locator:
        data["locator"] = locator
    source_access = parse_json_object(args.source_access_json, "--source-access-json")
    if source_access is not None:
        data["source_access"] = source_access
    if args.verification_status:
        data["verification_status"] = args.verification_status
    source_artifacts = sorted(set(getattr(args, "source_artifact", []) or []))
    if source_artifacts:
        data["source_artifacts"] = source_artifacts
    add_optional_common_fields(data, args)
    path = generated_record_path(root, "evidence", record_id, args.path)
    return run_new_record(root, "new evidence", path, data, args.json, args.overwrite)


def run_new_claim(root: Path, args: argparse.Namespace) -> int:
    record_id = ensure_id("claim", args.id, args.statement)
    data: dict[str, Any] = {
        "schema_version": 1,
        "kind": "claim",
        "id": record_id,
        "statement": args.statement,
        "subject": args.subject,
        "predicate": args.predicate,
        "support_type": args.support_type,
        "evidence": [{"id": evidence_id} for evidence_id in sorted(args.evidence)],
        "submitted_by": args.submitted_by,
    }
    if args.object is not None:
        data["object"] = args.object
    qualifiers = parse_key_values(args.qualifier)
    if qualifiers:
        data["qualifiers"] = qualifiers
    if args.time_start or args.time_end:
        data["time_scope"] = {"start": args.time_start, "end": args.time_end}
    if args.methodology:
        data["methodology"] = args.methodology
    if args.proposed_predicate_definition:
        data["proposed_predicate_definition"] = args.proposed_predicate_definition
    add_optional_common_fields(data, args)
    path = generated_record_path(root, "claims", record_id, args.path)
    return run_new_record(root, "new claim", path, data, args.json, args.overwrite)


def run_new_validation(root: Path, args: argparse.Namespace) -> int:
    seed = f"{args.target} {args.verdict} {args.submitted_by}"
    record_id = ensure_id("validation", args.id, seed)
    data: dict[str, Any] = {
        "schema_version": 1,
        "kind": "validation",
        "id": record_id,
        "target": args.target,
        "submitted_by": args.submitted_by,
        "verdict": args.verdict,
        "summary": args.summary,
        "depends_on": build_depends_on(args),
    }
    add_optional_common_fields(data, args)
    path = generated_record_path(root, "validations", record_id, args.path)
    return run_new_record(root, "new validation", path, data, args.json, args.overwrite)


def run_new_challenge(root: Path, args: argparse.Namespace) -> int:
    seed = f"{args.target} {args.challenge_type} {args.submitted_by}"
    record_id = ensure_id("challenge", args.id, seed)
    data: dict[str, Any] = {
        "schema_version": 1,
        "kind": "challenge",
        "id": record_id,
        "target": args.target,
        "submitted_by": args.submitted_by,
        "challenge_type": args.challenge_type,
        "summary": args.summary,
    }
    depends_on = build_depends_on(args)
    if any(depends_on.values()):
        data["depends_on"] = depends_on
    for field in ("addressed_by", "withdrawn_by", "superseded_by"):
        value = getattr(args, field)
        if value:
            data[field] = value
    add_optional_common_fields(data, args)
    path = generated_record_path(root, "challenges", record_id, args.path)
    return run_new_record(root, "new challenge", path, data, args.json, args.overwrite)


def run_new_relationship(root: Path, args: argparse.Namespace) -> int:
    participants = parse_participants(args.participant)
    participant_seed = " ".join(item["entity"] for item in participants)
    record_id = ensure_id("relationship", args.id, f"{args.type} {participant_seed}")
    data: dict[str, Any] = {
        "schema_version": 1,
        "kind": "relationship",
        "id": record_id,
        "type": args.type,
        "participants": participants,
        "derived_from": {
            "claims": sorted(args.derived_claim or []),
            "evidence": sorted(args.derived_evidence or []),
        },
        "submitted_by": args.submitted_by,
    }
    scope = parse_key_values(args.scope)
    if scope:
        data["scope"] = scope
    if args.qualifier:
        data["qualifiers"] = sorted(set(args.qualifier))
    if args.time_start or args.time_end:
        data["time_scope"] = {"start": args.time_start, "end": args.time_end}
    if args.materiality_level or args.materiality_basis:
        data["materiality"] = {
            "level": args.materiality_level,
            "basis": args.materiality_basis or "unknown",
        }
    if args.proposed_type_definition:
        data["proposed_type_definition"] = args.proposed_type_definition
    add_optional_common_fields(data, args)
    path = generated_record_path(root, "relationships", record_id, args.path)
    return run_new_record(root, "new relationship", path, data, args.json, args.overwrite)


def run_new_entity(root: Path, args: argparse.Namespace) -> int:
    record_id = args.id or f"entity:{args.entity_type}:{slugify(args.name)}"
    if not record_id.startswith("entity:"):
        raise ValueError(f"id `{record_id}` must start with `entity:`")
    data: dict[str, Any] = {
        "schema_version": 1,
        "kind": "entity",
        "id": record_id,
        "entity_type": args.entity_type,
        "name": args.name,
        "submitted_by": args.submitted_by,
    }
    if args.alias:
        data["aliases"] = sorted(set(args.alias))
    identifiers = parse_key_values(args.identifier)
    if identifiers:
        data["identifiers"] = identifiers
    if args.description:
        data["description"] = args.description
    if args.state:
        data["state"] = args.state
    add_optional_common_fields(data, args)
    path = generated_record_path(root, f"entities/{args.entity_type}", record_id, args.path)
    return run_new_record(root, "new entity", path, data, args.json, args.overwrite)


def run_new_metric(root: Path, args: argparse.Namespace) -> int:
    period = parse_key_values(args.period)
    record_id = ensure_id(
        "metric",
        args.id,
        f"{args.entity} {args.metric_definition} {' '.join(f'{k}-{v}' for k, v in sorted(period.items()))}",
    )
    data: dict[str, Any] = {
        "schema_version": 1,
        "kind": "metric",
        "id": record_id,
        "entity": args.entity,
        "metric_definition": args.metric_definition,
        "value": args.value,
        "unit": args.unit,
        "period": period,
        "value_basis": args.value_basis,
        "evidence": sorted(args.evidence),
        "submitted_by": args.submitted_by,
    }
    source_locator = parse_key_values(args.source_locator)
    if source_locator:
        data["source_locator"] = source_locator
    dimensions = parse_key_values(args.dimension)
    if dimensions:
        data["dimensions"] = dimensions
    for field in (
        "as_of",
        "reported_at",
        "published_at",
        "restated_from",
        "methodology",
        "limitations",
    ):
        value = getattr(args, field)
        if value:
            data[field] = value
    add_optional_common_fields(data, args)
    path = generated_record_path(root, "metrics", record_id, args.path)
    return run_new_record(root, "new metric", path, data, args.json, args.overwrite)


def run_new_event(root: Path, args: argparse.Namespace) -> int:
    record_id = ensure_id("event", args.id, f"{args.event_type} {args.title}")
    data: dict[str, Any] = {
        "schema_version": 1,
        "kind": "event",
        "id": record_id,
        "event_type": args.event_type,
        "event_state": args.event_state,
        "title": args.title,
        "entities": sorted(args.entity),
        "evidence": sorted(args.evidence),
        "submitted_by": args.submitted_by,
    }
    for field in ("occurred_at", "expected_at", "effective_at"):
        value = getattr(args, field)
        if value:
            data[field] = value
    period = parse_key_values(args.period)
    if period:
        data["period"] = period
    properties = parse_key_values(args.property)
    if properties:
        data["properties"] = properties
    add_optional_common_fields(data, args)
    path = generated_record_path(root, "events", record_id, args.path)
    return run_new_record(root, "new event", path, data, args.json, args.overwrite)


def run_new_dataset(root: Path, args: argparse.Namespace) -> int:
    record_id = ensure_id("dataset", args.id, f"{args.publisher} {args.title}")
    data: dict[str, Any] = {
        "schema_version": 1,
        "kind": "dataset",
        "id": record_id,
        "title": args.title,
        "dataset_type": args.dataset_type,
        "publisher": args.publisher,
        "coverage": parse_key_values(args.coverage),
        "access": parse_key_values(args.access),
        "sources": sorted(args.source),
        "content_mode": args.content_mode,
        "submitted_by": args.submitted_by,
    }
    for field in ("content_hash", "license", "limitations"):
        value = getattr(args, field)
        if value:
            data[field] = value
    add_optional_common_fields(data, args)
    path = generated_record_path(root, "datasets", record_id, args.path)
    return run_new_record(root, "new dataset", path, data, args.json, args.overwrite)


def run_new_thesis(root: Path, args: argparse.Namespace) -> int:
    depends_on = build_depends_on(args)
    if not any(depends_on.values()):
        error = command_error("missing_dependency", "thesis needs at least one explicit dependency")
        if args.json:
            print_json(result_envelope("new thesis", root, ok=False, errors=[error]))
        else:
            print(f"ERROR {error['message']}", file=sys.stderr)
        return 1

    record_id = ensure_id("thesis", args.id, args.title)
    data: dict[str, Any] = {
        "schema_version": 1,
        "kind": "thesis",
        "id": record_id,
        "title": args.title,
        "summary": args.summary,
        "depends_on": depends_on,
        "submitted_by": args.submitted_by,
    }
    if args.stance:
        data["stance"] = args.stance
    if args.time_horizon:
        data["time_horizon"] = args.time_horizon
    forecast = parse_json_object(args.forecast_json, "--forecast-json")
    if forecast is not None:
        data["forecast"] = forecast
    if args.contradicting_evidence:
        data["contradicting_evidence"] = sorted(set(args.contradicting_evidence))
    add_optional_common_fields(data, args)
    path = generated_record_path(root, "theses", record_id, args.path)
    return run_new_record(root, "new thesis", path, data, args.json, args.overwrite)


def run_new_question(root: Path, args: argparse.Namespace) -> int:
    record_id = ensure_id("question", args.id, args.question)
    data: dict[str, Any] = {
        "schema_version": 1,
        "kind": "question",
        "id": record_id,
        "question": args.question,
        "entities": sorted(set(args.entity)),
        "proof_type": args.proof_type,
        "priority": args.priority,
        "submitted_by": args.submitted_by,
    }
    for source_field, data_field in (
        ("related_evidence", "related_evidence"),
        ("related_claim", "related_claims"),
        ("related_relationship", "related_relationships"),
        ("related_thesis", "related_theses"),
        ("next_action", "next_actions"),
        ("resolved_by", "resolved_by"),
    ):
        values = sorted(set(getattr(args, source_field)))
        if values:
            data[data_field] = values
    add_optional_common_fields(data, args)
    path = generated_record_path(root, "questions", record_id, args.path)
    return run_new_record(root, "new question", path, data, args.json, args.overwrite)


def run_lint(root: Path, json_output: bool = False, current_only: bool = False) -> int:
    records, errors = validate_repo(root, current_only=current_only)
    warnings = [
        *preservation_policy_warnings(root, records),
        *duplicate_detection_warnings(root, records),
    ]
    if json_output:
        print(
            json.dumps(
                {
                    "ok": not errors,
                    "command": "lint",
                    "repo_root": str(root),
                    "records_checked": len(records),
                    "warnings": warnings,
                    "errors": [json_error(error) for error in errors],
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 1 if errors else 0

    if errors:
        for error in errors:
            print(f"ERROR {error}", file=sys.stderr)
        print(f"\n{len(errors)} validation error(s)", file=sys.stderr)
        return 1

    print(f"OK {len(records)} records validated")
    for warning in warnings:
        print(f"WARNING {warning['path']}: {warning['message']}", file=sys.stderr)
    return 0


def cmd_lint(args: argparse.Namespace) -> int:
    return run_lint(repo_root(), json_output=bool(args.json), current_only=bool(args.current_only))


def run_index_build(root: Path, json_output: bool = False) -> int:
    records, errors = validate_repo(root, current_only=False)
    if errors:
        if json_output:
            print_json(
                result_envelope(
                    "index build",
                    root,
                    ok=False,
                    errors=[json_error(error) for error in errors],
                    records_indexed=0,
                )
            )
        else:
            for error in errors:
                print(f"ERROR {error}", file=sys.stderr)
            print(f"\n{len(errors)} validation error(s)", file=sys.stderr)
        return 1

    result = create_index_database(root, records)
    if json_output:
        print_json(result_envelope("index build", root, **result))
    else:
        print(
            f"Wrote {Path(result['index_path']).relative_to(root)} "
            f"({result['records_indexed']} records)"
        )
    return 0


def cmd_index_build(args: argparse.Namespace) -> int:
    return run_index_build(repo_root(), json_output=bool(args.json))


def run_search(
    root: Path,
    query: str,
    json_output: bool = False,
    include_archive: bool = False,
    limit: int = 20,
) -> int:
    try:
        with connect_index(root) as conn:
            rows = search_rows(conn, query, include_archive=include_archive, limit=limit)
            results = [row_to_record(row) for row in rows]
    except FileNotFoundError as exc:
        error = command_error("index_missing", str(exc), "Run `fo index build` first.")
        if json_output:
            print_json(result_envelope("search", root, ok=False, errors=[error], query=query, results=[]))
        else:
            print(f"ERROR {error['message']}", file=sys.stderr)
        return 1

    if json_output:
        print_json(
            result_envelope(
                "search",
                root,
                query=query,
                result_count=len(results),
                results=results,
            )
        )
    else:
        for result in results:
            print(f"{result['id']} [{result['kind']}] {result['path']}")
            print(f"  {result['label']}")
        print(f"{len(results)} match(es)")
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    return run_search(
        repo_root(),
        args.query,
        json_output=bool(args.json),
        include_archive=bool(args.include_archive),
        limit=int(args.limit),
    )


def run_context(
    root: Path,
    record_id: str,
    json_output: bool = False,
    include_archive: bool = False,
) -> int:
    try:
        with connect_index(root) as conn:
            record = indexed_record(conn, record_id)
            if record is None or (record["archived"] and not include_archive):
                raise KeyError(record_id)
            outgoing = outgoing_refs(conn, record_id)
            incoming = incoming_refs(conn, record_id)
            edges = graph_edge_rows(conn, record_id)
            neighbor_ids = related_record_ids(conn, record_id)
            neighbors = fetch_records(conn, neighbor_ids)
            validations = target_review_records(conn, "validations", record_id)
            challenges = target_review_records(conn, "challenges", record_id)
    except FileNotFoundError as exc:
        error = command_error("index_missing", str(exc), "Run `fo index build` first.")
        if json_output:
            print_json(result_envelope("context", root, ok=False, errors=[error], id=record_id))
        else:
            print(f"ERROR {error['message']}", file=sys.stderr)
        return 1
    except KeyError:
        error = command_error("record_not_found", f"record `{record_id}` was not found")
        if json_output:
            print_json(result_envelope("context", root, ok=False, errors=[error], id=record_id))
        else:
            print(f"ERROR {error['message']}", file=sys.stderr)
        return 1

    if json_output:
        print_json(
            result_envelope(
                "context",
                root,
                id=record_id,
                record=record,
                outgoing_refs=outgoing,
                incoming_refs=incoming,
                graph_edges=edges,
                neighbors=neighbors,
                validations=validations,
                challenges=challenges,
            )
        )
    else:
        print(f"{record['id']} [{record['kind']}] {record['path']}")
        print(f"  {record['label']}")
        print(f"{len(neighbors)} neighbor(s), {len(validations)} validation(s), {len(challenges)} challenge(s)")
    return 0


def cmd_context(args: argparse.Namespace) -> int:
    return run_context(
        repo_root(),
        args.id,
        json_output=bool(args.json),
        include_archive=bool(args.include_archive),
    )


def run_review(
    root: Path,
    record_id: str,
    json_output: bool = False,
    include_archive: bool = False,
) -> int:
    try:
        with connect_index(root) as conn:
            record = indexed_record(conn, record_id)
            if record is None or (record["archived"] and not include_archive):
                raise KeyError(record_id)
            id_map = load_index_record_map(conn)
            target = id_map[record_id]
            validations = target_review_records(conn, "validations", record_id)
            challenges = target_review_records(conn, "challenges", record_id)
            evidence_ids = evidence_ids_for_record(target, id_map)
            evidence_records = fetch_records(conn, evidence_ids, include_data=True)
            review_analysis = build_review_analysis(
                target,
                validations,
                challenges,
                id_map,
                target_archived=bool(record["archived"]),
            )
            review_state = review_analysis["review_state"]
    except FileNotFoundError as exc:
        error = command_error("index_missing", str(exc), "Run `fo index build` first.")
        if json_output:
            print_json(result_envelope("review", root, ok=False, errors=[error], id=record_id))
        else:
            print(f"ERROR {error['message']}", file=sys.stderr)
        return 1
    except KeyError:
        error = command_error("record_not_found", f"record `{record_id}` was not found")
        if json_output:
            print_json(result_envelope("review", root, ok=False, errors=[error], id=record_id))
        else:
            print(f"ERROR {error['message']}", file=sys.stderr)
        return 1

    if json_output:
        print_json(
            result_envelope(
                "review",
                root,
                id=record_id,
                record=record,
                review_state=review_state,
                support_summary=review_analysis["support_summary"],
                target_evidence_summary=review_analysis["target_evidence_summary"],
                review_evidence_summary=review_analysis["review_evidence_summary"],
                validation_summary=review_analysis["validation_summary"],
                challenge_summary=review_analysis["challenge_summary"],
                contradiction_summary=review_analysis["contradiction_summary"],
                supersession_summary=review_analysis["supersession_summary"],
                staleness_summary=review_analysis["staleness_summary"],
                scope_summary=review_analysis["scope_summary"],
                evidence=evidence_records,
                validations=validations,
                challenges=challenges,
            )
        )
    else:
        print(f"{record_id}: {review_state['primary_label']}")
        if review_state["flags"]:
            print("flags: " + ", ".join(review_state["flags"]))
        print(
            f"{len(evidence_records)} evidence record(s), "
            f"{len(validations)} validation(s), {len(challenges)} challenge(s)"
        )
        source_count = review_analysis["support_summary"]["source_independence"][
            "unique_source_count"
        ]
        unique_paths = review_analysis["validation_summary"]["unique_dependency_path_count"]
        repeated_paths = review_analysis["validation_summary"]["repeated_dependency_path_count"]
        print(f"{source_count} support source(s), {unique_paths} validation path(s)")
        if repeated_paths:
            print(f"{repeated_paths} repeated validation path(s)")
    return 0


def cmd_review(args: argparse.Namespace) -> int:
    return run_review(
        repo_root(),
        args.id,
        json_output=bool(args.json),
        include_archive=bool(args.include_archive),
    )


def cmd_diff_review(args: argparse.Namespace) -> int:
    return run_diff_review(repo_root(), base_ref=str(args.base), json_output=bool(args.json))


def run_graph_neighbors(
    root: Path,
    record_id: str,
    json_output: bool = False,
    include_archive: bool = False,
) -> int:
    records, errors = load_records(root, include_archive=include_archive)
    if errors:
        if json_output:
            print_json(
                result_envelope(
                    "graph neighbors",
                    root,
                    ok=False,
                    errors=[json_error(error) for error in errors],
                    id=record_id,
                )
            )
        else:
            for error in errors:
                print(f"ERROR {error}", file=sys.stderr)
        return 1

    id_map = {record.id: record for record in records if record.id}
    if record_id not in id_map:
        error = command_error("record_not_found", f"record `{record_id}` was not found")
        if json_output:
            print_json(result_envelope("graph neighbors", root, ok=False, errors=[error], id=record_id))
        else:
            print(f"ERROR {error['message']}", file=sys.stderr)
        return 1

    graph = build_graph_data(root, records)
    edges = [
        edge
        for edge in graph["edges"]
        if edge.get("from") == record_id or edge.get("to") == record_id
    ]
    neighbor_ids = sorted(
        {
            str(edge["to"] if edge.get("from") == record_id else edge["from"])
            for edge in edges
            if edge.get("from") and edge.get("to")
        }
    )
    neighbors = [
        {
            "id": neighbor_id,
            "kind": id_map[neighbor_id].kind,
            "label": record_label(id_map[neighbor_id]),
            "path": str(id_map[neighbor_id].path.relative_to(root)),
        }
        for neighbor_id in neighbor_ids
        if neighbor_id in id_map
    ]

    if json_output:
        print_json(
            result_envelope(
                "graph neighbors",
                root,
                id=record_id,
                neighbor_count=len(neighbors),
                neighbors=neighbors,
                edges=edges,
            )
        )
    else:
        for neighbor in neighbors:
            print(f"{neighbor['id']} [{neighbor['kind']}] {neighbor['path']}")
            print(f"  {neighbor['label']}")
        print(f"{len(neighbors)} neighbor(s)")
    return 0


def cmd_graph_neighbors(args: argparse.Namespace) -> int:
    return run_graph_neighbors(
        repo_root(),
        args.id,
        json_output=bool(args.json),
        include_archive=bool(args.include_archive),
    )


def cmd_graph_build(args: argparse.Namespace) -> int:
    root = repo_root()
    records, errors = validate_repo(root, current_only=True)
    if errors:
        if args.json:
            print_json(
                result_envelope(
                    "graph build",
                    root,
                    ok=False,
                    errors=[json_error(error) for error in errors],
                )
            )
        else:
            for error in errors:
                print(f"ERROR {error}", file=sys.stderr)
            print(f"\n{len(errors)} validation error(s)", file=sys.stderr)
        return 1

    graph = build_graph_data(root, records)
    output_dir = root / ".local"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "graph.json"
    output_path.write_text(json.dumps(graph, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.json:
        print_json(
            result_envelope(
                "graph build",
                root,
                graph_path=str(output_path),
                node_count=graph["node_count"],
                edge_count=graph["edge_count"],
            )
        )
    else:
        print(f"Wrote {output_path.relative_to(root)}")
    return 0


def cmd_graph_inspect(args: argparse.Namespace) -> int:
    root = repo_root()
    graph_path = root / ".local" / "graph.json"
    if graph_path.exists():
        graph = json.loads(graph_path.read_text(encoding="utf-8"))
    else:
        records, errors = load_records(root, include_archive=False)
        if errors:
            for error in errors:
                print(f"ERROR {error}", file=sys.stderr)
            return 1
        graph = build_graph_data(root, records)

    needle = args.term.lower()
    matches = [
        node
        for node in graph.get("nodes", [])
        if needle in node.get("id", "").lower()
        or needle in node.get("label", "").lower()
        or needle in node.get("path", "").lower()
    ]
    for node in matches:
        print(f"{node['id']} [{node['kind']}] {node['path']}")
        print(f"  {node['label']}")
    print(f"{len(matches)} match(es)")
    return 0


def cmd_new_source(args: argparse.Namespace) -> int:
    return run_new_source(repo_root(), args)


def cmd_new_evidence(args: argparse.Namespace) -> int:
    return run_new_evidence(repo_root(), args)


def cmd_new_claim(args: argparse.Namespace) -> int:
    return run_new_claim(repo_root(), args)


def cmd_new_validation(args: argparse.Namespace) -> int:
    return run_new_validation(repo_root(), args)


def cmd_new_challenge(args: argparse.Namespace) -> int:
    return run_new_challenge(repo_root(), args)


def cmd_new_relationship(args: argparse.Namespace) -> int:
    return run_new_relationship(repo_root(), args)


def cmd_new_entity(args: argparse.Namespace) -> int:
    return run_new_entity(repo_root(), args)


def cmd_new_metric(args: argparse.Namespace) -> int:
    return run_new_metric(repo_root(), args)


def cmd_new_event(args: argparse.Namespace) -> int:
    return run_new_event(repo_root(), args)


def cmd_new_dataset(args: argparse.Namespace) -> int:
    return run_new_dataset(repo_root(), args)


def cmd_new_thesis(args: argparse.Namespace) -> int:
    return run_new_thesis(repo_root(), args)


def cmd_new_question(args: argparse.Namespace) -> int:
    return run_new_question(repo_root(), args)


def add_new_common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--id", help="explicit canonical id")
    parser.add_argument("--path", help="explicit output path")
    parser.add_argument("--submitted-by", required=True, help="GitHub contributor id, e.g. github:alice")
    parser.add_argument("--created-at", help="explicit record creation timestamp")
    parser.add_argument("--risk-flag", action="append", default=[], help="repeatable risk flag")
    parser.add_argument("--overwrite", action="store_true", help="replace an existing file")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")


def add_dependency_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--evidence", action="append", default=[], help="dependent evidence id")
    parser.add_argument("--claim", action="append", default=[], help="dependent claim id")
    parser.add_argument("--relationship", action="append", default=[], help="dependent relationship id")
    parser.add_argument("--thesis", action="append", default=[], help="dependent thesis id")
    parser.add_argument("--metric", action="append", default=[], help="dependent metric id")
    parser.add_argument("--event", action="append", default=[], help="dependent event id")
    parser.add_argument("--dataset", action="append", default=[], help="dependent dataset id")


def add_new_file_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--id", help="explicit canonical id")
    parser.add_argument("--path", help="explicit output path")
    parser.add_argument("--created-at", help="explicit record creation timestamp")
    parser.add_argument("--risk-flag", action="append", default=[], help="repeatable risk flag")
    parser.add_argument("--overwrite", action="store_true", help="replace an existing file")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fo", description="Finance OSINT local tooling")
    subparsers = parser.add_subparsers(dest="command", required=True)

    lint_parser = subparsers.add_parser("lint", help="validate repo records")
    lint_parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    lint_parser.add_argument(
        "--current-only",
        action="store_true",
        help="skip archive records during validation",
    )
    lint_parser.set_defaults(func=cmd_lint)

    new_parser = subparsers.add_parser("new", help="create deterministic YAML records")
    new_subparsers = new_parser.add_subparsers(dest="new_command", required=True)

    entity_parser = new_subparsers.add_parser("entity", help="create an entity record")
    add_new_common_options(entity_parser)
    entity_parser.add_argument(
        "--entity-type",
        required=True,
        choices=[
            "company",
            "person",
            "product",
            "component",
            "security",
            "listing",
            "market",
            "geography",
            "architecture",
            "commodity",
            "technology",
            "regulation",
            "fund",
            "service",
        ],
    )
    entity_parser.add_argument("--name", required=True)
    entity_parser.add_argument("--alias", action="append", default=[])
    entity_parser.add_argument("--identifier", action="append", default=[], help="repeatable key=value")
    entity_parser.add_argument("--description")
    entity_parser.add_argument(
        "--state",
        choices=["active", "inactive", "proposed", "merged", "retired"],
        default="proposed",
    )
    entity_parser.set_defaults(func=cmd_new_entity)

    source_parser = new_subparsers.add_parser("source", help="create a source record")
    add_new_common_options(source_parser)
    source_parser.add_argument("--source-type", required=True)
    source_parser.add_argument("--title", required=True)
    source_parser.add_argument("--public-status", required=True, choices=["public", "nonpublic", "unknown"])
    source_parser.add_argument(
        "--source-perspective",
        choices=SOURCE_PERSPECTIVES,
        default="unknown",
    )
    source_parser.add_argument("--accessed-at", required=True)
    source_parser.add_argument(
        "--content-mode",
        required=True,
        choices=[
            "metadata_only",
            "excerpt",
            "summary",
            "redacted_summary",
            "small_fixture",
            "external_link",
        ],
    )
    source_parser.add_argument("--publisher")
    source_parser.add_argument("--url")
    source_parser.add_argument("--archive-url")
    source_parser.add_argument("--published-at")
    source_parser.add_argument("--provenance")
    source_parser.add_argument(
        "--source-artifact",
        action="append",
        default=[],
        help="repeatable artifacts/sources/... png/jpg/jpeg/pdf path",
    )
    source_parser.set_defaults(func=cmd_new_source)

    evidence_parser = new_subparsers.add_parser("evidence", help="create an evidence record")
    add_new_common_options(evidence_parser)
    evidence_parser.add_argument(
        "--evidence-class",
        required=True,
        choices=[
            "public_primary",
            "public_secondary",
            "firsthand_public",
            "firsthand_private",
            "anonymous_internal",
            "rumor",
        ],
    )
    evidence_parser.add_argument("--source", required=True)
    evidence_parser.add_argument("--summary", required=True)
    evidence_parser.add_argument(
        "--content-mode",
        required=True,
        choices=[
            "metadata_only",
            "excerpt",
            "summary",
            "redacted_summary",
            "small_fixture",
            "external_link",
        ],
    )
    evidence_parser.add_argument("--observed-at", required=True)
    evidence_parser.add_argument(
        "--source-attribution",
        required=True,
        choices=["named_public", "anonymous_to_public", "unknown"],
    )
    evidence_parser.add_argument("--excerpt")
    evidence_parser.add_argument("--locator", action="append", default=[], help="repeatable key=value")
    evidence_parser.add_argument("--source-access-json", help="JSON object for source_access")
    evidence_parser.add_argument("--verification-status")
    evidence_parser.add_argument(
        "--source-artifact",
        action="append",
        default=[],
        help="repeatable artifacts/sources/... png/jpg/jpeg/pdf path",
    )
    evidence_parser.set_defaults(func=cmd_new_evidence)

    claim_parser = new_subparsers.add_parser("claim", help="create a claim record")
    add_new_common_options(claim_parser)
    claim_parser.add_argument("--statement", required=True)
    claim_parser.add_argument("--subject", required=True)
    claim_parser.add_argument("--predicate", required=True)
    claim_parser.add_argument("--object")
    claim_parser.add_argument(
        "--support-type",
        required=True,
        choices=["direct", "observed", "inferred", "private_attestation", "rumor"],
    )
    claim_parser.add_argument("--evidence", action="append", required=True, help="supporting evidence id")
    claim_parser.add_argument("--qualifier", action="append", default=[], help="repeatable key=value")
    claim_parser.add_argument("--time-start")
    claim_parser.add_argument("--time-end")
    claim_parser.add_argument("--methodology")
    claim_parser.add_argument("--proposed-predicate-definition")
    claim_parser.set_defaults(func=cmd_new_claim)

    validation_parser = new_subparsers.add_parser("validation", help="create a validation record")
    add_new_common_options(validation_parser)
    validation_parser.add_argument("--target", required=True)
    validation_parser.add_argument(
        "--verdict",
        required=True,
        choices=[
            "attests",
            "supports",
            "partially_supports",
            "disputes",
            "falsifies",
            "marks_stale",
            "withdraws",
        ],
    )
    validation_parser.add_argument("--summary", required=True)
    add_dependency_options(validation_parser)
    validation_parser.set_defaults(func=cmd_new_validation)

    challenge_parser = new_subparsers.add_parser("challenge", help="create a challenge record")
    add_new_common_options(challenge_parser)
    challenge_parser.add_argument("--target", required=True)
    challenge_parser.add_argument(
        "--challenge-type",
        required=True,
        choices=[
            "contradiction",
            "missing_evidence",
            "source_quality",
            "scope_error",
            "outdated",
            "ontology_issue",
            "materiality_dispute",
            "other",
        ],
    )
    challenge_parser.add_argument("--summary", required=True)
    challenge_parser.add_argument("--addressed-by")
    challenge_parser.add_argument("--withdrawn-by")
    challenge_parser.add_argument("--superseded-by")
    add_dependency_options(challenge_parser)
    challenge_parser.set_defaults(func=cmd_new_challenge)

    relationship_parser = new_subparsers.add_parser("relationship", help="create a relationship record")
    add_new_common_options(relationship_parser)
    relationship_parser.add_argument("--type", required=True)
    relationship_parser.add_argument(
        "--participant",
        action="append",
        required=True,
        help="repeatable role=entity:id",
    )
    relationship_parser.add_argument("--derived-claim", action="append", default=[])
    relationship_parser.add_argument("--derived-evidence", action="append", default=[])
    relationship_parser.add_argument("--scope", action="append", default=[], help="repeatable key=record:id")
    relationship_parser.add_argument("--qualifier", action="append", default=[])
    relationship_parser.add_argument("--time-start")
    relationship_parser.add_argument("--time-end")
    relationship_parser.add_argument("--materiality-level")
    relationship_parser.add_argument(
        "--materiality-basis",
        choices=["observed", "inferred", "estimated", "unknown"],
    )
    relationship_parser.add_argument("--proposed-type-definition")
    relationship_parser.set_defaults(func=cmd_new_relationship)

    metric_parser = new_subparsers.add_parser("metric", help="create a metric record")
    add_new_common_options(metric_parser)
    metric_parser.add_argument("--entity", required=True)
    metric_parser.add_argument("--metric-definition", required=True)
    metric_parser.add_argument("--value", required=True, type=float)
    metric_parser.add_argument("--unit", required=True)
    metric_parser.add_argument("--period", action="append", required=True, help="repeatable key=value")
    metric_parser.add_argument(
        "--value-basis",
        required=True,
        choices=["reported", "observed", "derived", "estimated", "restated"],
    )
    metric_parser.add_argument("--evidence", action="append", required=True)
    metric_parser.add_argument("--source-locator", action="append", default=[], help="repeatable key=value")
    metric_parser.add_argument("--dimension", action="append", default=[], help="repeatable key=value")
    metric_parser.add_argument("--as-of")
    metric_parser.add_argument("--reported-at")
    metric_parser.add_argument("--published-at")
    metric_parser.add_argument("--restated-from")
    metric_parser.add_argument("--methodology")
    metric_parser.add_argument("--limitations")
    metric_parser.set_defaults(func=cmd_new_metric)

    event_parser = new_subparsers.add_parser("event", help="create an event record")
    add_new_common_options(event_parser)
    event_parser.add_argument("--event-type", required=True)
    event_parser.add_argument(
        "--event-state",
        required=True,
        choices=["expected", "occurred", "cancelled", "missed"],
    )
    event_parser.add_argument("--title", required=True)
    event_parser.add_argument("--entity", action="append", required=True, help="related entity id")
    event_parser.add_argument("--evidence", action="append", required=True)
    event_parser.add_argument("--occurred-at")
    event_parser.add_argument("--expected-at")
    event_parser.add_argument("--effective-at")
    event_parser.add_argument("--period", action="append", default=[], help="repeatable key=value")
    event_parser.add_argument("--property", action="append", default=[], help="repeatable key=value")
    event_parser.set_defaults(func=cmd_new_event)

    dataset_parser = new_subparsers.add_parser("dataset", help="create a dataset record")
    add_new_common_options(dataset_parser)
    dataset_parser.add_argument("--title", required=True)
    dataset_parser.add_argument("--dataset-type", required=True)
    dataset_parser.add_argument("--publisher", required=True)
    dataset_parser.add_argument("--coverage", action="append", required=True, help="repeatable key=value")
    dataset_parser.add_argument("--access", action="append", required=True, help="repeatable key=value")
    dataset_parser.add_argument("--source", action="append", required=True, help="source id")
    dataset_parser.add_argument(
        "--content-mode",
        required=True,
        choices=[
            "metadata_only",
            "excerpt",
            "summary",
            "redacted_summary",
            "small_fixture",
            "external_link",
        ],
    )
    dataset_parser.add_argument("--content-hash")
    dataset_parser.add_argument("--license")
    dataset_parser.add_argument("--limitations")
    dataset_parser.set_defaults(func=cmd_new_dataset)

    thesis_parser = new_subparsers.add_parser("thesis", help="create a thesis record")
    add_new_common_options(thesis_parser)
    thesis_parser.add_argument("--title", required=True)
    thesis_parser.add_argument("--summary", required=True)
    thesis_parser.add_argument("--stance")
    thesis_parser.add_argument("--time-horizon")
    thesis_parser.add_argument("--forecast-json", help="JSON object forecast expression")
    thesis_parser.add_argument("--contradicting-evidence", action="append", default=[])
    add_dependency_options(thesis_parser)
    thesis_parser.set_defaults(func=cmd_new_thesis)

    question_parser = new_subparsers.add_parser("question", help="create a proof-gap question")
    add_new_common_options(question_parser)
    question_parser.add_argument("--question", required=True)
    question_parser.add_argument("--entity", action="append", required=True, help="related entity id")
    question_parser.add_argument("--proof-type", required=True)
    question_parser.add_argument("--priority", required=True, choices=["low", "medium", "high"])
    question_parser.add_argument("--related-evidence", action="append", default=[])
    question_parser.add_argument("--related-claim", action="append", default=[])
    question_parser.add_argument("--related-relationship", action="append", default=[])
    question_parser.add_argument("--related-thesis", action="append", default=[])
    question_parser.add_argument("--next-action", action="append", default=[])
    question_parser.add_argument("--resolved-by", action="append", default=[])
    question_parser.set_defaults(func=cmd_new_question)

    index_parser = subparsers.add_parser("index", help="local SQLite index utilities")
    index_subparsers = index_parser.add_subparsers(dest="index_command", required=True)

    index_build_parser = index_subparsers.add_parser("build", help="build .local/index.sqlite")
    index_build_parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    index_build_parser.set_defaults(func=cmd_index_build)

    search_parser = subparsers.add_parser("search", help="search indexed records")
    search_parser.add_argument("query", help="search query")
    search_parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    search_parser.add_argument("--include-archive", action="store_true", help="include archive records")
    search_parser.add_argument("--limit", type=int, default=20, help="maximum result count")
    search_parser.set_defaults(func=cmd_search)

    context_parser = subparsers.add_parser("context", help="show indexed context around a record")
    context_parser.add_argument("id", help="record id")
    context_parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    context_parser.add_argument("--include-archive", action="store_true", help="include archive records")
    context_parser.set_defaults(func=cmd_context)

    review_parser = subparsers.add_parser("review", help="derive local review state for a record")
    review_parser.add_argument("id", help="record id")
    review_parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    review_parser.add_argument("--include-archive", action="store_true", help="include archive records")
    review_parser.set_defaults(func=cmd_review)

    diff_review_parser = subparsers.add_parser(
        "diff-review",
        help="review repo-native record changes against a Git base ref",
    )
    diff_review_parser.add_argument("base", nargs="?", default="HEAD", help="Git base ref")
    diff_review_parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    diff_review_parser.set_defaults(func=cmd_diff_review)

    graph_parser = subparsers.add_parser("graph", help="graph utilities")
    graph_subparsers = graph_parser.add_subparsers(dest="graph_command", required=True)

    build_parser_ = graph_subparsers.add_parser("build", help="build .local/graph.json")
    build_parser_.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    build_parser_.set_defaults(func=cmd_graph_build)

    neighbors_parser = graph_subparsers.add_parser("neighbors", help="show graph neighbors for a record")
    neighbors_parser.add_argument("id", help="record id")
    neighbors_parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    neighbors_parser.add_argument(
        "--include-archive", action="store_true", help="include archive records"
    )
    neighbors_parser.set_defaults(func=cmd_graph_neighbors)

    inspect_parser = graph_subparsers.add_parser("inspect", help="inspect graph records")
    inspect_parser.add_argument("term", help="case-insensitive search term")
    inspect_parser.set_defaults(func=cmd_graph_inspect)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
