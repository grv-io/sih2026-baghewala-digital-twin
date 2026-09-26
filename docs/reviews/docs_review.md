# SIH Baghewala Docs Review — Brutal Assessment

## Findings

### Finding 1
**SEVERITY:** MAJOR  
**FILE:** README.md (line 62)  
**PROBLEM:**  
Windows guidance uses cmd.exe syntax in a bash code block. Comment says `# Windows: start dashboard/index.html` — `start` is cmd.exe command, not native PowerShell. While PowerShell aliases it to `Start-Process` (so it technically works), this is:
1. Confusing (bash block contains cmd.exe command)
2. Not PowerShell-idiomatic
3. A teammate copying literally won't understand why the style changes mid-block

**EXACT SUGGESTED FIX:**  
Replace line 62–63 with:
```bash
# 5. Open the dashboard (talks to the API at localhost:8000)
python -m webbrowser dashboard/index.html
```
This is cross-platform (Windows PowerShell, macOS, Linux) and requires no special comment.  
OR, if you must show OS-specific variants:
```bash
# 5. Open the dashboard (talks to the API at localhost:8000)
# macOS/Linux: open dashboard/index.html
# Windows: Invoke-Item dashboard/index.html
python -m webbrowser dashboard/index.html  # Alternative (cross-platform)
```

---

### Finding 2
**SEVERITY:** MAJOR  
**FILE:** DEMO_SCRIPT.md (line 9)  
**PROBLEM:**  
Setup checklist uses backticks (markdown code formatting) around `http://localhost:8000/params`, but the URL is broken: `localhost:8000/params` is correct per SPEC, but the raw instruction says "confirmed reachable at `http://localhost:8000/params`" — no issue with the URL itself, but the **adjacent step** (line 10) says "dashboard/index.html already open in a browser tab, refreshed once against the live API."

This implies the dashboard must be opened *before* the API is confirmed working, which inverts a reasonable test order. If the API fails to start, opening the dashboard first wastes time. Better: confirm API health first (curl/test /params), *then* open dashboard and refresh.

**EXACT SUGGESTED FIX:**  
Reorder steps to:
```markdown
- [ ] `python api/main.py` running in a terminal, confirmed reachable at `http://localhost:8000/params` (test with `curl http://localhost:8000/params` or browser).
- [ ] `dashboard/index.html` already open in a browser tab, refreshed once against the live API (browser network tab shows GET requests to localhost:8000).
- [ ] Zoom the browser to a size where all four dashboard panels are visible without scrolling.
- [ ] Have a second terminal tab hidden but ready, in case you need to restart the API.
```

---

### Finding 3
**SEVERITY:** MAJOR  
**FILE:** DEMO_SCRIPT.md (line 25, timing mismatch)  
**PROBLEM:**  
The "2:10–2:45" segment (35 seconds) only contains ~43 spoken words. At natural speaking pace (1.5 words/sec), this fills ~29 seconds, leaving ~6 seconds of dead air or forced pausing. The segment immediately before (1:35–2:10, also 35 sec) has only ~70 words (~47 seconds at 1.5 wps) — **overshoots the timeslot**. This means either:
1. Timing allocation is wrong
2. Presenter must rush part of the script
3. Presenter must pause unnaturally

**EXACT SUGGESTED FIX:**  
Recalculate timeslots based on realistic word counts and add natural-pause guidance. Example revision for 2:10–2:45:
```markdown
| 2:10–2:50 | Click **Optimize**. Let the baseline-vs-optimized SOR bar chart render. | "So instead of guessing, we let a **Bayesian optimizer** search the 4 control knobs — steam volume, soak time, cutoff rate, pump speed — for us. We're minimizing SOR while keeping floating risk under 30%. Here's the baseline the field is running today versus what the optimizer recommends. [Let it settle.] That's the win: lower steam cost, rod stays safe." |
```
(Adds ~20 more words, stretches to fill the time.) Or collapse both segments into one unified ~70-second "Optimizer" section.

---

### Finding 4
**SEVERITY:** MINOR  
**FILE:** DEMO_SCRIPT.md (line 34–42, fallback instruction)  
**PROBLEM:**  
Fallback says "switch the dashboard's API base constant / mock-mode toggle (top of `dashboard/index.html`)" — this is clear for a coder but **does not specify which line or variable name** to change. Under panic (10-second constraint), a presenter might:
1. Open file and not find an obvious "API base constant" comment
2. Miss the toggle if it's named something like `USE_MOCK_DATA` or `API_HOST`
3. Accidentally edit the wrong part of the file

**EXACT SUGGESTED FIX:**  
Clarify the fallback with exact variable/line reference:
```markdown
Then switch the dashboard's API base constant: open `dashboard/index.html` in an editor, find the line near the top that says:
```javascript
const API_BASE = 'http://localhost:8000';  // Change this to null or empty string for mock mode
// OR const USE_MOCK_DATA = false;  // Change to true
```
Set it to `const API_BASE = '';` or `const USE_MOCK_DATA = true;` (whichever is in your code), save, and refresh the browser.
```
**Pre-flight:** test this fallback path once before the demo so you know exactly which line to change.

---

### Finding 5
**SEVERITY:** MINOR  
**FILE:** architecture.svg (line 19, 28, 37, 46 — font sizes)  
**PROBLEM:**  
The three detailed content lines (file paths and module names) use `font-size="13"`. This is legible on a screen but **marginal for projection** on a washed-out or poorly-lit screen. Amber text (#f59e0b) on dark background (#0d1117) has good contrast, but small font size + dim projector = readability risk.

Example problematic lines:
- Line 19: "≥ 3000 rows, Latin-hypercube / random sampling, seed = 42" (13px)
- Line 28: "twin/thermal.py · twin/viscosity.py · twin/ipr.py · twin/srp.py · twin/cycle.py" (13px)

**EXACT SUGGESTED FIX:**  
Increase the three `font-size="13"` instances to `font-size="14"` or `font-size="15"`:
```xml
<!-- Replace lines 19, 28, 37, 46 -->
<text x="565" y="155" text-anchor="middle" font-size="14" fill="#8b949e">≥ 3000 rows, Latin-hypercube / random sampling, seed = 42</text>
<text x="565" y="305" text-anchor="middle" font-size="14" fill="#8b949e">twin/thermal.py · twin/viscosity.py · twin/ipr.py · twin/srp.py · twin/cycle.py</text>
<text x="565" y="455" text-anchor="middle" font-size="14" fill="#8b949e">ml/train.py (XGBoost) · ml/optimize.py (scikit-optimize gp_minimize)</text>
<text x="565" y="605" text-anchor="middle" font-size="14" fill="#8b949e">dashboard/index.html (Plotly) — calls FastAPI /simulate  /optimize  /params</text>
```

---

### Finding 6
**SEVERITY:** MINOR  
**FILE:** DEMO_SCRIPT.md (line 21, mock-mode discovery)  
**PROBLEM:**  
The setup checklist does not mention *where* to find the mock-mode toggle in `dashboard/index.html`. If the live API fails, the presenter needs to locate and edit this toggle quickly. The fallback instruction assumes the toggle/constant is at the "top of `dashboard/index.html`", but if it's not clearly labeled as a toggle (e.g., if it's a JavaScript variable named `API_ENDPOINT` vs `USE_LIVE_API`), a panicked presenter might not find it in 10 seconds.

**EXACT SUGGESTED FIX:**  
Add a pre-flight checklist item:
```markdown
- [ ] **Fallback only:** Before the demo, open `dashboard/index.html` in a text editor and locate the API base constant or mock-mode toggle (e.g., `const API_BASE = 'http://localhost:8000'` or `const USE_MOCK_DATA = false`). Write down the exact line number so you can flip it in <10 seconds if the API fails.
```

---

### Finding 7
**SEVERITY:** MINOR  
**FILE:** GLOSSARY.md (no issue, but context note)  
**PROBLEM:**  
None — all 20 definitions are crisp, one sentence each, correct, and non-circular. This is the cleanest document in the set.

---

### Finding 8
**SEVERITY:** MINOR  
**FILE:** README.md (project layout table, line 82–84)  
**PROBLEM:**  
Table says `api/main.py` exposes endpoints "on port 8000", but does not mention that the API must be started *before* the dashboard can function. The quickstart (lines 52–62) implies this order by listing `python api/main.py` before opening the dashboard, but a user who skips ahead (e.g., opens the dashboard immediately after step 2) will see the dashboard fail silently if the API isn't running.

**EXACT SUGGESTED FIX:**  
Add a note after the table or in the quickstart:
```markdown
> **Dependency order (critical):** The synthetic data must be generated before training models; models must be trained before the API can load them; the API must be running before the dashboard can fetch data. If you skip or run steps out of order, you'll see errors.
```

---

## Document Scores

| Document | Score | Summary |
|----------|-------|---------|
| **README.md** | 7/10 | Working quickstart, but Windows cmd.exe guidance in bash block is suboptimal; dependency order not explicit enough. |
| **DEMO_SCRIPT.md** | 7/10 | Good narrative flow and structure, but timing/word-count alignment is loose; fallback instruction lacks specificity (variable names, line numbers). |
| **GLOSSARY.md** | 10/10 | Clean, concise, correct. All 20 terms are one sentence each; no circularity or technical bloat. Excellent reference. |
| **architecture.svg** | 9/10 | Excellent contrast and visual hierarchy; colors project well. Minor concern: 13px font size marginal for projection. |
| **docs/SPEC.md** | N/A | Reference document, not reviewed per brief (this is the spec, not a doc that must match it). ✓ Appears internally consistent. |

---

## Worst Finding

**README.md, line 62:** Windows cmd.exe command (`start`) in a bash code block. A PowerShell user will be confused by the style inconsistency, and the guidance is not Windows PowerShell-native. Fix: use `python -m webbrowser` (cross-platform) or explicit PowerShell command `Invoke-Item`.

**Cascading concern:** This confusion at the quickstart entry point may cause a new teammate to second-guess whether the other commands (e.g., `python api/main.py`) are correct for Windows, reducing confidence in the whole setup.

---

## Readiness Assessment

- **Technical accuracy:** Good. Physics/ML/API contracts are correct per SPEC.
- **Executable clarity:** Fair. Quickstart works, but Windows guidance and dependency order could be clearer.
- **Demo robustness:** Fair. Script is solid but timing is loose; fallback path is underdocumented.
- **Visual polish:** Very good. Architecture diagram is presentation-ready.
- **Judge-facing maturity:** 7/10. Docs are smart but need one pass to tighten Windows UX, timing, and fallback procedures before judges see them.

---

**Review completed:** 2026-09-13
