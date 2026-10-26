"""
Self-contained HTML report for a GRL USB PD C2 automation run.

Sections: run / tester environment, summary tiles, pass-rate trend of previous runs,
and a filterable results table whose failed rows expand to the error text, an inline
failure screenshot and a link to the Playwright trace.
"""
import html
from typing import Any

RESULT_CLASS = {"PASSED": "pass", "FAILED": "fail", "ERROR": "fail", "SKIPPED": "skip", "XFAIL": "xfail"}


def _e(value: Any) -> str:
    return html.escape(str(value if value is not None else ""))


def _environment(env: dict[str, Any]) -> str:
    if not env:
        return ""
    cells = "".join(f"<div class='env-item'><span>{_e(k)}</span><b>{_e(v)}</b></div>" for k, v in env.items())
    return f"<section class='card env'>{cells}</section>"


def _trend(history: list[dict[str, Any]]) -> str:
    if len(history) < 2:
        return ""
    bars = []
    for run in history[-20:]:
        executed = run.get("passed", 0) + run.get("failed", 0)
        rate = round(100 * run.get("passed", 0) / executed) if executed else 0
        color = "var(--pass)" if run.get("failed", 0) == 0 else "var(--fail)"
        tip = f"{run.get('run')}: {run.get('passed', 0)} passed, {run.get('failed', 0)} failed, {run.get('skipped', 0)} skipped"
        bars.append(f"<div class='bar' title='{_e(tip)}'><div style='height:{max(rate, 4)}%;background:{color}'></div></div>")
    return (f"<section class='card'><div class='section-title'>Pass rate - last {len(bars)} runs</div>"
            f"<div class='trend'>{''.join(bars)}</div></section>")


def _rows(test_cases: list[dict[str, Any]]) -> str:
    rows = []
    for i, tc in enumerate(test_cases):
        result = str(tc.get("TC_Result", "UNKNOWN")).upper()
        cls = RESULT_CLASS.get(result, "skip")
        detail_parts = []
        if tc.get("Message"):
            detail_parts.append(f"<pre>{_e(tc['Message'])}</pre>")
        if tc.get("Screenshot"):
            src = _e(tc["Screenshot"])
            detail_parts.append(f"<a href='{src}' target='_blank'><img src='{src}' alt='failure screenshot'></a>")
        if tc.get("Trace"):
            detail_parts.append(f"<div>Trace: <code>playwright show-trace {_e(tc['Trace'])}</code></div>")
        expandable = bool(detail_parts)
        toggle = f" onclick=\"toggle('d{i}')\" class='clickable'" if expandable else ""
        rows.append(
            f"<tr data-result='{cls}'{toggle}>"
            f"<td>{_e(tc.get('Panel', ''))}</td>"
            f"<td><b>{_e(tc.get('Title') or tc.get('TC_ID', ''))}</b>"
            f"{' <span class=more>details</span>' if expandable else ''}</td>"
            f"<td>{_e(tc.get('Spec', ''))}</td>"
            f"<td><span class='badge {cls}'>{_e(result)}</span></td>"
            f"<td>{_e(tc.get('TC_Execution_Duration', ''))}</td>"
            f"<td class='remarks'>{_e(tc.get('TC_Remarks', ''))}</td></tr>")
        if expandable:
            rows.append(f"<tr id='d{i}' class='detail' data-result='{cls}' hidden>"
                        f"<td colspan='6'>{''.join(detail_parts)}</td></tr>")
    return "".join(rows)


def generate_html_report(report_data: dict[str, Any], output_path: str) -> None:
    name = _e(report_data.get("Report Name", "PD_Report"))
    total = report_data.get("Total Tests", 0)
    passed = report_data.get("Passed", 0)
    failed = report_data.get("Failed", 0)
    skipped = report_data.get("Skipped", 0)
    executed = passed + failed
    pass_rate = round(100 * passed / executed, 1) if executed else 0
    test_cases = report_data.get("Test Cases", [])

    content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{name} - GRL USB PD C2 Test Report</title>
