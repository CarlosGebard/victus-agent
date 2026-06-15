import json

from ops.scripts import contracts


def test_contracts_list_prints_config(capsys) -> None:
    assert contracts.main(["list"]) == 0

    output = capsys.readouterr().out
    assert "source=https://github.com/CarlosGebard/victus-docs.git" in output
    assert "subscription=fundamental" in output


def test_contracts_validate_checks_lockfile(tmp_path, monkeypatch, capsys) -> None:
    contract = tmp_path / "contract.md"
    contract.write_text("# Contract\n", encoding="utf-8")
    lockfile = tmp_path / "contracts.lock.json"
    lockfile.write_text(
        json.dumps(
            {
                "contracts": [
                    {
                        "contract_id": "test.contract",
                        "version": "v1",
                        "path": str(contract),
                        "sha256": contracts._sha256(contract),
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(contracts, "LOCKFILE_PATH", lockfile)

    assert contracts.main(["validate"]) == 0
    assert "validated 1 contracts" in capsys.readouterr().out
