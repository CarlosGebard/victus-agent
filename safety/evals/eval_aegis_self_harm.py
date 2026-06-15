from __future__ import annotations

import argparse
import json
from pathlib import Path

from safety.engine.safety_precheck import SafetyPrecheck
from safety.engine.schemas import SafetyPrecheckInput


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate self-harm recall/false positives on Aegis JSONL.")
    parser.add_argument("--input", default="safety/datasets/aegis_2_0.normalized.jsonl")
    args = parser.parse_args()

    safety = SafetyPrecheck()
    unsafe_total = unsafe_detected = safe_total = safe_flagged = 0
    with Path(args.input).open("r", encoding="utf-8") as file:
        for line in file:
            row = json.loads(line)
            if row.get("category") not in {"self_harm", "none"}:
                continue
            result = safety.check(
                SafetyPrecheckInput(
                    original_text=row.get("text", ""),
                    working_text=row.get("text", ""),
                )
            )
            detected = "self_harm" in result.categories
            if row.get("category") == "self_harm" and row.get("unsafe"):
                unsafe_total += 1
                unsafe_detected += int(detected)
            elif row.get("category") == "none" and not row.get("unsafe"):
                safe_total += 1
                safe_flagged += int(detected)

    recall = unsafe_detected / unsafe_total if unsafe_total else 0
    false_positive_rate = safe_flagged / safe_total if safe_total else 0
    print(
        json.dumps(
            {
                "unsafe_self_harm_total": unsafe_total,
                "unsafe_self_harm_detected": unsafe_detected,
                "recall": recall,
                "safe_total": safe_total,
                "safe_flagged": safe_flagged,
                "false_positive_rate": false_positive_rate,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
