from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from safety.engine.schemas import SafetyRule

DEFAULT_RULE_ROOT = Path("safety/rules")


def load_rules(root: str | Path = DEFAULT_RULE_ROOT) -> list[SafetyRule]:
    root_path = Path(root)
    rules: list[SafetyRule] = []
    for path in sorted(root_path.glob("**/*.yaml")):
        payload = _load_yaml(path)
        items = payload.get("rules", [])
        if not isinstance(items, list):
            raise ValueError(f"rules must be a list: {path}")
        rules.extend(_rule_from_mapping(item, path) for item in items)
    return [rule for rule in rules if rule.enabled]


def load_yaml_mapping(path: str | Path) -> dict[str, Any]:
    return _load_yaml(Path(path))


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    if not isinstance(data, dict):
        raise ValueError(f"YAML must contain a mapping: {path}")
    return data


def _rule_from_mapping(item: object, path: Path) -> SafetyRule:
    if not isinstance(item, dict):
        raise ValueError(f"rule must be a mapping: {path}")
    match = item.get("match")
    if not isinstance(match, dict):
        raise ValueError(f"rule.match must be a mapping: {path}")
    return SafetyRule(
        id=_required_str(item, "id", path),
        category=_required_str(item, "category", path),  # type: ignore[arg-type]
        severity=_required_str(item, "severity", path),  # type: ignore[arg-type]
        priority=int(item.get("priority", 0)),
        reason_code=_required_str(item, "reason_code", path),
        match=match,
        enabled=bool(item.get("enabled", True)),
        negative=bool(item.get("negative", False)),
    )


def _required_str(item: dict[str, Any], key: str, path: Path) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"rule.{key} must be a non-empty string: {path}")
    return value
