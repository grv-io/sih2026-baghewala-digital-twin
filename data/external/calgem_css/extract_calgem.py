"""
extract_calgem.py
==================

Builds a Cyclic Steam Stimulation (CSS) calibration/validation benchmark for
Baghewala heavy-oil digital twin from REAL California CalGEM (formerly DOGGR)
well-level monthly steam/water INJECTION data (2018-2021) plus official
CalGEM field-level annual production/injection statistics (2021 Supervisor
Annual Report), for Kern River, Midway-Sunset, and Coalinga fields.

DATA SOURCES (see SOURCE.md for full detail, URLs, and fetch dates):
  1. Well-level monthly injection (form OG110B), statewide, 2018-2021:
     mirrored as CSV (converted from CalGEM's own SQL Server database
     backups) by Inside Climate News:
     https://github.com/InsideClimateNews/2022-09-ca-kern-oil-water
     (sql_server_csv/<year>/dbo.<year>CaliforniaOilAndGasWellMonthlyInjection.csv)
  2. Well registry (API, FieldCode/FieldName, WellTypeCode, WellStatus,
     Operator) for the same statewide WellSTAR extract, year 2021 snapshot:
     dbo.2021CaliforniaOilAndGasWells.csv (same repo).
  3. Official CalGEM 2021 Supervisor Annual Report PDF (field-level annual
     oil production, and Cyclic Steam / Steamflood / Water Disposal /
     Waterflood injection volumes by field) -- fetched via the Wayback
     Machine because www.conservation.ca.gov was unreachable from the
     execution sandbox (see SOURCE.md "Connectivity" section).

IMPORTANT / KNOWN LIMITATION (see SOURCE.md and the benchmark doc):
  CalGEM's monthly OIL PRODUCTION table (form OG110, "MonthlyProduction")
  could not be obtained (the live CalGEM site was unreachable, and no
  reachable mirror of the production table -- as opposed to the injection
  table -- was found after an extensive search). Therefore this dataset
  can NOT compute true per-cycle oil volume, SOR, peak rate, or uplift
  (those require pairing each well's steam-in months with its oil-out
  months). What IS computed, from real well-level data, per detected
  injection episode ("cycle" proxy):
    - steam volume (bbl CWE and tonnes)
    - inject-phase duration (days)
    - the calendar gap to the NEXT injection episode on the same well,
      used as a PROXY for the combined soak+produce phase length (the
      well is registered as a cyclic-steam ("SC") producer, so the gap
      between injection episodes is presumed to be when it is producing/
      soaking -- but this is not directly confirmed by an oil record).
  Field-level annual SOR (steam / oil) IS available from the official
  Annual Report (real government-published aggregate), and is reported
  in summary.json / the benchmark doc as the closest available real
  comparison for the model's SOR.

Usage:
    python extract_calgem.py
Expects, in the same directory:
    inj_all_filtered.csv     (pre-filtered statewide monthly injection rows
                               for FieldCode in {150, 340, 464}, see fetch
                               step already performed / documented in
                               SOURCE.md)
    wells_lookup_kern.csv    (well registry rows for the same 3 fields)
Writes cycles_<field>.csv and summary.json to the working directory.
"""
import json
import numpy as np
import pandas as pd

FIELD_NAMES = {
    '150': 'Coalinga',
    '340': 'Kern River',
    '464': 'Midway-Sunset',
}
BBL_TO_TONNES = 0.159  # 1 bbl cold-water-equivalent (CWE) ~= 0.159 m3 ~= 0.159 t
GAP_MONTHS_TO_SPLIT = 1  # >=1 consecutive non-injecting month breaks an episode

# ---------------------------------------------------------------------
# Official CalGEM 2021 Supervisor Annual Report field-level totals
# (hand-transcribed from the PDF tables "California Oil, Associated Gas,
# and Water Production by District and Field in 2021" and "2021 California
# Steam and Water Injection by District and Field"; see SOURCE.md for the
# exact page numbers / quoted figures).
# ---------------------------------------------------------------------
ANNUAL_REPORT_2021 = {
    'Kern River': {
        'oil_bbl': 14_948_895,
        'gas_mcf': 721_948,
        'water_produced_bbl': 240_894_036,
        'cyclic_steam_bbl': 6_545_587,
        'steamflood_bbl': 45_250_803,
        'water_disposal_bbl': 10_079_928,
        'waterflood_bbl': 0,
    },
    'Midway-Sunset': {
        'oil_bbl': 18_881_678,
        'gas_mcf': 3_223_557,
        'water_produced_bbl': 174_878_131,
        'cyclic_steam_bbl': 86_348_234,
        'steamflood_bbl': 57_210_676,
        'water_disposal_bbl': 81_584_672,
        'waterflood_bbl': 0,
    },
    'Coalinga': {
        'oil_bbl': 4_925_637,
        'gas_mcf': 493_645,
        'water_produced_bbl': 61_107_630,
        'cyclic_steam_bbl': 14_407_683,
        'steamflood_bbl': 26_172_623,
        'water_disposal_bbl': 2_937_408,
        'waterflood_bbl': 10_643_517,
    },
}

