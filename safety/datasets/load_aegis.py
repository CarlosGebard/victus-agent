from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def main() -> int:
    parser = argparse.ArgumentParser(description="Load Aegis 2.0 from HuggingFace into JSONL.")
    parser.add_argument("--split", default="train")
    parser.add_argument("--output", default="safety/datasets/aegis_2_0.raw.jsonl")
    args = parser.parse_args()

    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise SystemExit("Install the optional 'datasets' package to load Aegis 2.0.") from exc

    dataset = load_dataset("nvidia/Aegis-AI-Content-Safety-Dataset-2.0", split=args.split)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as file:
        for row in dataset:
            file.write(json.dumps(dict(row), ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
