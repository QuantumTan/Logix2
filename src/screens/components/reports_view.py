# screens/components/reports_view.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QFrame, QScrollArea, QTableWidget, QHeaderView
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class ReportsView(QScrollArea):
    """Encapsulated Reports tab UI. Owner wires logic and data fetch/plot.

    Exposes attributes used by the owner (DashboardBase):
    - period_combo, reports_chart_header, chart_container_layout, reports_chart (None initially),
      _reports_placeholder, selected_emp_label, indiv_view_combo, indiv_table, indiv_summary_label
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)

        self.main_widget = QWidget()
        layout = QVBoxLayout(self.main_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Period selector and export buttons (buttons wired by owner)
        period_layout = QHBoxLayout()
        self.report_period = "daily"
        self.period_combo = QComboBox()
        self.period_combo.addItems(["Daily", "Weekly", "Monthly", "Yearly"])
        period_layout.addWidget(QLabel("Period:"))
        period_layout.addWidget(self.period_combo)
        period_layout.addStretch()

        self.export_csv_btn = QPushButton("Export CSV")
        self.export_csv_btn.setFixedHeight(35)
        self.export_csv_btn.setStyleSheet("QPushButton { background-color: #10b981; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold; }")
        self.export_pdf_btn = QPushButton("Export PDF")
        self.export_pdf_btn.setFixedHeight(35)
        self.export_pdf_btn.setStyleSheet("QPushButton { background-color: #ef4444; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold; }")

        period_layout.addWidget(self.export_csv_btn)
        period_layout.addWidget(self.export_pdf_btn)
        layout.addLayout(period_layout)

        # Chart header
        self.reports_chart_header = QLabel("📊 Daily Attendance Report")
        self.reports_chart_header.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        self.reports_chart_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.reports_chart_header.setStyleSheet("color: #1f2937; margin: 10px 0; padding: 10px; background: #f9fafb; border-radius: 8px;")
        layout.addWidget(self.reports_chart_header)

        # Chart container with fixed height
        chart_container = QFrame()
        chart_container.setFrameStyle(QFrame.Shape.Box)
        chart_container.setStyleSheet("QFrame { border: 2px solid #e5e7eb; border-radius: 8px; background: white; }")
        chart_container.setMinimumHeight(500)
        chart_container.setMaximumHeight(600)

        chart_layout = QVBoxLayout(chart_container)
        chart_layout.setContentsMargins(10, 10, 10, 10)

        self.reports_chart = None
        self._reports_placeholder = QLabel("📊 Chart will load when you switch to Reports tab")
        self._reports_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._reports_placeholder.setStyleSheet("color: #6b7280; font-size: 16px; padding: 40px;")
        chart_layout.addWidget(self._reports_placeholder)

        layout.addWidget(chart_container)
        self.chart_container_layout = chart_layout

        # Individual Employee Working Hours Section (search removed)
        indiv_header = QLabel("👤 Individual Employee Working Hours")
        indiv_header.setFont(QFont("Inter", 16, QFont.Weight.Bold))
        indiv_header.setAlignment(Qt.AlignmentFlag.AlignLeft)
        indiv_header.setStyleSheet("color: #1f2937; margin-top: 20px; margin-bottom: 10px; padding: 10px; background: #f9fafb; border-radius: 8px;")
        layout.addWidget(indiv_header)

        indiv_controls = QHBoxLayout()
        # Only keep the view selector; employee search removed
        indiv_controls.addStretch()
        indiv_controls.addWidget(QLabel("View:"))
        self.indiv_view_combo = QComboBox()
        self.indiv_view_combo.addItems(["Monthly", "Yearly"])
        self.indiv_view_combo.setFixedHeight(40)
        indiv_controls.addWidget(self.indiv_view_combo)
        layout.addLayout(indiv_controls)

        self.selected_emp_label = QLabel("No employee selected - showing all employees")
        self.selected_emp_label.setStyleSheet("color: #374151; font-weight: bold; padding: 8px; background: #f9fafb; border-radius: 6px;")
        layout.addWidget(self.selected_emp_label)

        # Individual export buttons (wired by owner)
        indiv_export_layout = QHBoxLayout()
        indiv_export_layout.addStretch()
        self.indiv_export_csv_btn = QPushButton("Export Individual Hours CSV")
        self.indiv_export_csv_btn.setFixedHeight(35)
        self.indiv_export_csv_btn.setStyleSheet("QPushButton { background-color: #10b981; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold; }")
        self.indiv_export_pdf_btn = QPushButton("Export Individual Hours PDF")
        self.indiv_export_pdf_btn.setFixedHeight(35)
        self.indiv_export_pdf_btn.setStyleSheet("QPushButton { background-color: #ef4444; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold; }")
        indiv_export_layout.addWidget(self.indiv_export_csv_btn)
        indiv_export_layout.addWidget(self.indiv_export_pdf_btn)
        layout.addLayout(indiv_export_layout)

        # Employee hours table
        table_container = QFrame()
        table_container.setFrameStyle(QFrame.Shape.Box)
        table_container.setStyleSheet("QFrame { border: 2px solid #e5e7eb; border-radius: 8px; background: white; }")
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(10, 10, 10, 10)

        self.indiv_table = QTableWidget()
        self.indiv_table.setColumnCount(6)
        self.indiv_table.setHorizontalHeaderLabels([
            "Employee Name",
            "Total Hours",
            "Average Daily Hours",
            "Total Absences",
            "Attendance %",
            "Overtime Hours",
        ])
        self.indiv_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.indiv_table.setMinimumHeight(250)
        self.indiv_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.indiv_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.indiv_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.indiv_table.setAlternatingRowColors(True)
        self.indiv_table.setStyleSheet(
            """
            QTableWidget { gridline-color: #e5e7eb; background: white; selection-background-color: transparent; selection-color: inherit; }
            QTableWidget::item { border: none; padding: 8px; }
            QTableWidget::item:selected { background-color: transparent; color: inherit; }
            QHeaderView::section { background: #f3f4f6; padding: 8px; border: 1px solid #e5e7eb; font-weight: bold; }
            """
        )

        table_layout.addWidget(self.indiv_table)
        layout.addWidget(table_container)

        self.indiv_summary_label = QLabel("Total: 0 hours")
        self.indiv_summary_label.setStyleSheet("color: #1f2937; font-size: 14px; font-weight: bold; padding: 10px; background: #f0f9ff; border-radius: 6px;")
        layout.addWidget(self.indiv_summary_label)

        self.setWidget(self.main_widget)
# screens/components/attendance_view.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QTableWidget, QHeaderView


class AttendanceView(QWidget):
    """Encapsulated Attendance tab UI. Owner wires signals/slots and data."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Search attendance...")
        self.search_edit.setFixedHeight(35)
        self.search_edit.setStyleSheet(
            """
            QLineEdit {
                background-color: white;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                color: #374151;
            }
            QLineEdit:focus {
                border-color: #06b6d4;
            }
            """
        )
        layout.addWidget(self.search_edit)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Employee ID",
            "Employee Name",
            "Check In",
            "Check Out",
            "Status",
            "Action",
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)
