"""Shared FastAPI dependencies: loading params/field_params.json, and making
sure `twin/` and `ml/` (top-level packages next to `api/`, not inside it)
are importable regardless of the process cwd."""
from __future__ import annotations

import json
import sys

from .settings import ROOT, get_settings

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def load_params() -> dict:
    """Load params/field_params.json fresh on every call (it's small, and
    keeping it live means edits during a hackathon demo take effect without
    an API restart)."""
    settings = get_settings()
    with open(settings.params_path, "r", encoding="utf-8") as f:
        return json.load(f)
