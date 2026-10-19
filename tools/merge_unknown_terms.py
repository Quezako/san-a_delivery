#!/usr/bin/env python3
"""Normalize and classify unknown ingredients exported by the userscript.

Usage:
    python tools/merge_unknown_terms.py --input san-a-ibs-unknown-terms.json
    python tools/merge_unknown_terms.py --input san-a-ibs-unknown-terms.json --output data/unknown_terms_report.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

from fodmap_reference_lib import ROOT, DATA_DIR, load_json, load_runtime_reference, normalize_term, summarize_unknown_terms, write_json, write_runtime_reference

LIBRETRANSLATE_ENDPOINTS = [
    "https://translate.argosopentech.com/translate",
    "https://libretranslate.com/translate",
    "https://translate.terraprint.co/translate",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Translate unknown Japanese ingredients via LibreTranslate and merge them into the local reference base.")
    parser.add_argument("--input", default=str(ROOT / "san-a-ibs-unknown-terms.json"), help="Path to the JSON export of unknown terms.")
    parser.add_argument("--reference", default=str(DATA_DIR / "fodmap_reference.json"), help="Path to the local reference JSON.")
    parser.add_argument("--output", default=str(ROOT / "san-a-ibs-unknown-terms-report.json"), help="Output JSON path for the report.")
    parser.add_argument("--endpoint", default="", help="Optional LibreTranslate endpoint override.")
    parser.add_argument("--source-lang", default="ja", help="Source language for translation.")
    parser.add_argument("--target-lang", default="en", help="Primary target language for canonical term.")
    return parser.parse_args()


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "_", value.lower().strip())
    cleaned = cleaned.strip("_")
    return cleaned or "ingredient"


def translate_text(term: str, source_lang: str, target_lang: str, endpoint_override: str = "") -> str:
    text = str(term).strip()
    if not text:
        return ""

    endpoints = [endpoint_override] if endpoint_override else LIBRETRANSLATE_ENDPOINTS
    payload = json.dumps({"q": text, "source": source_lang, "target": target_lang, "format": "text"}).encode("utf-8")

    last_error: Exception | None = None
    for endpoint in endpoints:
        if not endpoint:
            continue
        try:
            request = urllib.request.Request(
                endpoint,
                data=payload,
                headers={"Content-Type": "application/json", "Accept": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=25) as response:
                result = json.loads(response.read().decode("utf-8"))

            if isinstance(result, dict):
                translated = result.get("translatedText")
                if translated:
                    return str(translated).strip()

                data = result.get("data")
                if isinstance(data, list) and data:
                    translated = data[0].get("translatedText")
                    if translated:
                        return str(translated).strip()

            if isinstance(result, list) and result:
                translated = result[0].get("translatedText") if isinstance(result[0], dict) else None
                if translated:
                    return str(translated).strip()

        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as exc:
            last_error = exc
            continue

    if last_error is not None:
        raise RuntimeError(f"Translation failed for '{term}' via LibreTranslate: {last_error}")
    raise RuntimeError(f"Translation failed for '{term}' via LibreTranslate: no endpoint available")


def build_entry_from_translation(term: str, english_name: str, french_name: str, category: str = "ingredient") -> dict:
    canonical = str(english_name).strip()
    food_id = slugify(canonical)
    labels_ja = [term]
    labels_en = [canonical]
    labels_fr = [str(french_name).strip()]
    alias_values = sorted(set([canonical, *labels_ja, *labels_en, *labels_fr]))

    entry = {
        "food_id": food_id,
        "canonical": canonical,
        "category": category,
        "labels_ja": labels_ja,
        "labels_en": labels_en,
        "labels_fr": labels_fr,
        "aliases": alias_values,
        "is_fodmap": False,
        "fodmap_group": "unknown",
        "fodmap_level": "unknown",
        "confidence": "low",
        "notes": f"Auto-generated from LibreTranslate enrichment for '{term}'.",
        "source_refs": ["libretranslate_enrichment"],
        "source": "libretranslate_enrichment",
    }
    return entry


def merge_entry_into_reference(reference_entries: dict, translated_entry: dict, term: str) -> bool:
    food_id = translated_entry["food_id"]
    existing = reference_entries.get(food_id)
    if existing is None:
        reference_entries[food_id] = translated_entry
        return True

    for key in ("labels_ja", "labels_en", "labels_fr"):
        for value in translated_entry[key]:
            if value not in existing.get(key, []):
                existing.setdefault(key, []).append(value)

    existing.setdefault("aliases", [])
    for value in translated_entry["aliases"]:
        if value not in existing["aliases"]:
            existing["aliases"].append(value)

    existing.setdefault("source_refs", [])
    for value in translated_entry["source_refs"]:
        if value not in existing["source_refs"]:
            existing["source_refs"].append(value)

    existing["source"] = "libretranslate_enrichment"
    existing["notes"] = existing.get("notes", "") + f" | merged from {term} via LibreTranslate"
    return False


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    reference_path = Path(args.reference)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 1

    payload = load_json(input_path, {})
    unknown_terms = []
    reference_version = payload.get("reference_version", "unknown") if isinstance(payload, dict) else None

    if isinstance(payload, dict):
        unknown_terms = payload.get("unknown_terms", [])
    else:
        unknown_terms = payload

    reference_entries = load_runtime_reference(reference_path)
    summary = summarize_unknown_terms(reference_entries, unknown_terms)

    merged_count = 0
    merged_terms = []
    translations = []

    for term in summary["missing_terms"]:
        try:
            english_name = translate_text(term, args.source_lang, args.target_lang, args.endpoint)
            french_name = translate_text(term, args.source_lang, "fr", args.endpoint)
        except Exception as exc:
            print(f"Skipping '{term}': {exc}", file=sys.stderr)
            continue

        if not english_name:
            continue

        translated_entry = build_entry_from_translation(term, english_name, french_name or english_name)
        was_new = merge_entry_into_reference(reference_entries, translated_entry, term)
        translations.append({"term": term, "english": english_name, "french": french_name or english_name, "food_id": translated_entry["food_id"]})

        if was_new:
            merged_terms.append(term)
            merged_count += 1

    if merged_count:
        write_runtime_reference(reference_path, reference_entries)

    report = {
        "input_file": str(input_path),
        "reference_file": str(reference_path),
        "reference_version": reference_version,
        "summary": {
            "total_unknown_terms": summary["total_unknown_terms"],
            "known_count": summary["known_count"],
            "missing_count": summary["missing_count"],
            "merged_count": merged_count,
        },
        "already_known": summary["already_known"],
        "missing_terms": summary["missing_terms"],
        "merged_terms": merged_terms,
        "translations": translations,
    }

    write_json(output_path, report)

    print(f"unknown terms file: {input_path}")
    print(f"known terms: {summary['known_count']}")
    print(f"missing terms: {summary['missing_count']}")
    print(f"merged entries: {merged_count}")
    print(f"translations requested: {len(translations)}")
    print(f"report written to: {output_path}")

    if merged_terms:
        print("Merged into reference:")
        for value in merged_terms:
            print(f"  - {value}")
    else:
        print("No translated terms were merged into the base reference.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
