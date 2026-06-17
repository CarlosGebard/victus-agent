from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class LocalLlamaGuardResult:
    text: str
    prompt: str
    raw: dict[str, Any] = field(default_factory=dict)


class LocalLlamaGuardClient:
    def __init__(self, model_name: str, *, device_map: str = "auto") -> None:
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise RuntimeError(
                "Local Llama Guard requires the optional safety-local dependencies. "
                "Install them with: uv sync --extra safety-local"
            ) from exc

        self.model_name = model_name
        self._torch = torch
        try:
            self._tokenizer = AutoTokenizer.from_pretrained(model_name)
            self._model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map=device_map,
                torch_dtype="auto",
            )
        except OSError as exc:
            raise RuntimeError(
                "Could not load local Llama Guard model. If using "
                "meta-llama/Llama-Guard-3-1B, approve access on Hugging Face and run "
                "`huggingface-cli login`, or set `safety.model` to a local model directory."
            ) from exc

    def complete(self, prompt: str, *, max_new_tokens: int = 64) -> LocalLlamaGuardResult:
        inputs = self._tokenizer(prompt, return_tensors="pt")
        model_device = getattr(self._model, "device", None)
        if model_device is not None:
            inputs = {key: value.to(model_device) for key, value in inputs.items()}

        with self._torch.no_grad():
            output_ids = self._model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=self._tokenizer.eos_token_id,
            )

        generated_ids = output_ids[0][inputs["input_ids"].shape[-1] :]
        text = self._tokenizer.decode(generated_ids, skip_special_tokens=True).strip()
        return LocalLlamaGuardResult(
            text=text,
            prompt=prompt,
            raw={"model": self.model_name, "max_new_tokens": max_new_tokens},
        )
