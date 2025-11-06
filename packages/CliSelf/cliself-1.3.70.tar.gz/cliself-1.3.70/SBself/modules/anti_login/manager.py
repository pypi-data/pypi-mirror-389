from typing import Any, Dict, Optional, List 
from .utils import load_json, save_json
from ...config import AllConfig
_cfg = AllConfig.get("anti_login") 
# --- getters/setters ---
def is_enabled() -> bool:
    return bool(_cfg.get("anti_login", False))

def enable():
    _cfg["anti_login"] = True

def disable():
    _cfg["anti_login"] = False

def get_target():
    return _cfg.get("target_sender")

def set_target(target: Any):
    if isinstance(target, int):
        _cfg["target_sender"] = target
    else:
        s = str(target)
        if s.startswith("@"):
            s = s[1:]
        _cfg["target_sender"] = s