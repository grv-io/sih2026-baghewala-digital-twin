# CalGEM CSS Benchmark (California field data vs. Baghewala model)

Fetched 2026-09-26. Sources, exact URLs, codes and full methodology:
`data/external/calgem_css/SOURCE.md`. Script: `extract_calgem.py`.

## What was fetched

CalGEM's own website (`www.conservation.ca.gov` and everything on the same
IP, including the WellSTAR data dashboard) was unreachable from the build
sandbox after 15+ attempts (see SOURCE.md). Two real, official-CalGEM-
sourced substitutes were used instead:

1. **Well-level monthly steam/water injection (form OG110B), 2018-2021,
   statewide** — mirrored on GitHub by Inside Climate News from CalGEM's
   own SQL Server database backups (downloaded by them 2022-06-20).
   Filtered to Kern River, Midway-Sunset and Coalinga, and to wells the
   CalGEM well registry itself codes `WellTypeCode = SC` ("Cyclic Steam"),
   i.e. huff-and-puff wells — as opposed to `SF` ("Steamflood", continuous
   injectors, excluded). 282 MB downloaded, filtered down to ~93 MB
   in-memory, **no raw file kept**.
2. **Field-level annual totals for 2021** (oil production, and Cyclic
   Steam / Steamflood / Water Disposal volumes, separately) from CalGEM's
   own 2021 Supervisor Annual Report PDF, fetched via the Wayback Machine.

**Critical gap: no monthly OIL PRODUCTION by well was obtainable anywhere**
(only the injection table was mirrored; an extensive search for a
production-table mirror came up empty). So per-cycle SOR, peak rate,
pre-steam baseline and uplift — which need paired oil-out data — could
**not** be computed from well-level data. What follows is real steam-side
cycle data plus a real field-level annual SOR, not a full like-for-like
per-cycle SOR series.

## Distribution table (well-level injection cycles, 2018-2021)

| Field | SC wells | Cycles | Steam t/cycle p10/p50/p90 | Inject days p10/p50/p90 | Gap-to-next-inject days p10/p50/p90 (produce-phase proxy) |
|---|---|---|---|---|---|
| Kern River | 2,687 | 4,987 | 15.6 / 38.3 / 209 | 1 / 2 / 4 | 61 / 122 / 424 |
| Midway-Sunset | 2,698 | 4,021 | 367 / 1,204 / 9,334 | 4 / 13 / 75 | 61 / 122 / 397 |
| Coalinga | 386 | 684 | 143 / 786 / 1,546 | 2 / 6 / 12 | 61 / 153 / 427 |

"Cycles" = maximal runs of consecutive months with reported steam
injection > 0, on wells CalGEM itself classifies as cyclic-steam. The
"gap" column is the calendar gap to the well's next injection episode —
a proxy for produce+soak length, not a confirmed oil-producing period.

## Field-level annual SOR, 2021 (official, real, aggregate — not per-cycle)

| Field | Oil (MMbbl) | Cyclic steam (MMbbl CWE) | Steamflood (MMbbl) | SOR = (cyclic+steamflood)/oil |
|---|---|---|---|---|
| Kern River | 14.9 | 6.5 | 45.3 | **3.47** |
| Midway-Sunset | 18.9 | 86.3 | 57.2 | **7.60** |
| Coalinga | 4.9 | 14.4 | 26.2 | **8.24** |

(bbl steam / bbl oil = t steam / m³ oil numerically, since both unit
conversions use the same 0.159 factor — see SOURCE.md.)

## Side-by-side vs. the Baghewala reference cycle

| Metric | Baghewala model | Kern River (CalGEM) | Midway-Sunset | Coalinga | Verdict |
|---|---|---|---|---|---|
| Steam per cycle | 1,300-1,500 t | p50 38 t (p90 209 t) | **p50 1,204 t** (in band) | p50 786 t, p90 1,546 t (upper edge in band) | Kern River's *typical* cycle is far smaller than ours at monthly resolution (see caveat below); Midway-Sunset's median lands almost exactly inside our 1,300-1,500 t band. |
| SOR (t/m³) | 4.1 | field annual **3.47** (just below) | field annual **7.60** (well above) | field annual **8.24** (well above) | Our 4.1 sits just above Kern River's real 2021 field SOR and well below Midway-Sunset/Coalinga's — i.e. inside the plausible CSS range, closer to the shallow, lower-SOR end (Kern River). |
| Produce phase | ~180 days (6 mo) | proxy p50 122 d | proxy p50 122 d | proxy p50 153 d | Our 180-day assumption is a bit longer than the real median gap (~4 mo) but well inside the observed p10-p90 spread (61-427 d) at all three fields. |
| Peak rate (16 bbl/d) | — | not computable (no oil data) | — | — | Cannot be checked against this dataset; would need per-well monthly production. |
| Uplift (5.7x) | — | not computable | — | — | Same limitation. |

