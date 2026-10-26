"""
Excel Test Execution Report Generator using openpyxl.
"""
from typing import Any

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill


def generate_excel_report(report_data: dict[str, Any], output_path: str) -> None:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Execution Summary"

    # Header styling
    header_fill = PatternFill(start_color="1F2937", end_color="1F2937", fill_type="solid")
    header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    pass_fill = PatternFill(start_color="D1FAE5", end_color="D1FAE5", fill_type="solid")
    fail_fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")

    headers = ["S.No", "Test Case ID", "Result", "Duration (s)", "Remarks"]
    for col_idx, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=h)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    test_cases = report_data.get("Test Cases", [])
    for row_idx, tc in enumerate(test_cases, 2):
        s_no = row_idx - 1
        tc_id = tc.get("TC_ID", "")
        tc_result = str(tc.get("TC_Result", "UNKNOWN")).upper()
        duration = tc.get("TC_Execution_Duration", "N/A")
        remarks = tc.get("TC_Remarks", "")

        ws.cell(row=row_idx, column=1, value=s_no)
        ws.cell(row=row_idx, column=2, value=tc_id)
        res_cell = ws.cell(row=row_idx, column=3, value=tc_result)
        ws.cell(row=row_idx, column=4, value=duration)
        ws.cell(row=row_idx, column=5, value=remarks)

        if tc_result == "PASSED":
            res_cell.fill = pass_fill
        elif tc_result in ("FAILED", "ERROR"):
            res_cell.fill = fail_fill

    # Adjust column widths
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    wb.save(output_path)
