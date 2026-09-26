"""Validation of the measured-dynamometer-card fault classifier
(ml/dyno_classifier.py) -- a RandomForestClassifier trained on SYNTHETIC
cards swept from twin.dyno.compute_cards(), never on a real measured card
(see the module docstring's domain-shift caveat).

(a) training is deterministic (seed 42) and hits >= 0.90 hold-out accuracy
(b) each of the 8 baked cards (ml/models/dyno_cards.json) is classified as
    its own physics-derived card_type
(c) unit auto-detection (in/klbf vs m/kN) recovers the same prediction
(d) malformed input raises a clean ValueError
(e) the API route (POST /api/dyno/classify, GET /api/dyno/classify/demo)
    returns 200 with the documented keys
"""
from __future__ import annotations

import json

import numpy as np
import pytest

from ml import dyno_classifier as dc


@pytest.fixture(scope="module")
def module_params():
    """The conftest.py `params` fixture is function-scoped; this module needs
    a module-scoped equivalent to build the (module-scoped) `trained` model
    once instead of once per test."""
    with open(dc.DEFAULT_PARAMS_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def trained(module_params, tmp_path_factory):
    """Train once for the whole module (full scale, n_samples=3200, seed 42,
    ~1-2 min) -- every other test below consumes this SAME model/metrics
    rather than retraining, so there is exactly one source of truth for the
    'accuracy >= 0.90' and 'baked cards match' checks."""
    import joblib

    # Use tmp_path for training to avoid writing to tracked files
    tmp_dir = tmp_path_factory.mktemp("dyno_train")
    tmp_model = tmp_dir / "dyno_clf.joblib"
    tmp_metrics = tmp_dir / "dyno_clf_metrics.json"

    metrics = dc.train(module_params, n_samples=3200, seed=dc.SEED,
                        out_model=tmp_model, out_metrics=tmp_metrics)

    # Load the trained model into the cache so classify_card() can use it
    bundle = joblib.load(tmp_model)
    dc._MODEL_CACHE = bundle

    return metrics


@pytest.fixture(scope="module")
def baked_cards():
    with open(dc.BAKED_CARDS_PATH) as f:
        return json.load(f)


# --------------------------------------------------------------------------
# (a) training determinism + accuracy
# --------------------------------------------------------------------------
def test_a_training_is_deterministic(params, tmp_path):
    # Independent, throwaway paths -- must NOT touch dc.MODEL_PATH/METRICS_PATH
    # (the shared model the rest of this module's tests rely on via `trained`).
    m1 = dc.train(params, n_samples=400, seed=42,
                   out_model=tmp_path / "m1.joblib", out_metrics=tmp_path / "m1.json")
    m2 = dc.train(params, n_samples=400, seed=42,
                   out_model=tmp_path / "m2.joblib", out_metrics=tmp_path / "m2.json")
    assert m1["accuracy"] == pytest.approx(m2["accuracy"])
    assert m1["confusion_matrix"] == m2["confusion_matrix"]
    assert m1["generation"]["class_counts"] == m2["generation"]["class_counts"]


def test_a_accuracy_at_full_scale(trained):
    metrics = trained
    assert metrics["accuracy"] >= 0.90
    assert set(metrics["classes"]) == set(dc.CARD_TYPES)
    for c in metrics["classes"]:
        assert metrics["per_class_f1"][c] > 0.5, f"per-class F1 too low for {c}"


# --------------------------------------------------------------------------
# (b) baked cards classified as their own label
# --------------------------------------------------------------------------
@pytest.mark.parametrize("scenario", ["baseline", "recommendation"])
def test_b_baked_cards_classified_as_own_label(trained, baked_cards, scenario):
    rows = dc.classify_baked_demo(scenario)
    assert len(rows) == 4
    misses = [r for r in rows if r["predicted_card_type"] != r["true_card_type"]]
    assert not misses, f"mispredicted: {misses}"


def test_b_all_8_baked_cards_direct(trained, baked_cards):
    n_ok = 0
    for scenario in ("baseline", "recommendation"):
        for c in baked_cards["scenarios"][scenario]["cards"]:
            result = dc.classify_card(c["surface"]["position_m"], c["surface"]["load_kN"], units="m,kN")
            n_ok += int(result["card_type"] == c["card_type"])
    assert n_ok == 8


# --------------------------------------------------------------------------
# (c) unit auto-detection
# --------------------------------------------------------------------------
def test_c_unit_autodetect_in_klbf_matches_m_kn(trained, baked_cards):
    c = baked_cards["scenarios"]["baseline"]["cards"][0]
    pos_m = np.asarray(c["surface"]["position_m"])
    load_kN = np.asarray(c["surface"]["load_kN"])

    result_si = dc.classify_card(pos_m, load_kN, units="m,kN")

    pos_in = pos_m / dc.M_PER_IN
    load_klbf = load_kN / dc.KN_PER_KLBF
    result_imperial = dc.classify_card(pos_in, load_klbf, units=None)  # auto-detect

    assert result_imperial["card_type"] == result_si["card_type"]
    assert result_imperial["quality_flags"]["position_unit_used"] == "in"
    assert result_imperial["quality_flags"]["load_unit_used"] == "klbf"
    assert result_imperial["quality_flags"]["unit_guess"] is True
    assert result_si["quality_flags"]["unit_guess"] is False
    assert result_imperial["peak_kN"] == pytest.approx(result_si["peak_kN"], rel=0.01)


def test_c_unit_header_detection_via_parse_card_table():
    text = "position_in,load_klbf\n0.0,10.0\n10.0,20.0\n20.0,15.0\n10.0,5.0\n0.0,10.0\n5.0,12.0"
    position, load, units = dc.parse_card_table(text)
    assert units == {"position": "in", "load": "klbf"}
    assert len(position) == 6


def test_c_headerless_pasted_table():
    text = "0.0 10.0\n0.5 25.0\n1.0 40.0\n1.5 30.0\n2.0 5.0\n1.0 8.0\n0.0 10.0"
    position, load, units = dc.parse_card_table(text)
    assert units == {"position": None, "load": None}
    assert len(position) == 7 and len(load) == 7


# --------------------------------------------------------------------------
# (d) malformed input
# --------------------------------------------------------------------------
def test_d_mismatched_lengths_raises(trained):
    with pytest.raises(ValueError, match="same length"):
        dc.classify_card([1, 2, 3], [1, 2])


def test_d_too_few_points_raises(trained):
    with pytest.raises(ValueError, match="at least"):
        dc.classify_card([0, 1, 2], [0, 1, 2])


def test_d_nan_raises(trained):
    with pytest.raises(ValueError, match="NaN|infinite"):
        dc.classify_card([0, 1, 2, 3, float("nan"), 5], [1, 2, 3, 4, 5, 6])


def test_d_zero_range_raises(trained):
    with pytest.raises(ValueError, match="zero range"):
        dc.classify_card([1, 1, 1, 1, 1, 1], [1, 2, 3, 4, 5, 6])
    with pytest.raises(ValueError, match="zero range"):
        dc.classify_card([1, 2, 3, 4, 5, 6], [1, 1, 1, 1, 1, 1])


def test_d_empty_csv_text_raises():
    with pytest.raises(ValueError):
        dc.parse_card_table("")


def test_d_short_csv_raises():
    with pytest.raises(ValueError, match="at least"):
        dc.parse_card_table("position_m,load_kN\n0.0,10.0\n1.0,20.0")


# --------------------------------------------------------------------------
# (e) API route
# --------------------------------------------------------------------------
@pytest.fixture(scope="module")
def client(trained, tmp_path_factory):
    import os

    db_path = tmp_path_factory.mktemp("api_dyno_clf") / "test_twin.db"
    os.environ.setdefault("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")

    from fastapi.testclient import TestClient

    import api.main as main_module

    with TestClient(main_module.app) as c:
        yield c


def test_e_api_classify_json(client, baked_cards):
    c = baked_cards["scenarios"]["baseline"]["cards"][0]
    r = client.post("/api/dyno/classify", json={
        "position": c["surface"]["position_m"], "load": c["surface"]["load_kN"], "units": "m,kN",
    })
    assert r.status_code == 200
    body = r.json()
    for key in ("card_type", "probabilities", "fillage_est", "peak_kN", "min_kN",
                "sentence_en", "sentence_hi", "quality_flags", "model_caveat"):
        assert key in body
    assert body["card_type"] == c["card_type"]


def test_e_api_classify_multipart_csv(client, baked_cards):
    c = baked_cards["scenarios"]["baseline"]["cards"][1]
    csv_text = "position_m,load_kN\n" + "\n".join(
        f"{p},{l}" for p, l in zip(c["surface"]["position_m"], c["surface"]["load_kN"])
    )
    r = client.post("/api/dyno/classify", files={"file": ("card.csv", csv_text, "text/csv")})
    assert r.status_code == 200
    assert r.json()["card_type"] == c["card_type"]


def test_e_api_classify_malformed_returns_400(client):
    r = client.post("/api/dyno/classify", json={"position": [1, 2], "load": [1, 2]})
    assert r.status_code == 400
    assert "error" in r.json()


def test_e_api_classify_demo(client):
    r = client.get("/api/dyno/classify/demo")
    assert r.status_code == 200
    body = r.json()
    assert body["scenario"] == "baseline"
    assert len(body["cards"]) == 4
    for row in body["cards"]:
        assert row["predicted_card_type"] == row["true_card_type"]
