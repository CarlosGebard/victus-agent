import json
from typing import Any


def render_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))
