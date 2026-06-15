from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CENTRAL_REPO_URL = "https://github.com/CarlosGebard/victus-docs.git"
REGISTRY_PATH = Path("contracts/registry.json")
DESTINATION_DIR = Path("docs/contracts/fundamental")
LOCKFILE_PATH = DESTINATION_DIR / "contracts.lock.json"
SUBSCRIPTIONS = ("fundamental",)


@dataclass(frozen=True)
class ContractEntry:
    contract_id: str
    source_path: Path
    destination_path: Path
    version: str
    checksum: str | None = None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sync fundamental contracts from victus-docs.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("list", help="List configured contract subscriptions.")
    subparsers.add_parser("sync", help="Sync subscribed contracts from the central docs repo.")
    subparsers.add_parser("validate", help="Validate imported contracts against the lockfile.")

    args = parser.parse_args(argv)
    if args.command == "list":
        return list_contracts()
    if args.command == "sync":
        return sync_contracts()
    if args.command == "validate":
        return validate_contracts()
    parser.error(f"unknown command: {args.command}")
    return 2


def list_contracts() -> int:
    print(f"source={CENTRAL_REPO_URL}")
    print(f"registry={REGISTRY_PATH}")
    print(f"destination={DESTINATION_DIR}")
    for subscription in SUBSCRIPTIONS:
        print(f"subscription={subscription}")
    return 0


def sync_contracts() -> int:
    with tempfile.TemporaryDirectory(prefix="victus-contracts-") as tmp:
        checkout = Path(tmp) / "victus-docs"
        result = subprocess.run(
            ["git", "clone", "--depth", "1", CENTRAL_REPO_URL, str(checkout)],
            check=False,
        )
        if result.returncode != 0:
            return result.returncode

        registry = _load_registry(checkout / REGISTRY_PATH)
        entries = _select_entries(registry)
        DESTINATION_DIR.mkdir(parents=True, exist_ok=True)
        _clear_synced_markdown(DESTINATION_DIR)

        locked: list[dict[str, str]] = []
        for entry in entries:
            source = checkout / entry.source_path
            destination = DESTINATION_DIR / entry.destination_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            locked.append(
                {
                    "contract_id": entry.contract_id,
                    "version": entry.version,
                    "path": str(destination),
                    "sha256": _sha256(destination),
                }
            )

    _write_lockfile(locked)
    print(f"synced {len(locked)} contracts")
    return 0


def validate_contracts() -> int:
    if not LOCKFILE_PATH.exists():
        print(f"missing lockfile: {LOCKFILE_PATH}", file=sys.stderr)
        return 1

    payload = json.loads(LOCKFILE_PATH.read_text(encoding="utf-8"))
    contracts = payload.get("contracts", [])
    if not isinstance(contracts, list):
        print("invalid lockfile: contracts must be a list", file=sys.stderr)
        return 1

    errors: list[str] = []
    for item in contracts:
        path = Path(str(item.get("path", "")))
        expected = item.get("sha256")
        if not path.exists():
            errors.append(f"missing contract file: {path}")
            continue
        actual = _sha256(path)
        if actual != expected:
            errors.append(f"checksum mismatch: {path}")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print(f"validated {len(contracts)} contracts")
    return 0


def _load_registry(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"missing registry: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit("registry must be a JSON object")
    return payload


def _select_entries(registry: dict[str, Any]) -> list[ContractEntry]:
    raw_contracts = registry.get("contracts", [])
    if not isinstance(raw_contracts, list):
        raise SystemExit("registry contracts must be a list")

    entries: list[ContractEntry] = []
    for item in raw_contracts:
        if not isinstance(item, dict):
            raise SystemExit("registry contract entries must be objects")
        tags = item.get("tags", [])
        if not set(SUBSCRIPTIONS).intersection(tags):
            continue
        contract_id = _required_str(item, "contract_id")
        source_path = Path(_required_str(item, "path"))
        version = _required_str(item, "version")
        destination_name = item.get("destination") or source_path.name
        entries.append(
            ContractEntry(
                contract_id=contract_id,
                source_path=source_path,
                destination_path=Path(str(destination_name)),
                version=version,
                checksum=item.get("sha256"),
            )
        )
    return entries


def _required_str(item: dict[str, Any], key: str) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value:
        raise SystemExit(f"registry entry missing string field: {key}")
    return value


def _clear_synced_markdown(path: Path) -> None:
    for markdown in path.glob("**/*.md"):
        markdown.unlink()


def _write_lockfile(contracts: list[dict[str, str]]) -> None:
    payload = {
        "source": CENTRAL_REPO_URL,
        "registry": str(REGISTRY_PATH),
        "subscriptions": list(SUBSCRIPTIONS),
        "contracts": sorted(contracts, key=lambda item: item["contract_id"]),
    }
    LOCKFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOCKFILE_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
