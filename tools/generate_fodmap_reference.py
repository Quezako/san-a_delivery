#!/usr/bin/env python3
"""Generate a local FODMAP reference base for the San-A IBS checker.

The data model intentionally keeps two source tables:
- foods_table: ingredient / food names and multilingual aliases
- fodmap_rules: risk classification and FODMAP group

The generated runtime file merges both tables into a single flat reference map for the userscript.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from fodmap_reference_lib import build_runtime_reference as build_runtime_reference_map, normalize_aliases

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

SOURCE_MANIFEST = [
    {
        "name": "Monash University FODMAP app",
        "kind": "medical_reference",
        "url": "https://www.monashfodmap.com/",
        "notes": "Reference on common FODMAP trigger foods and food groups.",
    },
    {
        "name": "Darius Kazemi / corpora (food names)",
        "kind": "food_corpus",
        "url": "https://github.com/dariusk/corpora/tree/master/data/foods",
        "notes": "General food nomenclature corpus used as a naming baseline.",
    },
    {
        "name": "Japanese supermarket ingredient vocabulary",
        "kind": "curated_local",
        "url": "internal",
        "notes": "Curated list of common Japanese food names and ingredient aliases used in the San-A context.",
    },
]

FOODS_TABLE: List[Dict[str, Any]] = [
    {
        "food_id": "apple",
        "canonical": "apple",
        "category": "fruit",
        "labels_ja": ["リンゴ", "りんご", "アップル"],
        "labels_en": ["apple"],
        "labels_fr": ["pomme"],
        "notes": "Common high-fructose fruit often flagged in IBS guidance.",
        "source_refs": ["monash", "dariusk", "japan_local"],
    },
    {
        "food_id": "pear",
        "canonical": "pear",
        "category": "fruit",
        "labels_ja": ["梨", "なし"],
        "labels_en": ["pear"],
        "labels_fr": ["poire"],
        "notes": "Often moderate to high in fructose depending on serving size.",
        "source_refs": ["monash", "japan_local"],
    },
    {
        "food_id": "watermelon",
        "canonical": "watermelon",
        "category": "fruit",
        "labels_ja": ["スイカ", "すいか"],
        "labels_en": ["watermelon"],
        "labels_fr": ["pastèque"],
        "notes": "High-FODMAP fruit in many IBS guides.",
        "source_refs": ["monash", "japan_local"],
    },
    {
        "food_id": "mango",
        "canonical": "mango",
        "category": "fruit",
        "labels_ja": ["マンゴー", "まんごー"],
        "labels_en": ["mango"],
        "labels_fr": ["mangue"],
        "notes": "Fructose-rich fruit; often grouped with trigger fruits.",
        "source_refs": ["monash", "japan_local"],
    },
    {
        "food_id": "garlic",
        "canonical": "garlic",
        "category": "vegetable",
        "labels_ja": ["にんにく", "ニンニク"],
        "labels_en": ["garlic"],
        "labels_fr": ["ail"],
        "notes": "Common high-fructan ingredient in Japanese and Asian dishes.",
        "source_refs": ["monash", "japan_local"],
    },
    {
        "food_id": "onion",
        "canonical": "onion",
        "category": "vegetable",
        "labels_ja": ["玉ねぎ", "たまねぎ", "オニオン"],
        "labels_en": ["onion"],
        "labels_fr": ["oignon"],
        "notes": "Very common trigger ingredient.",
        "source_refs": ["monash", "japan_local"],
    },
    {
        "food_id": "shallot",
        "canonical": "shallot",
        "category": "vegetable",
        "labels_ja": ["エシャロット", "えしゃろっと"],
        "labels_en": ["shallot"],
        "labels_fr": ["échalote"],
        "notes": "Fructan-rich allium.",
        "source_refs": ["monash", "japan_local"],
    },
    {
        "food_id": "leek",
        "canonical": "leek",
        "category": "vegetable",
        "labels_ja": ["ネギ", "ねぎ", "リーク"],
        "labels_en": ["leek", "green onion"],
        "labels_fr": ["poireau"],
        "notes": "Also frequently used in Japanese cooking as green onion / leek-like aromatics.",
        "source_refs": ["monash", "japan_local"],
    },
    {
        "food_id": "gobo",
        "canonical": "gobo",
        "category": "vegetable",
        "labels_ja": ["ごぼう", "牛蒡", "ゴボウ"],
        "labels_en": ["burdock", "burdock root"],
        "labels_fr": ["bardane", "racine de bardane"],
        "notes": "Common Japanese root vegetable, often low in FODMAPs in standard portions.",
        "source_refs": ["japan_local", "monash"],
    },
    {
        "food_id": "asparagus",
        "canonical": "asparagus",
        "category": "vegetable",
        "labels_ja": ["アスパラガス", " asparagus "],
        "labels_en": ["asparagus"],
        "labels_fr": ["asperge"],
        "notes": "Common fructan-containing vegetable.",
        "source_refs": ["monash", "japan_local"],
    },
    {
        "food_id": "wheat",
        "canonical": "wheat",
        "category": "grain",
        "labels_ja": ["小麦", "こむぎ", "パン", "小麦粉"],
        "labels_en": ["wheat", "wheat flour"],
        "labels_fr": ["blé"],
        "notes": "Classical fructan source in many food products.",
        "source_refs": ["monash", "japan_local"],
    },
    {
        "food_id": "rye",
        "canonical": "rye",
        "category": "grain",
        "labels_ja": ["ライ麦", "らいばく"],
        "labels_en": ["rye"],
        "labels_fr": ["seigle"],
        "notes": "Fructan-rich grain.",
        "source_refs": ["monash", "japan_local"],
    },
    {
        "food_id": "barley",
        "canonical": "barley",
        "category": "grain",
        "labels_ja": ["大麦", "おおむぎ"],
        "labels_en": ["barley"],
        "labels_fr": ["orge"],
        "notes": "Fructan-rich grain often included in cereals and soups.",
        "source_refs": ["monash", "japan_local"],
    },
    {
        "food_id": "milk",
        "canonical": "milk",
        "category": "dairy",
        "labels_ja": ["牛乳", "ぎゅうにゅう", "ミルク"],
        "labels_en": ["milk"],
        "labels_fr": ["lait"],
        "notes": "Lactose-containing dairy product.",
        "source_refs": ["monash", "japan_local"],
    },
    {
        "food_id": "yogurt",
        "canonical": "yogurt",
        "category": "dairy",
        "labels_ja": ["ヨーグルト", "yogurt"],
        "labels_en": ["yogurt"],
        "labels_fr": ["yaourt"],
        "notes": "Often problematic due to lactose.",
        "source_refs": ["monash", "japan_local"],
    },
    {
        "food_id": "soft_cheese",
        "canonical": "soft_cheese",
        "category": "dairy",
        "labels_ja": ["軟 cheese", "ソフトチーズ", "soft cheese"],
        "labels_en": ["soft cheese"],
        "labels_fr": ["fromage frais", "fromage à pâte molle"],
        "notes": "Lactose can be elevated in soft cheeses.",
        "source_refs": ["monash", "japan_local"],
    },
    {
        "food_id": "chickpea",
        "canonical": "chickpea",
        "category": "legume",
        "labels_ja": ["ひよこ豆", "ひよこまめ", " chickpea "],
        "labels_en": ["chickpea"],
        "labels_fr": ["pois chiche"],
        "notes": "Classic GOS-rich legume.",
        "source_refs": ["monash", "japan_local"],
    },
    {
        "food_id": "lentil",
        "canonical": "lentil",
        "category": "legume",
        "labels_ja": ["レンズ豆", "レンズマメ", " lentil "],
        "labels_en": ["lentil"],
        "labels_fr": ["lentille"],
        "notes": "GOS-rich legume.",
        "source_refs": ["monash", "japan_local"],
    },
    {
        "food_id": "beans",
        "canonical": "beans",
        "category": "legume",
        "labels_ja": ["豆", "まめ", "beans"],
        "labels_en": ["beans", "beans and legumes"],
        "labels_fr": ["haricots", "légumineuses"],
        "notes": "Broad group often rich in GOS when not well tolerated.",
        "source_refs": ["monash", "japan_local"],
    },
    {
        "food_id": "cauliflower",
        "canonical": "cauliflower",
        "category": "vegetable",
        "labels_ja": ["カリフラワー", " cauli "],
        "labels_en": ["cauliflower"],
        "labels_fr": ["chou-fleur"],
        "notes": "Often moderate in FODMAPs depending on serving size.",
        "source_refs": ["monash", "japan_local"],
    },
    {
        "food_id": "mushroom",
        "canonical": "mushroom",
        "category": "vegetable",
        "labels_ja": ["きのこ", "キノコ", "mushroom"],
        "labels_en": ["mushroom"],
        "labels_fr": ["champignon"],
        "notes": "Generally lower FODMAP but can vary by species.",
        "source_refs": ["japan_local"],
    },
    {
        "food_id": "rice",
        "canonical": "rice",
        "category": "grain",
        "labels_ja": ["米", "こめ", "ライス"],
        "labels_en": ["rice"],
        "labels_fr": ["riz"],
        "notes": "Generally low FODMAP staple in many IBS patterns.",
        "source_refs": ["monash", "japan_local"],
    },
    {
        "food_id": "potato",
        "canonical": "potato",
        "category": "vegetable",
        "labels_ja": ["じゃがいも", "ジャガイモ", " potato "],
        "labels_en": ["potato"],
        "labels_fr": ["pomme de terre"],
        "notes": "Generally low FODMAP in standard servings.",
        "source_refs": ["monash", "japan_local"],
    },
    {
        "food_id": "tomato",
        "canonical": "tomato",
        "category": "vegetable",
        "labels_ja": ["トマト", " tomato "],
        "labels_en": ["tomato"],
        "labels_fr": ["tomate"],
        "notes": "Often low-FODMAP in moderate portions.",
        "source_refs": ["monash", "japan_local"],
    },
    {
        "food_id": "spinach",
        "canonical": "spinach",
        "category": "vegetable",
        "labels_ja": ["ほうれん草", "ホウレンソウ"],
        "labels_en": ["spinach"],
        "labels_fr": ["épinard"],
        "notes": "Generally low FODMAP in moderate portions.",
        "source_refs": ["monash", "japan_local"],
    },
    {
        "food_id": "banana",
        "canonical": "banana",
        "category": "fruit",
        "labels_ja": ["バナナ", " banana "],
        "labels_en": ["banana"],
        "labels_fr": ["banane"],
        "notes": "Often treated as low FODMAP depending on ripeness.",
        "source_refs": ["monash", "japan_local"],
    },
    {
        "food_id": "kiwi",
        "canonical": "kiwi",
        "category": "fruit",
        "labels_ja": ["キウイ", "きうい"],
        "labels_en": ["kiwi"],
        "labels_fr": ["kiwi"],
        "notes": "Often low FODMAP in moderate servings.",
        "source_refs": ["monash", "japan_local"],
    },
]

FODMAP_RULES: List[Dict[str, Any]] = [
    {"food_id": "apple", "fodmap_group": "fructose", "fodmap_level": "high", "is_fodmap": True, "confidence": "medium", "source": "monash"},
    {"food_id": "pear", "fodmap_group": "fructose", "fodmap_level": "moderate", "is_fodmap": True, "confidence": "medium", "source": "monash"},
    {"food_id": "watermelon", "fodmap_group": "fructose", "fodmap_level": "high", "is_fodmap": True, "confidence": "medium", "source": "monash"},
    {"food_id": "mango", "fodmap_group": "fructose", "fodmap_level": "high", "is_fodmap": True, "confidence": "medium", "source": "monash"},
    {"food_id": "garlic", "fodmap_group": "fructan", "fodmap_level": "high", "is_fodmap": True, "confidence": "high", "source": "monash"},
    {"food_id": "onion", "fodmap_group": "fructan", "fodmap_level": "high", "is_fodmap": True, "confidence": "high", "source": "monash"},
    {"food_id": "shallot", "fodmap_group": "fructan", "fodmap_level": "high", "is_fodmap": True, "confidence": "high", "source": "monash"},
    {"food_id": "leek", "fodmap_group": "fructan", "fodmap_level": "high", "is_fodmap": True, "confidence": "medium", "source": "monash"},
    {"food_id": "gobo", "fodmap_group": "none", "fodmap_level": "low", "is_fodmap": False, "confidence": "medium", "source": "curated_local"},
    {"food_id": "asparagus", "fodmap_group": "fructan", "fodmap_level": "high", "is_fodmap": True, "confidence": "medium", "source": "monash"},
    {"food_id": "wheat", "fodmap_group": "fructan", "fodmap_level": "high", "is_fodmap": True, "confidence": "high", "source": "monash"},
    {"food_id": "rye", "fodmap_group": "fructan", "fodmap_level": "high", "is_fodmap": True, "confidence": "medium", "source": "monash"},
    {"food_id": "barley", "fodmap_group": "fructan", "fodmap_level": "high", "is_fodmap": True, "confidence": "medium", "source": "monash"},
    {"food_id": "milk", "fodmap_group": "lactose", "fodmap_level": "high", "is_fodmap": True, "confidence": "high", "source": "monash"},
    {"food_id": "yogurt", "fodmap_group": "lactose", "fodmap_level": "high", "is_fodmap": True, "confidence": "high", "source": "monash"},
    {"food_id": "soft_cheese", "fodmap_group": "lactose", "fodmap_level": "moderate", "is_fodmap": True, "confidence": "medium", "source": "monash"},
    {"food_id": "chickpea", "fodmap_group": "gos", "fodmap_level": "high", "is_fodmap": True, "confidence": "high", "source": "monash"},
    {"food_id": "lentil", "fodmap_group": "gos", "fodmap_level": "high", "is_fodmap": True, "confidence": "high", "source": "monash"},
    {"food_id": "beans", "fodmap_group": "gos", "fodmap_level": "moderate", "is_fodmap": True, "confidence": "medium", "source": "monash"},
    {"food_id": "cauliflower", "fodmap_group": "fructan", "fodmap_level": "moderate", "is_fodmap": True, "confidence": "medium", "source": "monash"},
    {"food_id": "mushroom", "fodmap_group": "unknown", "fodmap_level": "unknown", "is_fodmap": False, "confidence": "low", "source": "curated_local"},
    {"food_id": "rice", "fodmap_group": "none", "fodmap_level": "low", "is_fodmap": False, "confidence": "high", "source": "monash"},
    {"food_id": "potato", "fodmap_group": "none", "fodmap_level": "low", "is_fodmap": False, "confidence": "high", "source": "monash"},
    {"food_id": "tomato", "fodmap_group": "none", "fodmap_level": "low", "is_fodmap": False, "confidence": "medium", "source": "monash"},
    {"food_id": "spinach", "fodmap_group": "none", "fodmap_level": "low", "is_fodmap": False, "confidence": "medium", "source": "monash"},
    {"food_id": "banana", "fodmap_group": "none", "fodmap_level": "low", "is_fodmap": False, "confidence": "medium", "source": "monash"},
    {"food_id": "kiwi", "fodmap_group": "none", "fodmap_level": "low", "is_fodmap": False, "confidence": "medium", "source": "monash"},
]


def build_runtime_reference() -> Dict[str, Dict[str, Any]]:
    return build_runtime_reference_map(FOODS_TABLE, FODMAP_RULES)


def write_json(path: Path, payload: Any) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def write_userscript_embed(path: Path, entries: Dict[str, Dict[str, Any]]) -> None:
    payload = {
        "schema": "fodmap_reference_v1",
        "entries": entries,
    }
    js = "globalThis.SAN_A_FODMAP_REFERENCE = " + json.dumps(payload, ensure_ascii=False, indent=2) + ";\n"
    js += "if (typeof module !== 'undefined') { module.exports = globalThis.SAN_A_FODMAP_REFERENCE; }\n"
    path.write_text(js, encoding="utf-8")


def main() -> None:
    source_manifest = {
        "generated_at": "2026-10-19",
        "project": "san-a_delivery",
        "source_references": SOURCE_MANIFEST,
    }

    foods_table = {
        "schema": "foods_table_v1",
        "entries": FOODS_TABLE,
    }
    fodmap_rules = {
        "schema": "fodmap_rules_v1",
        "entries": FODMAP_RULES,
    }
    runtime_reference = {
        "schema": "fodmap_reference_v1",
        "entries": build_runtime_reference(),
    }

    write_json(DATA_DIR / "source_manifest.json", source_manifest)
    write_json(DATA_DIR / "foods_table.json", foods_table)
    write_json(DATA_DIR / "fodmap_rules.json", fodmap_rules)
    write_json(DATA_DIR / "fodmap_reference.json", runtime_reference)
    write_userscript_embed(ROOT / "src" / "fodmap_reference_embed.js", runtime_reference["entries"])

    print(f"Generated reference files in {DATA_DIR}")
    print(f"Foods: {len(FOODS_TABLE)}")
    print(f"FODMAP rules: {len(FODMAP_RULES)}")
    print(f"Merged runtime entries: {len(runtime_reference['entries'])}")
    print(f"Userscript embed: {ROOT / 'src' / 'fodmap_reference_embed.js'}")


if __name__ == "__main__":
    main()