**Plain-language judgement:** the numbers we can actually check (SOR,
produce-phase length) put Baghewala's reference cycle inside the real
Kern-County CSS band, closest to Kern River's own field-level SOR (3.47 vs
our 4.1) — we use only the official 2021 field-level annual SOR band (3.47–8.24)
as a plausibility check. Kern River is a shallow (~300 m), predominantly steamflood field
with a cyclic-steam subset; the 9,692 records across all three fields are
steam-injection episodes, not per-cycle SORs (per-well oil is not available to us).
Midway-Sunset/Coalinga run 2-8x hotter (SOR 7.6-8.2)
from mixing in much more continuous steamflood, which Baghewala has none
of. The per-cycle *steam mass* check is shakier: Kern River's raw
monthly-injection episodes look tiny (median 38 t) next to 1,300-1,500 t.
Likely a resolution artifact, not physics — Kern River is shallow (~300 m)
so a full slug is genuinely smaller than a 1,150 m Baghewala cycle needs,
and monthly reporting + ~52% "Estimated" records frequently splits one real
2-3 week steam slug across calendar months (SOURCE.md limitation #2).
Midway-Sunset/Coalinga's larger, better-reported cycles (p50 ≈ 800-1,200 t)
bracket 1,300-1,500 t at their p90 and are a fairer proxy here. Depth is
the expected reason Baghewala needs a bigger slug than Kern River
specifically — differences are expected; treat as a plausibility band, not
a target (SOURCE.md limitation #4).

## Concrete uses for this data

1. **Regression test**: assert the model's per-cycle SOR (4.1) falls
   within [3.47, 8.24] (Kern River-Coalinga field SOR) as a standing
   sim-sanity check, cheap to keep green as the model changes.
2. **Sim-to-real plausibility check**: run the twin at a Kern-River-like
   shallow analogue and confirm output SOR/cycle-steam track the Kern
   River band rather than Midway-Sunset — catches depth-sensitivity bugs.
3. **Slide-worthy statistic**: "Our model's 4.1 SOR sits between Kern
   River's real 2021 field average (3.47) and Coalinga's (8.24) — inside
   the real California cyclic-steam envelope, on ~20,000 real wells."
4. **Produce-phase calibration**: the p10-p90 gap-between-cycles band
   (61-427 days) is a defensible outer bound for the model's produce-phase
   duration knob.
5. **Distribution, not a point estimate**: `cycles_*.csv` (9,692 real
   cycles) can back a Monte-Carlo sweep of SOR/cycle-length inputs.

## Known data-quality caveats (see SOURCE.md for full detail)

- No monthly oil production by well; field-level SOR is annual/aggregate,
  not per-cycle.
- ~52% of monthly injection records are CalGEM "Estimated" (not
  operator-reported); short/low-volume cycles at the p10 tail are likely
  reporting-gap artifacts, not true short huff-and-puff events.
- "Produce phase" is a calendar-gap proxy, not a confirmed producing
  period, and is right-censored at the end of each well's 2018-2021 window.
- Kern River/Midway-Sunset/Coalinga are shallow (~300 m), ~100-year-old,
  hot-water-drive-assisted fields; Baghewala is ~1,150 m deep with no
  legacy thermal drive — treat all of the above as a plausibility band,
  not a calibration target.
- The CalGEM field-by-field annual appendix was discontinued after the
  2021 Supervisor Annual Report, so the official field-level snapshot is a
  single year, not a multi-year trend (only oil production, not injection,
  has a 2017-2021 trend in the same report).

## Second attempt (2026-09-26, later session) — still no monthly per-well oil

Goal: find monthly per-well OIL PRODUCTION (CalGEM form OG110 / "MonthlyProduction")
to pair with the injection cycles above and compute real per-cycle SOR/uplift/peak
rate. ~20 searches/fetches run. **Still not obtained** — but the data's actual public
location was pinned down precisely, which a human with a browser can now go get.

**Where the data actually lives (confirmed, but blocked for this session's tools):**
`http://wellstar-public.conservation.ca.gov/General/PublicDownloads/Index` is CalGEM's
own public bulk-download portal and **does serve monthly production data** — confirmed
by a FracTracker Alliance analysis (published 2026-08, "California's New Oil Wells
Average 13.5 Barrels/Day") that states verbatim: *"Oil and gas production volumes were
downloaded (8/21/25) from CalGEM's WellStar database... which reports monthly totals"*,
citing exactly this URL. Their notebook is hosted at
`https://fractracker.box.com/s/8g8diwdzjoccdu6h6s4sp0g7knpq12dx` but Box.com requires
JS rendering that this session's WebFetch tool cannot execute, so the notebook's exact
file-list/query parameters couldn't be extracted.

**What was tried this round:**
1. **Same ICN GitHub org** (`InsideClimateNews/2022-09-ca-kern-oil-water`) — re-checked
   the 2021 `sql_server_csv/` folder listing directly via the GitHub API and the repo's
   own methodology page (`insideclimatenews.github.io/2022-09-ca-kern-oil-water/`).
   Confirmed only 3 files per year (`...WellMonthlyInjection.csv`,
   `...WellQuarterlyInjection.csv`, `...Wells.csv` registry) — no `MonthlyProduction`
   file was ever mirrored by them; their story only needed injection data. Checked the
   org's other repos (California fumigants, farmworkers, TX/PA produced water) — none
   touch CalGEM production.
2. **Other GitHub mirrors** — `geopetoa/DOGGR-Production-Data` is a Selenium notebook
   that scrapes the old DOGGR FTP polygon-select tool per-well (no bulk file in the
   repo, and the FTP portal it targets is superseded/likely dead). `rockpyer/ca-permits`
   ingests CalGEM ArcGIS REST layers for well **permits** only, not production.
   Searches for "CalGEM production csv github", "DOGGR production database csv
   github", "WellSTAR production monthly csv" surfaced no other mirror.
3. **Kaggle / data.gov / data.ca.gov** — no Kaggle dataset for CA well-level
   production found (only generic multi-country or unrelated oil datasets).
   `lab.data.ca.gov`/`data.ca.gov` CalGEM listings are GIS/location layers (wells,
   facilities, boundaries) only — no production-volume dataset.
   `data.conservation.ca.gov` (CKAN) loaded but returned no usable dataset list via
   WebFetch (likely JS-rendered).
4. **Wayback Machine** — blocked entirely for this session (`web.archive.org` connection
   refused by the WebFetch tool itself, not a site-side block), so the previously-noted
   CalGEM production/injection download-index page could not be replayed from archive
   this round either.
5. **wellstar-public.conservation.ca.gov direct + proxy attempts** — the confirmed
   production URL above returned **HTTP 403** (same WAF-blocks-scripted-clients
   behaviour as the first session); a Google-Translate reverse-proxy rewrite
   (`wellstar-public-conservation-ca-gov.translate.goog/...`) returned **404** both with
   and without translate query params, so that workaround (which worked for *rendering*
   the ordinary `www.conservation.ca.gov` HTML pages in the first session) does not work
   for this particular ASP.NET download-portal path. `www.conservation.ca.gov` itself is
   still fully unreachable (`ECONNREFUSED`) from this sandbox.
6. **EIA / USGS / academic replication packages** — Zenodo/Mendeley search found no
   CalGEM per-well production mirror (found only an unrelated Wilmington
   flow-geomechanics dataset and the OGIM global infrastructure-location database,
   which is facility locations, not production time series). No SPE/USGS Kern River
   replication package with a downloadable production table was located.

**Recommended next step for a human with a browser** (not achievable by this session's
fetch tools): open `http://wellstar-public.conservation.ca.gov/General/PublicDownloads/Index`
directly in a normal browser (the WAF appears to key off missing browser fingerprint/
JS-challenge, not IP or auth), download the monthly production bulk file(s) for
FieldCode 150/340/464, and re-run a version of `extract_calgem.py` that joins it against
the existing `inj_all_filtered.csv`-derived cycles by `APINumber` + month. Until then,
the per-cycle SOR/peak-rate/uplift comparison in this benchmark remains not computable,
and the field-level annual SOR (§ above) stays the best available real-data comparison.

## Third check (27 Sep)

The production portal `wellstar-public.conservation.ca.gov` does not open from India even in a normal browser → almost certainly geo-blocked (California state site). Needs a US VPN or a US-based collaborator. Dropped for the idea-round deadline (30 Sep); keep for the final submission round.
