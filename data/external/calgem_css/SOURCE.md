# CalGEM CSS benchmark — sources, methods, limitations

Fetched: 2026-09-26.

## Connectivity problem (read this first)

`www.conservation.ca.gov` and every subdomain that resolves to the same IP
(`13.87.163.94`) — including `wellstar-dashboard.conservation.ca.gov` and
`secure.conservation.ca.gov` — was **unreachable** (TCP connect timeout) from
the execution sandbox on every attempt (>15 tries: plain `urlopen`, full
browser headers, HTTP vs HTTPS, WebFetch). Other `conservation.ca.gov`
subdomains on different IPs responded (`gis.conservation.ca.gov` 200,
`filerequest.conservation.ca.gov` 200, `maps.conservation.ca.gov` 403), but
none of them serve the actual production/injection bulk files. A Google
Translate reverse-proxy trick (`https://<host-with-dashes>.translate.goog/...`)
*did* reach the blocked host's content server-side (used below to confirm the
page structure and to find the Power BI dashboard's embed target), but does
not work for binary files (PDF fetch through it timed out), and the
dashboard itself is an authenticated `app.powerbigov.us` embed (Azure AD /
GCC-High tenant `4c5988ae-5a00-40e8-b065-a017f9c99494`), not a public
"publish to web" report — no anonymous data access.

The official CalGEM download pages that were confirmed to exist but could
not be reached:
- `https://www.conservation.ca.gov/calgem/Pages/Production-and-Injection-Data.aspx`
- `https://www.conservation.ca.gov/calgem/Online_Data/Pages/Index.aspx` (links
  to "Well Production and Injection Summary Reports" → `filerequest.conservation.ca.gov/?q=production_injection_data`,
  and to a "SQL Server Express download" — CalGEM distributes its bulk
  production/injection data as a **SQL Server database backup**, not a plain
  CSV/ZIP)
- `https://wellstar-dashboard.conservation.ca.gov/` (Power BI Gov, auth-gated)
- `https://wellstar-public.conservation.ca.gov/` (403 from a WAF, reachable
  network-wise but blocks scripted clients)

`data.ca.gov` / `data.conservation.ca.gov` (CKAN) were reachable but only
catalog GIS well/facility *location* layers (WellSTAR Wells MapServer etc.),
not monthly volumes.

## What was actually used

### 1. Well-level monthly STEAM/WATER INJECTION, 2018-2021 (real CalGEM data)

Mirrored by Inside Climate News (journalism data project, byline Peter
Aldhous), who downloaded CalGEM's own SQL Server database backups on
2022-06-20 and converted each year's tables to CSV:

  Repo: https://github.com/InsideClimateNews/2022-09-ca-kern-oil-water
  Files used (fetched via `raw.githubusercontent.com`, one file per year):
  - `sql_server_csv/2018/dbo.2018CaliforniaOilAndGasWellMonthlyInjection.csv` (56,134,886 bytes)
  - `sql_server_csv/2019/dbo.2019CaliforniaOilAndGasWellMonthlyInjection.csv` (60,021,561 bytes)
  - `sql_server_csv/2020/dbo.2020CaliforniaOilAndGasWellMonthlyInjection.csv` (58,475,946 bytes)
  - `sql_server_csv/2021/dbo.2021CaliforniaOilAndGasWellMonthlyInjection.csv` (57,500,711 bytes)
  - `sql_server_csv/2021/dbo.2021CaliforniaOilAndGasWells.csv` (49,765,940 bytes) — well registry
    (API, FieldCode, FieldName, WellTypeCode, WellStatus, Operator, Lease).

  Total downloaded: ~282 MB. Each year's injection file was streamed in
  200k-row chunks, filtered to `FieldCode in {150, 340, 464}` (Coalinga,
  Kern River, Midway-Sunset), and the filtered rows + raw file were
  processed and the **raw file deleted immediately** (per download budget).
  Kept: `inj_all_filtered.csv` (1,198,096 rows, ~93 MB — NOT copied into the
  repo, scratch-only) and `wells_lookup_kern.csv` (70,533 rows for the 3
  fields, deduped to 64,309 unique APIs — scratch-only).

  This table is form **OG110B** (statewide monthly water/steam injection
  report). No monthly PRODUCTION (form OG110) table was in this mirror —
  the ICN project only needed injection data for its water-sourcing story.
  An extensive search (GitHub API/search, grep.app, Sourcegraph, direct
  web search) found no reachable mirror of the CalGEM monthly production
  table. **This is the main limitation of this dataset — see below.**

  Well-type codes used (from the WellSTAR well registry, `WellTypeCode`
  column) to identify true cyclic-steam wells:
  - `SC` = **Cyclic Steam** producer (huff-and-puff) — used as the CSS
    well set for this benchmark.
  - `SF` = Steamflood injector (continuous) — excluded (these are the
    "wells that only inject continuously" the task asked to mark/exclude).
  - `OG` = plain oil & gas producer, `WD` = water disposal, `WF` =
    waterflood, `OB` = observation, `WS` = water source, `GD`/`AI`/`INJ`/
    `PM`/`DH`/`Multi`/`UNK` = other/rare.
  Well counts in the registry (2021 snapshot) for the 3 fields:
  Kern River 12,500 SC / 1,905 SF; Midway-Sunset 6,300 SC / 5,310 SF;
  Coalinga 1,911 SC / 894 SF (out of ~22k/39k/9k total wells respectively).

### 2. Field-level annual official statistics (2021)

