from __future__ import annotations

import argparse
import json
import re
import sqlite3
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


def record_label(record: Record) -> str:
    for key in ("name", "title", "statement", "summary", "label"):
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


def evidence_ids_for_record(record: Record, id_map: dict[str, Record]) -> list[str]:
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
            return as_reference_list(depends_on.get("evidence"))
    if record.kind == "thesis":
        depends_on = record.data.get("depends_on", {})
        evidence_ids: list[str] = []
        if isinstance(depends_on, dict):
            evidence_ids.extend(as_reference_list(depends_on.get("evidence")))
            for claim_id in as_string_list(depends_on.get("claims")):
                claim = id_map.get(claim_id)
                if claim:
                    evidence_ids.extend(evidence_ids_for_claim(claim))
            for relationship_id in as_string_list(depends_on.get("relationships")):
                relationship = id_map.get(relationship_id)
                if relationship:
                    evidence_ids.extend(evidence_ids_for_relationship(relationship, id_map))
        return sorted(set(evidence_ids))
    return []


def is_open_challenge(record: dict[str, Any]) -> bool:
    data = record.get("data", {})
    return not any(data.get(key) for key in ("addressed_by", "withdrawn_by", "superseded_by"))


def derive_review_state(
    target: Record,
    validations: list[dict[str, Any]],
    challenges: list[dict[str, Any]],
    evidence_classes: set[str],
) -> dict[str, Any]:
    verdicts = {str(item["data"].get("verdict")) for item in validations}
    open_challenges = [challenge for challenge in challenges if is_open_challenge(challenge)]
    flags: list[str] = []

    if open_challenges:
        flags.append("has_open_challenge")
    if evidence_classes & LOW_TRUST_EVIDENCE_CLASSES:
        flags.append("has_low_trust_support")
    if evidence_classes & {"firsthand_private", "anonymous_internal"}:
        flags.append("has_private_support")
    if target.data.get("contradicts") or any(
        challenge["data"].get("challenge_type") == "contradiction" for challenge in challenges
    ):
        flags.append("has_contradiction")
    if target.data.get("superseded_by") or target.data.get("duplicate_of"):
        flags.append("has_superseding_record")

    if target.data.get("withdrawn_by") or "withdraws" in verdicts:
        primary_label = "withdrawn"
    elif target.data.get("superseded_by") or target.data.get("duplicate_of"):
        primary_label = "superseded"
    elif open_challenges or verdicts & {"disputes", "falsifies"}:
        primary_label = "contested"
    elif evidence_classes and evidence_classes <= LOW_TRUST_EVIDENCE_CLASSES:
        primary_label = "low_trust_only"
    elif "partially_supports" in verdicts:
        primary_label = "partially_supported"
    elif verdicts & {"attests", "supports"}:
        primary_label = "supported"
    else:
        primary_label = "unreviewed"

    return {"primary_label": primary_label, "flags": sorted(set(flags))}


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
    return records, errors


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
        "accessed_at": args.accessed_at,
        "content_mode": args.content_mode,
        "submitted_by": args.submitted_by,
    }
    for field in ("publisher", "url", "archive_url", "published_at", "provenance"):
        value = getattr(args, field)
        if value:
            data[field] = value
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


def run_lint(root: Path, json_output: bool = False, current_only: bool = False) -> int:
    records, errors = validate_repo(root, current_only=current_only)
    if json_output:
        print(
            json.dumps(
                {
                    "ok": not errors,
                    "command": "lint",
                    "repo_root": str(root),
                    "records_checked": len(records),
                    "warnings": [],
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
            evidence_classes = {
                str(evidence["data"].get("evidence_class"))
                for evidence in evidence_records
                if isinstance(evidence.get("data"), dict)
            }
            review_state = derive_review_state(target, validations, challenges, evidence_classes)
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
    return 0


def cmd_review(args: argparse.Namespace) -> int:
    return run_review(
        repo_root(),
        args.id,
        json_output=bool(args.json),
        include_archive=bool(args.include_archive),
    )


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
