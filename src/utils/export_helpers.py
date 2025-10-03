"""Utilities for exporting CSV and PDF reports.

These helpers keep UI-free logic separate; callers handle file dialogs and messages.
"""
from __future__ import annotations

from typing import Iterable, Sequence, Optional

from ..config import DEFAULT_CSV_ENCODING


def format_period_label(period: str, today_qdate) -> str:
    """Return a human-friendly period label for filenames and headers.
    period: one of daily, weekly, monthly, yearly
    today_qdate: QDate instance passed by caller to avoid importing Qt at module import time
    """
    if period == "daily":
        return today_qdate.toString("yyyy-MM-dd")
    if period == "weekly":
        start = today_qdate.addDays(-7)
        return f"{start.toString('yyyy-MM-dd')} to {today_qdate.toString('yyyy-MM-dd')}"
    if period == "monthly":
        return today_qdate.toString("MMMM yyyy")
    if period == "yearly":
        return today_qdate.toString("yyyy")
    return today_qdate.toString("yyyy-MM-dd")


def export_department_attendance_csv(
    rows: Iterable[dict],
    period_label: str,
    path: str,
    encoding: str = DEFAULT_CSV_ENCODING,
) -> None:
    """Write department attendance rows to CSV.
    Each row should contain: department, total_employees, present, late, absent
    """
    with open(path, "w", encoding=encoding, newline="") as f:
        f.write("Period,Department,Total Employees,Present,Late,Absent\n")
        for d in rows:
            f.write(
                f"{period_label},{d.get('department','')},{d.get('total_employees',0)},{d.get('present',0)},{d.get('late',0)},{d.get('absent',0)}\n"
            )


def build_department_attendance_html(title: str, period_label: str, rows: Iterable[dict]) -> str:
    """Build a simple HTML table for department attendance.
    Caller can render this HTML to PDF using export_html_to_pdf.
    """
    html = [
        f"<h2 style=\"text-align:center;\">{title} – {period_label}</h2>",
        "<br>",
        "<table border=\"1\" cellspacing=\"0\" cellpadding=\"10\" width=\"100%\">",
        "<thead>",
        "<tr style=\"background-color:#f3f4f6;\">",
        "<th align=\"left\">Department</th>",
        "<th align=\"center\">Total Employees</th>",
        "<th align=\"center\">Present</th>",
        "<th align=\"center\">Late</th>",
        "<th align=\"center\">Absent</th>",
        "</tr>",
        "</thead>",
        "<tbody>",
    ]
    for d in rows:
        html.append(
            "<tr>"
            f"<td>{d.get('department','')}</td>"
            f"<td align=\"center\">{d.get('total_employees',0)}</td>"
            f"<td align=\"center\">{d.get('present',0)}</td>"
            f"<td align=\"center\">{d.get('late',0)}</td>"
            f"<td align=\"center\">{d.get('absent',0)}</td>"
            "</tr>"
        )
    html.append("</tbody></table>")
    return "".join(html)


def export_html_to_pdf(html: str, path: str) -> None:
    """Render HTML string to a PDF file using Qt's QTextDocument.
    Imported lazily so non-Qt environments importing this module won't fail.
    """
    from PyQt6.QtGui import QPdfWriter, QPainter, QFont, QTextDocument
    from PyQt6.QtCore import QSizeF
    from PyQt6.QtGui import QPageSize, QPageLayout

    writer = QPdfWriter(path)
    writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    writer.setPageOrientation(QPageLayout.Orientation.Portrait)

    doc = QTextDocument()
    doc.setDefaultFont(QFont("Inter", 10))
    doc.setHtml(html)

    painter = QPainter(writer)
    doc.setPageSize(QSizeF(writer.width(), writer.height()))
    doc.drawContents(painter)
    painter.end()


def export_qtablewidget_to_csv(table, path: str, encoding: str = DEFAULT_CSV_ENCODING) -> None:
    """Dump the current contents of a QTableWidget to CSV.
    Column headers are included as the first row.
    """
    # Import lazily to avoid hard dependency at import time
    from PyQt6.QtWidgets import QTableWidget

    assert isinstance(table, QTableWidget)
    row_count = table.rowCount()
    col_count = table.columnCount()

    with open(path, "w", encoding=encoding, newline="") as f:
        # headers
        headers = []
        for c in range(col_count):
            hi = table.horizontalHeaderItem(c)
            headers.append(hi.text() if hi else f"Column {c+1}")
        f.write(",".join(headers) + "\n")
        # rows
        for r in range(row_count):
            row = []
            for c in range(col_count):
                it = table.item(r, c)
                row.append((it.text() if it else "").replace(",", ";"))
            f.write(",".join(row) + "\n")


def build_qtablewidget_html(table, title: str, subtitle: Optional[str] = None, summary_text: str = "") -> str:
    """Build an HTML document from a QTableWidget contents with optional title/subtitle/summary."""
    from PyQt6.QtWidgets import QTableWidget

    assert isinstance(table, QTableWidget)
    col_count = table.columnCount()
    row_count = table.rowCount()

    parts = [f"<h2 style=\"text-align:center;\">{title}</h2>"]
    if subtitle:
        parts.append(f"<p style=\"text-align:center;\">{subtitle}</p>")
    parts.append("<br>")
    parts.append("<table border=\"1\" cellspacing=\"0\" cellpadding=\"10\" width=\"100%\"><thead><tr style=\"background-color:#f3f4f6;\">")
    for c in range(col_count):
        hi = table.horizontalHeaderItem(c)
        parts.append(f"<th align=\"center\">{hi.text() if hi else f'Column {c+1}'}</th>")
    parts.append("</tr></thead><tbody>")
    for r in range(row_count):
        parts.append("<tr>")
        for c in range(col_count):
            it = table.item(r, c)
            parts.append(f"<td align=\"center\">{(it.text() if it else '')}</td>")
        parts.append("</tr>")
    parts.append("</tbody></table>")
    if summary_text:
        parts.append(f"<br><p style=\"text-align:center; font-weight:bold;\">{summary_text}</p>")
    return "".join(parts)