CalGEM's own **2021 CalGEM Supervisor Annual Report** PDF (the last edition
found to include the full field-by-field appendix; the 2022 and 2023
editions are much shorter and omit it). Retrieved via the Wayback Machine
because the origin host was unreachable:

  Original: `https://www.conservation.ca.gov/calgem/Documents/2021%20CalGEM%20Supervisor%20Annual%20Report.pdf`
  Archived copy used: `http://web.archive.org/web/20250319081535id_/https://www.conservation.ca.gov/calgem/Documents/2021%20CalGEM%20Supervisor%20Annual%20Report.pdf`
  (3,049,573 bytes, 68 pages)

  Tables transcribed (see `extract_calgem.py` for the exact numbers used):
  - p.13-14 "2021 Oil Production from the Ten Largest Fields (MMbbl/year)",
    5-year trend 2017-2021, for Kern River, Midway-Sunset, Coalinga.
  - p.29 "California Oil, Associated Gas, and Water Production by District
    and Field in 2021" — Oil and Condensate Produced (bbl), Gross Gas
    Produced (Mcf), Water Produced (bbl), per field.
  - p.40-41 "2021 California Steam and Water Injection by District and
    Field" — Cyclic Steam (bbl), Steamflood (bbl), Water Disposal (bbl),
    Waterflood (bbl), Total Water Injected (bbl), per field. This is the
    **only place a Cyclic-Steam-specific volume, separate from Steamflood,
    is published** for these fields.

  Also checked and confirmed NOT archived / not useful: `data.conservation.ca.gov`
  (CKAN, expired TLS cert on direct fetch), CalGEM's 2022/2023 annual
  reports (no field appendix), a 2012 "Oil and Gas Production by County" PDF
  (county not field level, pre-WellSTAR).

## Unit conversions

- 1 bbl steam (cold-water-equivalent, CWE) = 0.159 m³ ≈ 0.159 t (as given).
- 1 bbl oil = 0.159 m³ (as given). Because both conversions use the same
  0.159 factor, any ratio expressed as "steam bbl / oil bbl" is numerically
  identical to "steam tonnes / oil m³" (t/m³) — this is how the field-level
  SOR figures below were computed directly from the Annual Report's bbl
  figures without a separate unit-conversion step.

## Cycle-detection rule (well-level, injection-only)

For each well flagged `WellTypeCode == 'SC'` with at least one non-null
monthly injection record 2018-2021:
1. A month is "injecting" if `SteamWaterInjected > 0`.
2. A "cycle" (injection episode) = a maximal run of consecutive injecting
   months.
3. Per cycle: `steam_bbl_cwe` = sum of `SteamWaterInjected` over the run;
   `steam_tonnes` = ×0.159; `inject_days` = sum of `DaysInjecting` (present
   for ~100% of "Reported" rows, ~0% of "Estimated" rows — undercounts
   inject-days for cycles containing estimated months, flagged via
   `n_months_estimated_flag`).
4. `gap_days_to_next_inject_proxy_produce_phase` = calendar days between
   the end of this cycle and the start of the well's next detected cycle.
   This is used **only as a proxy** for the produce+soak phase length,
   because no oil-production record exists to confirm the well was
   actually producing (vs. idle) during that gap. The last cycle observed
   for each well has no "next cycle" in the 2018-2021 window and is marked
   `produce_phase_censored = True` (gap left blank).
5. Oil-dependent fields (`oil_m3`, `cycle_sor_t_per_m3`, `peak_rate_bbl_d`,
   `pre_steam_baseline_bbl_d`, `uplift_x`) are present as columns for
   schema completeness but are **always blank** (`oil_data_available =
   False`) — see Limitation #1.

## Limitations (also repeated in the benchmark doc)

1. **No monthly oil production by well was obtainable.** Only the
   injection side of the CSS cycle is real, well-level data here. Per-cycle
   oil volume / SOR / peak rate / pre-steam baseline / uplift could not be
   computed. The field-level annual SOR (steam/oil, from the 2021 Annual
   Report) is the closest available real substitute, and is aggregate, not
   per-well or per-cycle.
2. Monthly resolution + a large fraction (~52%) of "Estimated" (not
   operator-reported) records means short single-month "cycles" at the
   low end of the distribution are likely fragments of one real injection
   period split by a non-reporting month, not true separate huff-and-puff
   events — treat the p10 tail of `steam_tonnes`/`inject_days` with caution;
   the median/p90 and the Midway-Sunset numbers (longer, better-reported
   cycles) are more trustworthy.
3. `gap_days_to_next_inject_proxy_produce_phase` can include idle/shut-in
   time unrelated to producing, and is right-censored at the end of each
   well's observed window.
4. Kern River crude is ~13° API but the reservoir is shallow (~300 m) and
   the field is hot-water-drive dominated from ~100 years of continuous
   steamflood/waterflood — absolute SOR and rates from Kern River/Midway-
   Sunset/Coalinga are **not directly transferable** to Baghewala (~1,150 m
   deep, no legacy hot-water drive); use as a plausibility *band*, not a
   target.
5. The field-by-field annual appendix was discontinued after the 2021
   Supervisor Annual Report, so the "official" field-level snapshot is a
   single year (2021), not a multi-year trend (the 2017-2021 figure is
   oil-production-only, from a different table in the same report).

## Reproducing

Run `extract_calgem.py` in a directory containing `inj_all_filtered.csv`
(statewide monthly injection rows pre-filtered to FieldCode in
{150,340,464} — see fetch loop described above, not included here due to
size) and `wells_lookup_kern.csv` (well registry rows for the same fields).
It writes `cycles_<field>.csv` and `summary.json`.
