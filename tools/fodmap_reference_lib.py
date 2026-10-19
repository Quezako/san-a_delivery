#!/usr/bin/env python3
"""Shared helpers for the San-A FODMAP reference pipeline."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


def load_json(path: str | Path, default: Any = None) -> Any:
    file_path = Path(path)
    if not file_path.exists():
        return default
    with file_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: str | Path, payload: Any) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def normalize_term(value: str) -> str:
    if value is None:
        return ""
    cleaned = re.sub(r"[\s_\-]+", "", str(value).strip().lower())
    cleaned = re.sub(r"[()\[\]{}<>.,!?:;\"'’“”]+", "", cleaned)
    return cleaned


def normalize_aliases(values: Iterable[str]) -> List[str]:
    normalized = []
    seen = set()
    for value in values or []:
        cleaned = normalize_term(value)
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        normalized.append(cleaned)
    return sorted(normalized)


def build_runtime_reference(foods_table: Sequence[Dict[str, Any]], fodmap_rules: Sequence[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    by_id = {item["food_id"]: item for item in foods_table}
    by_food_id = {item["food_id"]: item for item in fodmap_rules}

    reference: Dict[str, Dict[str, Any]] = {}
    for food_id, food in by_id.items():
        rule = by_food_id.get(food_id, {})
        alias_values = []
        for key in ("labels_ja", "labels_en", "labels_fr"):
            alias_values.extend(food.get(key, []))
        runtime_entry = {
            "food_id": food_id,
            "canonical": food["canonical"],
            "category": food.get("category"),
            "labels_ja": food.get("labels_ja", []),
            "labels_en": food.get("labels_en", []),
            "labels_fr": food.get("labels_fr", []),
            "aliases": normalize_aliases(alias_values),
            "is_fodmap": bool(rule.get("is_fodmap", False)),
            "fodmap_group": rule.get("fodmap_group", "unknown"),
            "fodmap_level": rule.get("fodmap_level", "unknown"),
            "confidence": rule.get("confidence", "low"),
            "notes": food.get("notes", ""),
            "source_refs": food.get("source_refs", []),
            "source": rule.get("source", "curated_local"),
        }
        reference[food_id] = runtime_entry
    return reference


def load_runtime_reference(path: str | Path | None = None) -> Dict[str, Dict[str, Any]]:
    file_path = Path(path) if path is not None else DATA_DIR / "fodmap_reference.json"
    payload = load_json(file_path, {})
    if isinstance(payload, dict) and "entries" in payload:
        return payload.get("entries", {})
    return payload if isinstance(payload, dict) else {}


def load_unknown_terms(path: str | Path) -> List[str]:
    file_path = Path(path)
    payload = load_json(file_path, [])
    if isinstance(payload, list):
        terms = payload
    elif isinstance(payload, dict):
        terms = payload.get("unknown_terms", [])
    else:
        terms = []
    return [str(item).strip() for item in terms if str(item).strip()]


def write_runtime_reference(path: str | Path, entries: Dict[str, Dict[str, Any]]) -> None:
    file_path = Path(path)
    payload = {"schema": "fodmap_reference_v1", "entries": entries}
    write_json(file_path, payload)

    embed_path = file_path.parent / ".." / "src" / "fodmap_reference_embed.js"
    embed_path = embed_path.resolve()
    js = "globalThis.SAN_A_FODMAP_REFERENCE = " + json.dumps(payload, ensure_ascii=False, indent=2) + ";\n"
    js += "if (typeof module !== 'undefined') { module.exports = globalThis.SAN_A_FODMAP_REFERENCE; }\n"
    embed_path.write_text(js, encoding="utf-8")


def summarize_unknown_terms(reference_entries: Dict[str, Dict[str, Any]], unknown_terms: Sequence[str]) -> Dict[str, Any]:
    known = set()
    for entry in reference_entries.values():
        for alias in entry.get("aliases", []) or []:
            known.add(str(alias).strip().lower())

    normalized_unknown = []
    seen = set()
    for term in unknown_terms:
        normalized = normalize_term(term)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        normalized_unknown.append(normalized)

    present = []
    missing = []
    for term in normalized_unknown:
        if term in known:
            present.append(term)
        else:
            missing.append(term)

    return {
        "total_unknown_terms": len(normalized_unknown),
        "already_known": present,
        "missing_terms": missing,
        "known_count": len(present),
        "missing_count": len(missing),
    }
