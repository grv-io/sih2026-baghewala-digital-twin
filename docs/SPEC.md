# Baghewala Digital Twin — Shared Build Spec (SIH26120)

All agents/modules MUST follow this contract. Units are SI unless stated.

## Project layout
```
sih-baghewala/
├── requirements.txt         numpy, scipy, pandas, scikit-learn, xgboost, scikit-optimize, fastapi, uvicorn, pytest
├── params/field_params.json (single source of truth for reservoir/fluid/pump parameters)
├── twin/                    Python package
│   ├── __init__.py
│   ├── thermal.py           Marx-Langenheim steam zone + cooldown
│   ├── viscosity.py         Andrade/ASTM-type mu(T)
│   ├── ipr.py               Vogel inflow performance
│   ├── srp.py               sucker-rod pump load, efficiency, rod-floating index
│   ├── cycle.py             CSS cycle simulator (orchestrates the above)
│   └── generate_data.py     synthetic dataset generator → data/synthetic_cycles.csv
├── data/                    generated CSVs
├── ml/
│   ├── train.py             trains models → ml/models/*.joblib
│   ├── optimize.py          Bayesian optimizer over CSS+SRP params
│   └── models/
├── api/main.py              FastAPI app
├── dashboard/               4-page dashboard (Plotly via cdnjs), talks to API
├── tests/                   pytest sanity tests for twin/
├── ppt/                     SIH pitch deck (final/, archive/, build scripts)
└── docs/                    this spec, project log, research, reviews, study material
    ├── SPEC.md              (this file)
    └── research/            markdown notes + sources (research agent output)
```

## params/field_params.json (schema + defaults; research agent refines values, others consume)
```json
{
  "reservoir": {"T_initial_C": 47.0, "P_initial_kPa": 6000, "depth_m": 500,
    "thickness_m": 12.0, "porosity": 0.28, "k_thermal_W_mK": 2.5,
    "rock_heat_capacity_Jm3K": 2.3e6},
  "fluid": {"api_gravity": 18.0, "mu_ref_cP": 2000.0, "T_ref_C": 47.0,
    "andrade_A": null, "andrade_B_K": null, "bubble_point_kPa": 3000},
  "steam": {"quality": 0.75, "T_injection_C": 250.0,
    "latent_heat_Jkg": 1.7e6, "injection_rate_tpd": 100},
  "srp": {"stroke_m": 3.0, "spm_range": [4, 12], "rod_length_m": 500,
    "plunger_d_m": 0.057, "rod_mass_kgm": 3.8},
  "css": {"steam_volume_t_range": [500, 3000], "soak_days_range": [3, 15],
    "cutoff_rate_m3d_range": [1, 8]}
}
```
`null` = to be filled by research agent (with source cited in docs/research/ notes). Consumers must read this file, never hardcode.

## Module contracts (function signatures, exact names)
- `thermal.steam_zone_temperature(t_days, params) -> (T_avg_C, heated_radius_m)` — Marx-Langenheim heated-zone growth during injection; exponential-decay cooldown after injection stops (document the simplification).
- `viscosity.mu_cP(T_C, params) -> float` — Andrade form `mu = A * exp(B/T_K)`; if andrade_A/B null, fit them from (mu_ref_cP, T_ref_C) plus one high-T anchor (e.g. 50 cP at 150 °C, note as assumption).
- `ipr.oil_rate_m3d(P_res_kPa, P_wf_kPa, mu_cP, params) -> float` — Vogel curve scaled by a mobility factor (mu_ref/mu).
- `srp.pump_state(spm, stroke_m, mu_cP, rate_m3d, params) -> dict` with keys: `prod_rate_m3d, peak_rod_load_kN, energy_kWh_d, floating_index` (0–1; >0.6 = floating risk; base it on viscous downstroke drag vs rod weight — document formula).
- `cycle.simulate_css_cycle(steam_t, soak_days, cutoff_m3d, spm, params, dt_days=1.0) -> pandas.DataFrame` — columns exactly: `day, phase, T_res_C, mu_cP, P_res_kPa, oil_m3d, steam_t_cum, energy_kWh, rod_load_kN, floating_index`. Phases: `inject|soak|produce`. Cycle ends when oil rate < cutoff. Also `cycle.summary(df) -> dict`: `oil_total_m3, SOR_t_per_m3, energy_per_m3_kWh, days_total, max_floating_index, failures_expected`.

## Synthetic data
`twin/generate_data.py` → `data/synthetic_cycles.csv`: one row per simulated cycle, columns = inputs (steam_t, soak_days, cutoff_m3d, spm) + all summary() outputs. ≥3000 rows, Latin-hypercube or random sampling over css/srp ranges, seed=42.

## ML contracts
- `ml/train.py`: reads synthetic_cycles.csv → saves `sor_model.joblib` (XGBoost regressor for SOR), `float_model.joblib` (classifier: max_floating_index>0.6), plus `metrics.json` (R², AUC on 20% holdout).
- `ml/optimize.py`: `best_settings(params) -> dict` — Bayesian (skopt gp_minimize) over the 4 inputs minimizing predicted SOR subject to floating probability < 0.3; returns inputs + predicted SOR + baseline SOR (midpoint settings) + % improvement.

## API (FastAPI, port 8000, CORS *)
- `GET /simulate?steam_t=&soak_days=&cutoff=&spm=` → `{summary: {...}, series: [rows of the cycle DataFrame]}`
- `GET /optimize` → best_settings() result
- `GET /params` → field_params.json contents

## Dashboard (single index.html, no build step)
Load Plotly ONLY from https://cdnjs.cloudflare.com. Panels: (1) cycle time-series (T, viscosity, oil rate vs day), (2) pump card approximation (rod load vs stroke position sketch from srp outputs), (3) floating-risk gauge + alert banner, (4) baseline-vs-optimized SOR bar comparison (calls /optimize). API base `http://localhost:8000`, editable constant at top. Amber/dark professional theme.

## Conventions
- Python 3.12, type hints, docstrings citing the source model (e.g. "Marx & Langenheim 1959").
- Every physical assumption gets an inline `# ASSUMPTION:` comment.
- Tests: monotonic checks (viscosity falls as T rises; SOR rises as steam_t rises past optimum; floating_index rises with mu and spm).
- No network calls in twin/ or ml/. Deterministic with seed 42.
