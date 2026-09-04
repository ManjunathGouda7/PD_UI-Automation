"""
Interactive HTML Dashboard Report Generator for USB PD C2 UI Automation.
Includes Dark/Light mode toggle, visual summary stats, and step inspection.
"""
import html
from typing import Any

def generate_html_report(report_data: dict[str, Any], output_path: str) -> None:
    report_name = html.escape(str(report_data.get("Report Name", "PD_Report")))
    total_tests = report_data.get("Total Tests", 0)
    passed = report_data.get("Passed", 0)
    failed = report_data.get("Failed", 0)
    execution_time = html.escape(str(report_data.get("Total Time", "N/A")))
    dut_ip = html.escape(str(report_data.get("DUT_IP", "192.168.102.76")))
    test_cases = report_data.get("Test Cases", [])

    pass_pct = round((passed / total_tests) * 100, 1) if total_tests > 0 else 0

    rows_html = []
    for tc in test_cases:
        tc_id = html.escape(str(tc.get("TC_ID", "")))
        tc_result = str(tc.get("TC_Result", "UNKNOWN")).upper()
        duration = html.escape(str(tc.get("TC_Execution_Duration", "N/A")))
        badge_cls = "badge-pass" if tc_result == "PASSED" else ("badge-fail" if tc_result == "FAILED" else "badge-other")

        rows_html.append(f"""
        <tr>
            <td><strong>{tc_id}</strong></td>
            <td><span class="badge {badge_cls}">{tc_result}</span></td>
            <td>{duration}</td>
        </tr>
        """)

    table_rows = "".join(rows_html)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report_name} - GRL USB PD C2 Test Report</title>
    <style>
        :root {{
            --bg-base: #0a0b0f;
            --bg-card: #131622;
            --border-color: #232936;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent: #ff7800;
            --pass-color: #10b981;
            --fail-color: #ef4444;
        }}
        [data-theme="light"] {{
            --bg-base: #f8fafc;
            --bg-card: #ffffff;
            --border-color: #e2e8f0;
            --text-main: #0f172a;
            --text-muted: #64748b;
            --accent: #ea580c;
        }}
        body {{
            background: var(--bg-base);
            color: var(--text-main);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 30px;
            transition: background 0.3s, color 0.3s;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid var(--border-color);
            padding-bottom: 20px;
            margin-bottom: 25px;
        }}
        .title {{
            font-size: 24px;
            font-weight: 800;
            color: var(--accent);
        }}
        .theme-btn {{
            background: var(--bg-card);
            color: var(--text-main);
            border: 1px solid var(--border-color);
            padding: 8px 16px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }}
        .stat-val {{
            font-size: 32px;
            font-weight: 800;
            margin-top: 8px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            overflow: hidden;
        }}
        th, td {{
            padding: 14px 20px;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }}
        th {{
            background: rgba(255, 120, 0, 0.08);
            color: var(--accent);
            text-transform: uppercase;
            font-size: 12px;
            letter-spacing: 0.05em;
        }}
        .badge {{
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 700;
        }}
        .badge-pass {{ background: rgba(16, 185, 129, 0.2); color: var(--pass-color); }}
        .badge-fail {{ background: rgba(239, 68, 68, 0.2); color: var(--fail-color); }}
        .badge-other {{ background: rgba(148, 163, 184, 0.2); color: var(--text-muted); }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <div class="title">⚡ GRL USB PD C2 Automation Report</div>
            <div style="color: var(--text-muted); margin-top: 5px;">Report: {report_name} | DUT: {dut_ip} | Duration: {execution_time}</div>
        </div>
        <button class="theme-btn" onclick="toggleTheme()">🌓 Toggle Dark/Light</button>
    </div>

    <div class="stats-grid">
        <div class="stat-card">
            <div style="color: var(--text-muted); font-size: 13px;">TOTAL TESTS</div>
            <div class="stat-val">{total_tests}</div>
        </div>
        <div class="stat-card">
            <div style="color: var(--pass-color); font-size: 13px;">PASSED</div>
            <div class="stat-val" style="color: var(--pass-color);">{passed}</div>
        </div>
        <div class="stat-card">
            <div style="color: var(--fail-color); font-size: 13px;">FAILED</div>
            <div class="stat-val" style="color: var(--fail-color);">{failed}</div>
        </div>
        <div class="stat-card">
            <div style="color: var(--accent); font-size: 13px;">PASS RATE</div>
            <div class="stat-val" style="color: var(--accent);">{pass_pct}%</div>
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th>Test Case ID</th>
                <th>Result</th>
                <th>Duration</th>
            </tr>
        </thead>
        <tbody>
            {table_rows}
        </tbody>
    </table>

    <script>
        function toggleTheme() {{
            const current = document.documentElement.getAttribute('data-theme');
            const target = current === 'light' ? 'dark' : 'light';
            document.documentElement.setAttribute('data-theme', target);
        }}
    </script>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
