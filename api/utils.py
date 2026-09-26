"""Small shared helpers used by routers and jobs. No physics/ML logic here."""
from __future__ import annotations

from typing import Any

import numpy as np


def to_native(obj: Any) -> Any:
    """Recursively convert numpy scalars/arrays (which pandas/xgboost/skopt
    tend to hand back) into plain Python types so they serialize cleanly
    with the stdlib `json` module (numpy types survive `json.dumps` only via
    a custom encoder, and round-trip wrong with `default=str`)."""
    if isinstance(obj, dict):
        return {k: to_native(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_native(v) for v in obj]
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj
