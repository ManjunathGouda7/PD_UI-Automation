# GRL USB PD C2 (V-DPWR-EPR) UI & API Automation

Playwright + pytest automation for the **GRL-V-DPWR-EPR USB Power Delivery and Type-C Test Software**
(web UI served by the GRL software at `http://localhost:5003`). Locators and API contracts are verified
against software **1.1.1.4** (`/v1.1.4.html`).

## What it covers

| Suite | Scope |
|---|---|
| `test_00_app_shell` | Title / model / version vs API, left navigation, every panel activates |
| `test_01_connection` | Tester Status table vs `GET /api/ConnectionSetup`, IP field, licenses, calibration validity; scan / connect *(hardware)* |
| `test_02_product_cap` | DUT type & cable options, Port 1 selection vs `GetPortConfigurations`, project-name validation; select & persist, Read Device Data *(hardware)* |
| `test_03_test_config` | Test count vs API (215), certification filter vs API, report inputs vs API, rerun controls, test tree |
| `test_04_results` | Summary counters vs `GetTestResults`, chart toolbar, empty-plot state |
| `test_05_report` | Toolbar, report location, HTML download prompt |
| `test_06_configure` | Controller options, channel toggles (client-side, restored), capture buttons; Apply *(hardware)* |
| `test_07_loopback` | Data fields & units, Start/Stop gating |
| `test_08_help` | Version vs API, support links, API document served, debug-log download |
| `test_09_api` | Read-only REST checks + **contract tests** against the live Swagger spec (every endpoint used by `C2ApiClient` exists; responses match their published schemas) |

## Safety model

The suite runs against a shared, real tester. By default it is **read-only**:

* Tests that change tester/backend state (connect, scan, apply config, attach/detach, change DUT type,
  read device data) are marked `hardware` and **skipped** unless `--allow-hw-actions` / `ALLOW_HW_ACTIONS=true`.
* Tests needing a connected tester are marked `requires_tester`; they wait up to `TESTER_WAIT_S`
  (30 s) for a connection, then skip — or fail with `--strict-hardware`.
* App popups: single-button informational alerts (e.g. *Controller Calibration Alert*) are acknowledged
  automatically and recorded; confirmation prompts (Ok/Cancel) are **never** auto-answered.
* No silent fallback: if the backend is unreachable the run aborts. The offline mock is used only with
  `--mock`, serves the API only (UI tests are skipped), and refuses to start if port 5003 is in use.
* UI tests must not run in parallel against one tester (`-w` > 1 is for API tests only).

## Quick start

```powershell
python -m pip install -r requirements.txt
python -m playwright install chromium
copy Configurations\.env.example Configurations\.env   # optional overrides

python run.py                      # smoke (read-only, UI + API)
python run.py --mode full          # everything safe to run
python run.py --mode api           # REST API only, no browser
python run.py --mode full --allow-hw-actions --strict-hardware   # include tests that drive the tester
python run.py --smart              # suites affected by your git changes
python run.py --mode api --mock    # API suite against the offline mock (GRL software not running)
python run.py --gui                # PyQt6 desktop runner
```

Plain pytest works too (config lives in `pyproject.toml`): `pytest -m smoke`, `pytest -m "connection and not hardware"`.

## Configuration

Precedence: environment variable → `Configurations/.env` → `jsons/Inputs.json` → default.

| Variable | Default | Purpose |
|---|---|---|
| `BASE_URL` | `http://localhost:5003` | GRL software host; the versioned page is resolved from `/api/App/GetURLVersionExtension` |
| `DUT_IP` | `192.168.255.1` (Inputs.json) | Tester IP used by the connect test |
| `HEADLESS` | `true` | Browser mode |
| `ALLOW_HW_ACTIONS` | `false` | Enable `hardware` tests |
| `STRICT_HARDWARE` | `false` | Fail instead of skip without a tester |
| `MOCK_SERVER` | `false` | Offline API mock |
| `UI_TIMEOUT_MS` / `PAGE_LOAD_TIMEOUT_MS` / `AUTO_CONNECT_TIMEOUT_MS` / `TESTER_WAIT_S` | 10000 / 30000 / 90000 / 30 | Timing |

Expected UI values (dropdown options, labels, URLs) live in `jsons/test_data.json`.

## Architecture

```
Scripts/
  Helpers/  config.py, Locators.py (verified ids), api_client.py, swagger_contract.py,
            popups.py (PopupGuard), waits.py, mock_server.py, logger.py, smart_test_selector.py
  Pages/    base_page.py (panel-scoped lookups, dropdowns, self-heal), app_page.py, one page per panel
  TestCases/ test_00 … test_09
  UI/       PyQt6 runner, HTML / Excel reports
  conftest.py  backend check, run modes, browser/page fixtures, popup guard, failure artifacts
```

Notes on the application that shaped the design:

* The UI is one long scrolling page; all panels are always mounted. The active panel's wrapper has
  `.scroll-content-sticky`. Element lookups are therefore **scoped to the panel** (several ids repeat).
* Dropdowns are Bootstrap button menus (`[aria-labelledby=<id>] .dropdown-item`), not `<select>`.
* On load the app auto-connects to the last tester (~5 s); readiness waits for *Scan Network* to enable.
* The app polls continuously, so `networkidle` never settles — readiness is element-based.
* On tester disconnect the app jumps to *Connection Setup* by itself; page objects re-open their panel once
  and log a warning.
* `/api/C2Api/GetConnectionStatus` is **not** the UI tester status — use `GET /api/ConnectionSetup`
  (`C2ApiClient.is_tester_connected()`).

## Reports

Every run (GUI, `run.py` or plain pytest) writes its own folder, named after the panel(s) it covered:

```
Reports/
  Connection_Setup/2026-10-26_14-52-16/      one panel
    report.html  report.xlsx  summary.json
    fail_<test>.png  trace_<test>.zip         only for failed tests
    downloads/                                files downloaded by tests (e.g. Debug_Log.txt)
  All_Panels/2026-10-26_14-53-45/             Run All
    report.html  report.xlsx  summary.json    overall
    Connection_Setup/ Help/ REST_API/ ...     per-panel report + that panel's failure artifacts
  Multiple_Panels/<timestamp>/                any other mix of panels (same layout as All_Panels)
```

Open a trace with `playwright show-trace <trace.zip>`. The GUI's **📂 Open Report** button opens the last run's folder.
CI also writes JUnit XML to `Reports/junit.xml`; `--allure` adds Allure results. Logs: `logs/automation.log`.

One browser window serves the whole run: tests share a page that is reset between tests (popups and menus
closed, app reloaded only if unhealthy), so the window is not closed and reopened per test.

## Known product issues (tracked by tests)

| Test | Issue |
|---|---|
| `test_02 … TC_04` (xfail, strict) | Project *Save* stays enabled after the name is cleared or is whitespace only |
| `test_03 … TC_08` | Test selection tree renders no nodes although the UI receives all 215 test cases |
| `test_01 … TC_05` | During reconnect the UI briefly shows calibration dates `0001-01-01` / *Calibration Error* and raises a false *Controller calibration has expired* alert |
