import json
from pathlib import Path

import pytest

PARAMS_PATH = Path(__file__).resolve().parents[1] / "params" / "field_params.json"


@pytest.fixture
def params():
    with open(PARAMS_PATH) as f:
        return json.load(f)


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "benchmark: asserts the twin against a published field/literature number "
        "(tests/test_benchmarks.py); deselect with -m 'not benchmark'",
    )


def legacy_rev10(params: dict) -> dict:
    """The rev-10 physics switches (twin.cycle.legacy_rev10_params)."""
    from twin import cycle
    return cycle.legacy_rev10_params(params)


@pytest.fixture
def legacy_params(params):
    return legacy_rev10(params)