<style>
:root {{ --bg:#0a0b0f; --card:#131622; --border:#232936; --text:#f8fafc; --muted:#94a3b8;
        --accent:#ff7800; --pass:#10b981; --fail:#ef4444; --skip:#f59e0b; --xfail:#a78bfa; }}
[data-theme="light"] {{ --bg:#f8fafc; --card:#ffffff; --border:#e2e8f0; --text:#0f172a; --muted:#64748b; --accent:#ea580c; }}
body {{ background:var(--bg); color:var(--text); font-family:'Segoe UI',Roboto,sans-serif; margin:0; padding:24px; }}
.header {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; }}
.title {{ font-size:22px; font-weight:800; color:var(--accent); }}
.sub {{ color:var(--muted); margin-top:4px; }}
button {{ background:var(--card); color:var(--text); border:1px solid var(--border); padding:7px 14px;
         border-radius:8px; cursor:pointer; font-weight:600; }}
button.active {{ border-color:var(--accent); color:var(--accent); }}
.card {{ background:var(--card); border:1px solid var(--border); border-radius:12px; padding:16px; margin-bottom:16px; }}
.env {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:10px; }}
.env-item span {{ display:block; color:var(--muted); font-size:12px; }}
.stats {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px; margin-bottom:16px; }}
.stat {{ background:var(--card); border:1px solid var(--border); border-radius:12px; padding:14px; text-align:center; }}
.stat div:first-child {{ color:var(--muted); font-size:12px; }}
.stat div:last-child {{ font-size:28px; font-weight:800; margin-top:4px; }}
.section-title {{ color:var(--muted); font-size:12px; margin-bottom:8px; }}
.trend {{ display:flex; gap:4px; align-items:flex-end; height:60px; }}
.bar {{ flex:1; height:100%; display:flex; align-items:flex-end; background:rgba(148,163,184,.12); border-radius:3px; }}
.bar div {{ width:100%; border-radius:3px; }}
.filters {{ display:flex; gap:8px; margin-bottom:10px; }}
table {{ width:100%; border-collapse:collapse; background:var(--card); border:1px solid var(--border); }}
th, td {{ padding:10px 14px; text-align:left; border-bottom:1px solid var(--border); vertical-align:top; }}
th {{ color:var(--accent); font-size:12px; text-transform:uppercase; letter-spacing:.05em; }}
tr.clickable {{ cursor:pointer; }}
.more {{ color:var(--accent); font-size:11px; margin-left:6px; }}
.remarks {{ color:var(--muted); font-size:13px; max-width:520px; }}
.badge {{ padding:3px 9px; border-radius:6px; font-size:12px; font-weight:700; }}
.badge.pass {{ background:rgba(16,185,129,.18); color:var(--pass); }}
.badge.fail {{ background:rgba(239,68,68,.18); color:var(--fail); }}
.badge.skip {{ background:rgba(245,158,11,.18); color:var(--skip); }}
.badge.xfail {{ background:rgba(167,139,250,.18); color:var(--xfail); }}
tr.detail td {{ background:rgba(0,0,0,.18); }}
tr.detail pre {{ white-space:pre-wrap; color:#fca5a5; font-size:12px; max-height:320px; overflow:auto; }}
tr.detail img {{ max-width:720px; width:100%; border:1px solid var(--border); border-radius:8px; margin:8px 0; }}
</style>
</head>
<body>
<div class="header">
  <div>
    <div class="title">GRL USB PD C2 Automation Report</div>
    <div class="sub">{name} &nbsp;|&nbsp; Duration {_e(report_data.get("Total Time", "N/A"))}</div>
  </div>
  <button onclick="toggleTheme()">Dark / Light</button>
</div>
{_environment(report_data.get("Environment", {}))}
<div class="stats">
  <div class="stat"><div>TOTAL</div><div>{total}</div></div>
  <div class="stat"><div>PASSED</div><div style="color:var(--pass)">{passed}</div></div>
  <div class="stat"><div>FAILED</div><div style="color:var(--fail)">{failed}</div></div>
  <div class="stat"><div>SKIPPED / XFAIL</div><div style="color:var(--skip)">{skipped}</div></div>
  <div class="stat"><div>PASS RATE (executed)</div><div style="color:var(--accent)">{pass_rate}%</div></div>
</div>
{_trend(report_data.get("History", []))}
<div class="filters">
  <button class="active" onclick="filterRows('all', this)">All</button>
  <button onclick="filterRows('fail', this)">Failed</button>
  <button onclick="filterRows('skip', this)">Skipped</button>
  <button onclick="filterRows('pass', this)">Passed</button>
</div>
<table>
  <thead><tr><th>Panel</th><th>Test</th><th>Spec</th><th>Result</th><th>Duration</th><th>Remarks</th></tr></thead>
  <tbody>{_rows(test_cases)}</tbody>
</table>
<script>
function toggleTheme() {{
  const el = document.documentElement;
  el.setAttribute('data-theme', el.getAttribute('data-theme') === 'light' ? 'dark' : 'light');
}}
function toggle(id) {{ const r = document.getElementById(id); r.hidden = !r.hidden; }}
function filterRows(kind, btn) {{
  document.querySelectorAll('.filters button').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  document.querySelectorAll('tbody tr').forEach(r => {{
    const res = r.dataset.result;
    const match = kind === 'all' || res === kind || (kind === 'skip' && res === 'xfail');
    if (r.classList.contains('detail')) {{ if (!match) r.hidden = true; }}
    else r.style.display = match ? '' : 'none';
  }});
}}
</script>
</body>
</html>"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