# 2017-2021 oil production trend for these fields (Figure 11, "2021 Oil
# Production from the Ten Largest Fields (MMbbl/year)", same Annual Report).
OIL_TREND_MMBBL = {
    'Kern River':     {2017: 21.9, 2018: 17.2, 2019: 17.8, 2020: 16.3, 2021: 15.0},
    'Midway-Sunset':  {2017: 22.3, 2018: 22.1, 2019: 21.4, 2020: 20.2, 2021: 18.9},
    'Coalinga':       {2017: 6.6,  2018: 6.3,  2019: 5.8,  2020: 5.5,  2021: 4.9},
}


def load_data():
    inj = pd.read_csv('inj_all_filtered.csv', dtype=str)
    wl = pd.read_csv('wells_lookup_kern.csv', dtype=str)

    # dedupe wells lookup to one row per API; prefer the row whose
    # WellTypeCode is 'SC' (cyclic steam) if the well has multiple
    # pool completions with different codes.
    wl['_pref'] = (wl['WellTypeCode'] == 'SC').astype(int)
    wl = wl.sort_values('_pref', ascending=False).drop_duplicates('API', keep='first')
    wl = wl.drop(columns='_pref')

    inj['InjectionDate'] = pd.to_datetime(inj['InjectionDate'])
    inj['SteamWaterInjected'] = pd.to_numeric(inj['SteamWaterInjected'], errors='coerce').fillna(0.0)
    inj['DaysInjecting'] = pd.to_numeric(inj['DaysInjecting'], errors='coerce').fillna(0.0)
    inj['FieldName'] = inj['FieldCode'].map(FIELD_NAMES)

    merged = inj.merge(
        wl[['API', 'WellTypeCode', 'WellStatus', 'OperatorName', 'LeaseName', 'WellNumber']],
        left_on='APINumber', right_on='API', how='left', suffixes=('', '_wl')
    )
    return merged, wl


def detect_cycles(well_df):
    """well_df: one well's monthly injection rows, sorted by date.
    Returns a list of cycle dicts."""
    well_df = well_df.sort_values('InjectionDate').reset_index(drop=True)
    injecting = well_df['SteamWaterInjected'] > 0

    cycles = []
    i = 0
    n = len(well_df)
    episodes = []  # (start_idx, end_idx) inclusive, contiguous True runs
    while i < n:
        if injecting.iloc[i]:
            j = i
            while j + 1 < n and injecting.iloc[j + 1]:
                j += 1
            episodes.append((i, j))
            i = j + 1
        else:
            i += 1

    for k, (s, e) in enumerate(episodes):
        seg = well_df.iloc[s:e + 1]
        steam_bbl = seg['SteamWaterInjected'].sum()
        inject_days = seg['DaysInjecting'].sum()
        n_estimated = (seg['ReportedOrEstimated'] == 'Estimated').sum()
        start_date = seg['InjectionDate'].iloc[0]
        end_date = seg['InjectionDate'].iloc[-1]

        if k + 1 < len(episodes):
            next_start = well_df['InjectionDate'].iloc[episodes[k + 1][0]]
            gap_days = (next_start - end_date).days
            censored = False
        else:
            gap_days = np.nan
            censored = True  # right-censored: well may still be producing

        cycles.append({
            'cycle_index': k,
            'inject_start': start_date.date().isoformat(),
            'inject_end': end_date.date().isoformat(),
            'steam_bbl_cwe': round(float(steam_bbl), 1),
            'steam_tonnes': round(float(steam_bbl) * BBL_TO_TONNES, 2),
            'inject_days': round(float(inject_days), 1),
            'inject_months': int(e - s + 1),
            'n_months_estimated_flag': int(n_estimated),
            'gap_days_to_next_inject_proxy_produce_phase': gap_days,
            'produce_phase_censored': censored,
            'oil_m3': np.nan,
            'oil_data_available': False,
            'cycle_sor_t_per_m3': np.nan,
            'peak_rate_bbl_d': np.nan,
            'pre_steam_baseline_bbl_d': np.nan,
            'uplift_x': np.nan,
        })
    return cycles


def build_cycles_table(merged, field_name):
    fdf = merged[(merged['FieldName'] == field_name) & (merged['WellTypeCode'] == 'SC')].copy()
    rows = []
    for api, g in fdf.groupby('APINumber'):
        well_meta = g.iloc[0]
        cycs = detect_cycles(g)
        for c in cycs:
            c['api'] = api
            c['field'] = field_name
            c['operator'] = well_meta.get('OperatorName')
            c['lease_name'] = well_meta.get('LeaseName')
            c['well_number'] = well_meta.get('WellNumber')
            c['well_status'] = well_meta.get('WellStatus')
            rows.append(c)
    if not rows:
        return pd.DataFrame()
    out = pd.DataFrame(rows)
    col_order = [
        'field', 'api', 'lease_name', 'well_number', 'operator', 'well_status',
        'cycle_index', 'inject_start', 'inject_end', 'inject_months', 'inject_days',
        'steam_bbl_cwe', 'steam_tonnes', 'n_months_estimated_flag',
        'gap_days_to_next_inject_proxy_produce_phase', 'produce_phase_censored',
        'oil_m3', 'oil_data_available', 'cycle_sor_t_per_m3',
        'peak_rate_bbl_d', 'pre_steam_baseline_bbl_d', 'uplift_x',
    ]
    return out[col_order]


def pctiles(s):
    s = s.dropna()
    if len(s) == 0:
        return None
    return {
        'p10': round(float(np.percentile(s, 10)), 2),
        'p50': round(float(np.percentile(s, 50)), 2),
        'p90': round(float(np.percentile(s, 90)), 2),
        'mean': round(float(s.mean()), 2),
        'n': int(len(s)),
    }


def main():
    merged, wl = load_data()

    summary = {
        'generated_from': 'CalGEM (formerly DOGGR) WellSTAR monthly injection data, 2018-2021, '
                           'mirrored by InsideClimateNews from official CalGEM SQL Server backups; '
                           'field-level annual figures from the CalGEM 2021 Supervisor Annual Report.',
        'fields': {},
        'field_level_annual_2021_official': ANNUAL_REPORT_2021,
        'oil_production_trend_mmbbl_2017_2021_official': OIL_TREND_MMBBL,
        'baghewala_model_reference_cycle': {
            'steam_tonnes_per_cycle': [1300, 1500],
            'sor_t_per_m3': 4.1,
            'peak_rate_bbl_d': 16,
            'produce_phase_months': 6,
            'uplift_x': 5.7,
        },
        'limitations': [
            'Monthly OIL PRODUCTION by well (form OG110) was not obtainable from any reachable '
            'source; only monthly STEAM/WATER INJECTION (form OG110B) was available. Per-cycle '
            'oil volume, SOR, peak rate, pre-steam baseline, and uplift could NOT be computed '
            'from well-level data as a result.',
            'The "produce phase" length reported per cycle is a PROXY: the calendar gap between '
            'the end of one injection episode and the start of the next on the same well. It is '
            'not confirmed to be an actual producing period (could include shut-in/idle time).',
            'Field-level annual SOR uses the official 2021 CalGEM Supervisor Annual Report figures '
            '(oil production and cyclic-steam+steamflood injection), the last annual report found '
            'to include the field-by-field appendix (2022/2023 reports omit it).',
            'CalGEM injection reports flagged "Estimated" (vs "Reported") lack a DaysInjecting value '
            'in ~100% of cases; inject_days for cycles containing estimated months is understated.',
        ],
    }

    for code, fname in FIELD_NAMES.items():
        cycles_df = build_cycles_table(merged, fname)
        out_path = f'cycles_{fname.lower().replace(" ", "_").replace("-", "_")}.csv'
        cycles_df.to_csv(out_path, index=False)

        n_wells = cycles_df['api'].nunique() if len(cycles_df) else 0
        n_cycles = len(cycles_df)
        closed = cycles_df[cycles_df['produce_phase_censored'] == False] if len(cycles_df) else cycles_df

        ar = ANNUAL_REPORT_2021[fname]
        field_annual_sor = round((ar['cyclic_steam_bbl'] + ar['steamflood_bbl']) / ar['oil_bbl'], 3)
        field_annual_sor_cyclic_only_over_total_oil = round(ar['cyclic_steam_bbl'] / ar['oil_bbl'], 3)

        summary['fields'][fname] = {
            'csv_file': out_path,
            'n_sc_wells_with_injection_data': n_wells,
            'n_cycles_detected': n_cycles,
            'steam_tonnes_per_cycle': pctiles(cycles_df['steam_tonnes']) if n_cycles else None,
            'inject_days_per_cycle': pctiles(cycles_df['inject_days']) if n_cycles else None,
            'produce_phase_gap_days_proxy_noncensored': pctiles(
                closed['gap_days_to_next_inject_proxy_produce_phase']) if len(closed) else None,
            'cycles_by_year': (
                cycles_df['inject_start'].str.slice(0, 4).value_counts().sort_index().to_dict()
                if n_cycles else {}
            ),
            'field_level_annual_sor_2021_total_steam_over_oil': field_annual_sor,
            'field_level_annual_ratio_2021_cyclicsteam_over_oil': field_annual_sor_cyclic_only_over_total_oil,
        }
        print(fname, '-> wells:', n_wells, 'cycles:', n_cycles, 'csv:', out_path)

    with open('summary.json', 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    print('Wrote summary.json')


if __name__ == '__main__':
    main()
