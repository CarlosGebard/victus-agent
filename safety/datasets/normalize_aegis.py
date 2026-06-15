from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize Aegis 2.0 JSONL for Victus evals.")
    parser.add_argument("--input", default="safety/datasets/aegis_2_0.raw.jsonl")
    parser.add_argument("--output", default="safety/datasets/aegis_2_0.normalized.jsonl")
    parser.add_argument("--source", default="safety/data_sources/aegis_2_0.yaml")
    args = parser.parse_args()

    mappings = _load_mappings(Path(args.source))
    with Path(args.input).open("r", encoding="utf-8") as source, Path(args.output).open(
        "w", encoding="utf-8"
    ) as target:
        for line in source:
            raw = json.loads(line)
            normalized = normalize_row(raw, mappings)
            if normalized:
                target.write(json.dumps(normalized, ensure_ascii=False) + "\n")
    return 0


def normalize_row(row: dict[str, Any], mappings: dict[str, str]) -> dict[str, Any] | None:
    text = _first_text(row, "prompt", "user", "instruction", "input", "response")
    if not text:
        return None

    source_category = _first_text(row, "violated_category", "category", "taxonomy", "label")
    category = mappings.get(source_category, "none")
    unsafe = category == "self_harm" or bool(row.get("unsafe") is True)
    return {
        "source": "aegis_2_0",
        "text": text,
        "category": category,
        "unsafe": unsafe,
        "source_category": source_category,
    }


def _load_mappings(path: Path) -> dict[str, str]:
    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    return dict(data.get("category_mappings", {}))


def _first_text(row: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


if __name__ == "__main__":
    raise SystemExit(main())
