from pathlib import Path

from application.config import load_runtime_config


def test_load_runtime_config_reads_llm_settings(tmp_path: Path) -> None:
    config_path = tmp_path / "runtime.yml"
    config_path.write_text(
        "llm:\n  provider: litellm\n  model: litellm_proxy/test-model\n",
        encoding="utf-8",
    )

    config = load_runtime_config(config_path)

    assert config.llm.provider == "litellm"
    assert config.llm.model == "litellm_proxy/test-model"
    assert config.safety.model == "meta-llama/Llama-Guard-3-1B"


def test_load_runtime_config_reads_safety_model(tmp_path: Path) -> None:
    config_path = tmp_path / "runtime.yml"
    config_path.write_text(
        (
            "llm:\n"
            "  provider: litellm\n"
            "  model: litellm_proxy/test-model\n"
            "safety:\n"
            "  model: litellm_proxy/llama-guard-test\n"
        ),
        encoding="utf-8",
    )

    config = load_runtime_config(config_path)

    assert config.safety.model == "litellm_proxy/llama-guard-test"
