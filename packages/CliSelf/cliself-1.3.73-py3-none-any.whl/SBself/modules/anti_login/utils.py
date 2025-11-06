from typing import Any, Dict
from pathlib import Path
import json

def load_json(path: str, default: Dict[str, Any]) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return default.copy()
    try:
        with p.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default.copy()

def save_json(path: str, data: Dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
