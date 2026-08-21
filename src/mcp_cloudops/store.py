from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).parent / "data"


def load_json(name: str) -> list[dict[str, Any]]:
    with (DATA_DIR / name).open("r", encoding="utf-8") as file:
        return json.load(file)
