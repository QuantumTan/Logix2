# screens/base_dashboard.py
import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QSizePolicy, QStackedWidget,
    QFileDialog, QMessageBox, QInputDialog, QComboBox, QScrollArea, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, QTimer, QTime, QDate
from PyQt6.QtGui import QFont, QPixmap, QPainter, QPageLayout, QPageSize, QPdfWriter

from ..database.db_queries import get_all_employees, get_employee_details, get_department_attendance, update_employee, delete_employee, get_today_attendance, get_today_stats
import os
import shutil

MATPLOTLIB_AVAILABLE = False


def _matplotlib_disabled_by_env() -> bool:
    return os.environ.get("LOGIX_DISABLE_CHARTS", "0").strip() in {"1", "true", "True", "yes", "on"}


#shared chart widget for reports
class ReportsChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.figure = None
        self.canvas = None

        if _matplotlib_disabled_by_env():
            self._create_fallback_widget(layout)
            return

        # try to import matplotlib lazily here, and handle any failures gracefully
        global MATPLOTLIB_AVAILABLE
        try:
            from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas  # type: ignore
            from matplotlib.figure import Figure  # type: ignore
            import matplotlib.pyplot as plt  # type: ignore
            self._FigureCanvas = FigureCanvas
            self._Figure = Figure
            self._plt = plt
            MATPLOTLIB_AVAILABLE = True
        except Exception as e:
            print(f"Matplotlib not available or failed to initialize: {e}")
            MATPLOTLIB_AVAILABLE = False
            self._FigureCanvas = None
            self._Figure = None
            self._plt = None

        if MATPLOTLIB_AVAILABLE and self._Figure and self._FigureCanvas:
            try:
                # Remove tight_layout=True and increase figure size to prevent layout warnings
                self.figure = self._Figure(figsize=(12, 8))
                self.canvas = self._FigureCanvas(self.figure)
                layout.addWidget(self.canvas)
                # Load static data immediately
                self.load_static_demo_data()
            except Exception as e:
                print(f"Chart widget creation failed: {e}")
                self.figure = None
                self.canvas = None
                self._create_fallback_widget(layout)
        else:
            self._create_fallback_widget(layout)

    #shows an error message if matplotlib is not available funtion:
    def _create_fallback_widget(self, layout):
        """Create fallback widget when matplotlib is not available"""
        lbl = QLabel("📊 Charts require matplotlib\nInstall with: pip install matplotlib")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("color:#6b7280; font-size: 14px; padding: 40px; background: white; border-radius: 8px;")
        layout.addWidget(lbl)

    def load_static_demo_data(self):
        """Load comprehensive static demo data for charts with 2x2 layout"""
        try:
            if not MATPLOTLIB_AVAILABLE or not self.canvas or not self.figure:
                return

            # Create a simple demo chart to show the chart is working
            self.figure.clear()
            ax = self.figure.add_subplot(111)

            # Sample data for demonstration
            departments = ['IT', 'HR', 'Finance', 'Operations']
            present = [25, 15, 20, 30]
            late = [5, 3, 4, 8]
            absent = [2, 4, 1, 3]

            # Grouped bar chart positions
            x = list(range(len(departments)))
            width = 0.25
            x_present = [i - width for i in x]
            x_late = x
            x_absent = [i + width for i in x]

            ax.bar(x_present, present, width=width, color="#10b981", label="Present", alpha=0.9)
            ax.bar(x_late, late, width=width, color="#f59e0b", label="Late", alpha=0.9)
            ax.bar(x_absent, absent, width=width, color="#ef4444", label="Absent", alpha=0.9)

            ax.set_xticks(x)
            ax.set_xticklabels(departments)
            ax.set_title('Sample Attendance Report', fontweight='bold')
            ax.set_ylabel('Number of Employees')
            ax.grid(True, axis='y', linestyle='--', alpha=0.3)
            ax.legend()

            # Adjust layout manually to prevent tight_layout warnings
            self.figure.subplots_adjust(left=0.1, bottom=0.15, right=0.9, top=0.9)
            self.canvas.draw()

        except Exception as e:
            print(f"Failed to load demo chart data: {e}")

    def plot(self, labels: list[str], present: list[int], late: list[int], absent: list[int], title: str):
        """Plot method for dynamic data with grouped bars for Present, Late, Absent"""
        try:
            if not MATPLOTLIB_AVAILABLE or not self.canvas or not self.figure:
                return

            # Normalize lengths to avoid index errors
            n = min(len(labels), len(present), len(late), len(absent))
            labels = labels[:n]
            present = [int(p or 0) for p in present[:n]]
            late = [int(l or 0) for l in late[:n]]
            absent = [int(a or 0) for a in absent[:n]]

            # Clear and create single plot
            self.figure.clear()
            ax = self.figure.add_subplot(111)

            x = list(range(len(labels)))
            width = 0.25 if len(labels) > 0 else 0.25

            x_present = [i - width for i in x]
            x_late = x
            x_absent = [i + width for i in x]

            ax.bar(x_present, present, width=width, color="#10b981", label="Present", alpha=0.9)
            ax.bar(x_late, late, width=width, color="#f59e0b", label="Late", alpha=0.9)
            ax.bar(x_absent, absent, width=width, color="#ef4444", label="Absent", alpha=0.9)

            ax.set_xticks(x)
            ax.set_xticklabels(labels, rotation=0 if len(labels) <= 6 else 20, ha='right')
            ax.set_title(title, fontweight='bold')
            ax.set_ylabel('Number of Employees')
            ax.grid(True, axis='y', linestyle='--', alpha=0.3)
            ax.legend()

            # Adjust layout manually to prevent tight_layout warnings
            self.figure.subplots_adjust(left=0.1, bottom=0.2 if len(labels) > 6 else 0.15, right=0.95, top=0.9)
            self.canvas.draw()

        except Exception as e:
            print(f"Chart plotting failed: {e}")

    def closeEvent(self, event):
        """clean up matplotlib resources to prevent memory issues"""
        try:
            if getattr(self, '_plt', None) is not None and getattr(self, 'figure', None) is not None:
                # Close the specific figure to release backend resources
                self._plt.close(self.figure)
        except Exception as e:
            print(f"Error closing ReportsChartWidget: {e}")
        super().closeEvent(event)


class DashboardBase(QWidget):
    def __init__(self, title_suffix="Dashboard"):
        super().__init__()
        self.setWindowTitle(f"LOGIX - {title_suffix}")
        self.setGeometry(200, 100, 1500, 900)
        self.current_tab = "attendance"
        self.employee_data = {}
        self.attendance_rows: list[dict] = []
        self.load_employee_data()
        # Enable charts by default; guarded with try/except and internal fallbacks
        self.enable_charts = True

        self.inactive_style = "QPushButton { background-color: white; color: #f87171; padding: 5px 30px; border-radius: 15px; font-weight: bold; border: 2px solid #f87171; height: 30px; } QPushButton:hover { background-color: #fef2f2; }"
        self.active_style = "QPushButton { background-color: #f87171; color: white; padding: 5px 30px; border-radius: 15px; font-weight: bold; border: 2px solid #f87171; height: 30px; } QPushButton:hover { background-color: #ef4444; }"

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        # === Top Header with Gradient Background ===
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(
                    spread:pad,
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #60a5fa,
                    stop:1 #fca5a5
                );
                border-radius: 8px;
                padding: 12px;
            }
        """)
        header_layout = QHBoxLayout()

        # Left Logo + Title
        logo = QLabel()
        pixmap = QPixmap("assets/logix.png")
        logo.setStyleSheet("background-color: transparent;")
        pixmap = pixmap.scaled(90, 90, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        logo.setPixmap(pixmap)

        title = QLabel("LOGIX\nAttendance Monitoring System")
        title.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: white; margin-left: 10px; background-color: transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        left_layout = QHBoxLayout()
        left_layout.addWidget(logo)
        left_layout.addWidget(title)

        # Right side (Date on the left, buttons vertically aligned on the right)
        right_layout = QHBoxLayout()

        # Date layout
        date_layout = QVBoxLayout()
        today_label = QLabel("Today")
        today_label.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        today_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        today_label.setStyleSheet("color: white; background-color: transparent;")

        self.date_label = QLabel(QDate.currentDate().toString("MMMM d, yyyy"))
        self.date_label.setFont(QFont("Inter", 12))
        self.date_label.setStyleSheet("color: white; background-color: transparent;")

        date_layout.addWidget(today_label)
        date_layout.addWidget(self.date_label)

        # Top-right Logout button for Admin/Staff dashboards
        self.logout_btn = QPushButton("Logout")
        self.logout_btn.setStyleSheet("""
        background-color: #ef4444; color: white; padding: 8px 16px; border-radius: 8px; font-weight: bold;
        """)
        self.logout_btn.setFixedWidth(100)

        right_layout.addLayout(date_layout)
        right_layout.addStretch()
        right_layout.addWidget(self.logout_btn)

        header_layout.addLayout(left_layout)
        header_layout.addStretch()
        header_layout.addLayout(right_layout)

        header_frame.setLayout(header_layout)
        main_layout.addWidget(header_frame)

        # === Stats Layout ===
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)

        self.time_label = QLabel("Current Time\n--:--:-- --")
        self.time_label.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setStyleSheet("background: #eff6ff; color: #3b82f6; font-size: 16px; padding: 20px; border-radius: 10px;")
        self.time_label.setFixedHeight(160)

        # Stat Cards (label top left, number bottom right)
        self.present_card, self.present_number = self.create_stat_card(0, "Present", "#dcfce7", "green")
        self.late_card, self.late_number = self.create_stat_card(0, "Late", "#fef3c7", "orange")
        self.absent_card, self.absent_number = self.create_stat_card(0, "Absent", "#fee2e2", "red")

        stats_layout.addWidget(self.time_label)
        stats_layout.addWidget(self.present_card)
        stats_layout.addWidget(self.late_card)
        stats_layout.addWidget(self.absent_card)

        main_layout.addLayout(stats_layout)

        # === Tabs Layout ===
        tabs_layout = QHBoxLayout()
        self.tabs_layout = tabs_layout
        tabs_layout.setSpacing(15)

        # Center the tab buttons by adding stretch on both sides
        tabs_layout.addStretch()

        attendance_btn = QPushButton("Attendance")
        attendance_btn.setStyleSheet(self.active_style)
        attendance_btn.clicked.connect(lambda: self.switch_tab("attendance"))

        employee_mgmt_btn = QPushButton("Employee Management")
        employee_mgmt_btn.setStyleSheet(self.inactive_style)
        employee_mgmt_btn.clicked.connect(lambda: self.switch_tab("employee_management"))

        reports_btn = QPushButton("Reports")
        reports_btn.setStyleSheet(self.inactive_style)
        reports_btn.clicked.connect(lambda: self.switch_tab("reports"))

        tabs_layout.addWidget(attendance_btn)
        tabs_layout.addWidget(employee_mgmt_btn)
        tabs_layout.addWidget(reports_btn)

        tabs_layout.addStretch()

        main_layout.addLayout(tabs_layout)

        self.tab_buttons = {
            "attendance": attendance_btn,
            "employee_management": employee_mgmt_btn,
            "reports": reports_btn
        }

        main_layout.addSpacing(10)

        # Content stack
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack)

        self.setLayout(main_layout)

        # Timer to update time
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start()

        # Setup common pages
        self.setup_attendance_page()
        self.setup_employee_management_page()
        self.setup_reports_page()

        # Initial stats update
        self.update_stats()

        # Periodic attendance refresh (no event bus)
        self.attendance_refresh_timer = QTimer(self)
        self.attendance_refresh_timer.setInterval(3000)
        self.attendance_refresh_timer.timeout.connect(lambda: [self.refresh_attendance_view(), self.update_stats()])
        self.attendance_refresh_timer.start()

        # Reports tab auto-refresh timer - disabled for new reports screen
        self.reports_refresh_timer = QTimer(self)
        self.reports_refresh_timer.setInterval(10000)  # 10 seconds
        self.reports_refresh_timer.timeout.connect(self.update_reports_view)  # Remove parameter dependency

        # Switch to default tab
        self.switch_tab("attendance")

    def create_stat_card(self, number, label_text, bg_color, fg_color):
        card = QFrame()
        card.setStyleSheet(f"background: {bg_color}; border-radius: 10px; margin-top: 20px; margin-bottom: 20px;")
        card.setFixedHeight(200)
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(0)

        text_label = QLabel(label_text)
        text_label.setFont(QFont("Inter", 10, QFont.Weight.Bold))
        text_label.setStyleSheet(f"color: {fg_color}; margin: 10px")
        text_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        number_label = QLabel(str(number))
        number_label.setFont(QFont("Inter", 16, QFont.Weight.Bold))
        number_label.setStyleSheet(f"color: {fg_color}; margin: 10px;")
        number_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)

        layout.addWidget(text_label)
        layout.addStretch(1)
        layout.addWidget(number_label)
        card.setLayout(layout)
        return card, number_label

    def update_stats(self):
        stats = get_today_stats()
        self.present_number.setText(str(stats.get('present', 0)))
        self.late_number.setText(str(stats.get('late', 0)))
        self.absent_number.setText(str(stats.get('absent', 0)))

    def update_time(self):
        current_time = QTime.currentTime().toString("hh:mm:ss AP")
        self.time_label.setText(f"Current Time\n{current_time}")

    def setup_attendance_page(self):
        if hasattr(self, 'attendance_page') and self.attendance_page is not None:
            return
        self.attendance_page = QWidget()
        attendance_layout = QVBoxLayout(self.attendance_page)

        self.attendance_search = QLineEdit()
        self.attendance_search.setPlaceholderText("🔍 Search attendance...")
        self.attendance_search.setFixedHeight(35)
        self.attendance_search.setStyleSheet("""
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
        """)
        self.attendance_search.textChanged.connect(self.filter_attendance_table)
        attendance_layout.addWidget(self.attendance_search)

        # Use exact same table setup as employee_dashboard
        self.attendance_table = QTableWidget()
        self.attendance_table.setColumnCount(6)
        self.attendance_table.setHorizontalHeaderLabels(["Employee ID", "Employee Name", "Check In", "Check Out", "Status", "Action"])
        self.attendance_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.attendance_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        attendance_layout.addWidget(self.attendance_table)
        self.content_stack.addWidget(self.attendance_page)

        # Initial load
        self.refresh_attendance_view()

    def refresh_attendance_view(self):
        try:
            self.attendance_rows = get_today_attendance() or []
        except Exception as e:
            print(f"Failed to load attendance: {e}")
            self.attendance_rows = []
        # Apply current filter
        query = self.attendance_search.text() if hasattr(self, 'attendance_search') else ""
        self.filter_attendance_table(query)

    def filter_attendance_table(self, text):
        text = (text or "").lower()
        rows = [
            row for row in self.attendance_rows
            if text in (row.get('full_name', '') or '').lower()
            or text in str(row.get('employee_id', '')).lower()
        ]
        self.attendance_table.setRowCount(len(rows))
        for r, data in enumerate(rows):
            self.attendance_table.setItem(r, 0, QTableWidgetItem(str(data.get('employee_id', ''))))
            self.attendance_table.setItem(r, 1, QTableWidgetItem(data.get('full_name', '')))
            self.attendance_table.setItem(r, 2, QTableWidgetItem(data.get('check_in', '--')))
            self.attendance_table.setItem(r, 3, QTableWidgetItem(data.get('check_out', '--')))
            self.attendance_table.setItem(r, 4, QTableWidgetItem(data.get('status', '')))

            view_btn = QPushButton("VIEW")
            view_btn.setStyleSheet("background-color: #f87171; color: white; padding: 5px; border-radius: 6px; margin: 2px;")
            emp_id = data.get('employee_id', '')
            view_btn.clicked.connect(lambda checked=False, eid=emp_id: self.show_employee_details(eid))
            self.attendance_table.setCellWidget(r, 5, view_btn)

    def show_employee_details(self, emp_id):
        # Placeholder - implement in child classes
        pass

    def setup_employee_management_page(self):
        if hasattr(self, 'employee_management_page') and self.employee_management_page is not None:
            return
        self.employee_management_page = QWidget()
        emp_layout = QVBoxLayout(self.employee_management_page)

        # === Add Employee button (top-right) ===
        top_btn_layout = QHBoxLayout()
        top_btn_layout.addStretch()  # pushes button to the right
        self.add_emp_btn = QPushButton("Add Employee")
        self.add_emp_btn.setStyleSheet(
            "QPushButton {background:#06b6d4;color:white;padding:8px 16px;"
            "border-radius:8px;font-weight:bold;}"
        )
        self.add_emp_btn.clicked.connect(self.handle_add_employee)
        top_btn_layout.addWidget(self.add_emp_btn, alignment=Qt.AlignmentFlag.AlignRight)
        emp_layout.addLayout(top_btn_layout)

        # === Search bar (full width below button) ===
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍 Search employee...")
        self.search.setFixedHeight(35)
        self.search.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                color: #374151;
            }
            QLineEdit:focus {
                border-color: #60a5fa;
                outline: none;
            }
        """)
        self.search.textChanged.connect(self.filter_employee_table)
        emp_layout.addWidget(self.search)

        # === Employee Table ===
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Employee ID", "Name", "Position", "Department", "Absences", "Leave Credits", "Actions"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        emp_layout.addWidget(self.table)
        self.content_stack.addWidget(self.employee_management_page)

        # Load employee data into table
        self.load_employee_table()

    def load_employee_table(self):
        self.load_employee_data()
        self.table.setRowCount(len(self.employee_data))
        keys = list(self.employee_data.keys())
        for row in range(len(keys)):
            emp_id = keys[row]
            emp = self.employee_data[emp_id]
            self.table.setItem(row, 0, QTableWidgetItem(str(emp['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(emp['name']))
            self.table.setItem(row, 2, QTableWidgetItem(emp['position']))
            self.table.setItem(row, 3, QTableWidgetItem(emp['department']))
            self.table.setItem(row, 4, QTableWidgetItem(str(emp['absences'])))
            self.table.setItem(row, 5, QTableWidgetItem(str(emp['leave_credits'])))

            # Action cell
            action_widget = QWidget()
            h = QHBoxLayout(action_widget)
            h.setContentsMargins(0, 0, 0, 0)
            h.setSpacing(4)

            edit_btn = QPushButton("Edit")
            edit_btn.setStyleSheet("QPushButton{background:#60a5fa;color:white;padding:4px 8px;border-radius:6px;font-size:10px;}")
            edit_btn.setFixedWidth(80)

            delete_btn = QPushButton("Delete")
            delete_btn.setStyleSheet("QPushButton{background:#ef4444;color:white;padding:4px 8px;border-radius:6px;font-size:10px;}")
            delete_btn.setFixedWidth(80)

            leave_btn = QPushButton("Edit Leave")
            leave_btn.setStyleSheet("QPushButton{background:#f59e0b;color:white;padding:4px 8px;border-radius:6px;font-size:10px;}")
            leave_btn.setFixedWidth(80)

            edit_btn.clicked.connect(lambda checked, eid=emp_id: self.handle_edit_employee(eid))
            delete_btn.clicked.connect(lambda checked, eid=emp_id: self.handle_delete_employee(eid))
            leave_btn.clicked.connect(lambda checked, eid=emp_id: self.handle_edit_leave(eid))

            h.addWidget(edit_btn)
            h.addWidget(delete_btn)
            h.addWidget(leave_btn)
            h.addStretch()
            self.table.setCellWidget(row, 6, action_widget)  # Note: Column 5 is "Action", but labels have 6 columns (0-5)

    def filter_employee_table(self, text: str):
        text = (text or '').lower()
        row = 0
        for emp_id, emp in self.employee_data.items():
            id_match = text in str(emp['id']).lower()
            name_match = text in (emp['name'] or '').lower()
            pos_match = text in (emp['position'] or '').lower()
            dept_match = text in (emp['department'] or '').lower()
            if id_match or name_match or pos_match or dept_match:
                self.table.setRowHidden(row, False)
            else:
                self.table.setRowHidden(row, True)
            row += 1

    def handle_add_employee(self):
        # Placeholder - implement in child classes
        pass

    def handle_edit_employee(self, emp_id):
        # Placeholder - implement in child classes
        pass

    def handle_delete_employee(self, emp_id):
        # Placeholder - implement in child classes
        pass

    def handle_edit_leave(self, emp_id):
        # Placeholder - implement in child classes
        pass

    def setup_reports_page(self):
        if hasattr(self, 'reports_page') and self.reports_page is not None:
            return

        # Create a main widget that will contain everything
        self.reports_main_widget = QWidget()
        reports_layout = QVBoxLayout(self.reports_main_widget)
        reports_layout.setSpacing(20)
        reports_layout.setContentsMargins(20, 20, 20, 20)

        # Period selector and export buttons
        period_layout = QHBoxLayout()
        self.report_period = "daily"
        self.period_combo = QComboBox()
        self.period_combo.addItems(["Daily", "Weekly", "Monthly", "Yearly"])
        self.period_combo.currentTextChanged.connect(self.update_reports_view)
        period_layout.addWidget(QLabel("Period:"))
        period_layout.addWidget(self.period_combo)
        period_layout.addStretch()

        # Export buttons
        csv_btn = QPushButton("Export CSV")
        csv_btn.clicked.connect(self.export_report_csv)
        csv_btn.setFixedHeight(35)
        csv_btn.setStyleSheet("QPushButton { background-color: #10b981; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold; }")

        pdf_btn = QPushButton("Export PDF")
        pdf_btn.clicked.connect(self.export_report_pdf)
        pdf_btn.setFixedHeight(35)
        pdf_btn.setStyleSheet("QPushButton { background-color: #ef4444; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold; }")

        period_layout.addWidget(csv_btn)
        period_layout.addWidget(pdf_btn)
        reports_layout.addLayout(period_layout)

        # Chart header
        self.reports_chart_header = QLabel("📊 Daily Attendance Report")
        self.reports_chart_header.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        self.reports_chart_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.reports_chart_header.setStyleSheet("color: #1f2937; margin: 10px 0; padding: 10px; background: #f9fafb; border-radius: 8px;")
        reports_layout.addWidget(self.reports_chart_header)

        # Chart container with fixed height and proper sizing
        chart_container = QFrame()
        chart_container.setFrameStyle(QFrame.Shape.Box)
        chart_container.setStyleSheet("QFrame { border: 2px solid #e5e7eb; border-radius: 8px; background: white; }")
        chart_container.setMinimumHeight(500)  # Ensure minimum height for chart
        chart_container.setMaximumHeight(600)  # Prevent it from getting too large

        chart_layout = QVBoxLayout(chart_container)
        chart_layout.setContentsMargins(10, 10, 10, 10)

        # Initialize chart or placeholder
        self.reports_chart = None
        self._reports_placeholder = QLabel("📊 Chart will load when you switch to Reports tab")
        self._reports_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._reports_placeholder.setStyleSheet("color: #6b7280; font-size: 16px; padding: 40px;")
        chart_layout.addWidget(self._reports_placeholder)

        reports_layout.addWidget(chart_container)
        # Keep reference for later chart insertion
        self.chart_container_layout = chart_layout

        # Individual Employee Working Hours Section
        indiv_header = QLabel("👤 Individual Employee Working Hours")
        indiv_header.setFont(QFont("Inter", 16, QFont.Weight.Bold))
        indiv_header.setAlignment(Qt.AlignmentFlag.AlignLeft)
        indiv_header.setStyleSheet("color: #1f2937; margin-top: 20px; margin-bottom: 10px; padding: 10px; background: #f9fafb; border-radius: 8px;")
        reports_layout.addWidget(indiv_header)

        # Employee search and view controls
        indiv_controls = QHBoxLayout()
        self.indiv_search_input = QLineEdit()
        self.indiv_search_input.setPlaceholderText("🔍 Search employee by ID or name...")
        self.indiv_search_input.setFixedHeight(40)
        self.indiv_search_input.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                color: #374151;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
            }
        """)
        self.indiv_search_input.textChanged.connect(self._on_indiv_search_text_changed)

        indiv_controls.addWidget(QLabel("Employee:"))
        indiv_controls.addWidget(self.indiv_search_input, stretch=1)

        indiv_controls.addSpacing(20)
        indiv_controls.addWidget(QLabel("View:"))
        self.indiv_view_combo = QComboBox()
        self.indiv_view_combo.addItems(["Monthly", "Yearly"])
        self.indiv_view_combo.setFixedHeight(40)
        self.indiv_view_combo.currentTextChanged.connect(self._on_indiv_selection_changed)
        indiv_controls.addWidget(self.indiv_view_combo)

        reports_layout.addLayout(indiv_controls)

        # Debounced search setup
        self.indiv_search_timer = QTimer(self)
        self.indiv_search_timer.setSingleShot(True)
        self.indiv_search_timer.setInterval(300)
        self.indiv_search_timer.timeout.connect(self._perform_indiv_search)

        # Search results list
        self.indiv_results = QListWidget()
        self.indiv_results.setMaximumHeight(120)
        self.indiv_results.setStyleSheet("""
            QListWidget {
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                background: white;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f3f4f6;
            }
            QListWidget::item:hover {
                background: #f3f4f6;
            }
            QListWidget::item:selected {
                background: #3b82f6;
                color: white;
            }
        """)
        self.indiv_results.itemClicked.connect(self._on_indiv_result_clicked)
        reports_layout.addWidget(self.indiv_results)

        # Selected employee label
        self.selected_emp_label = QLabel("No employee selected - showing all employees")
        self.selected_emp_label.setStyleSheet("color: #374151; font-weight: bold; padding: 8px; background: #f9fafb; border-radius: 6px;")
        reports_layout.addWidget(self.selected_emp_label)

        # Individual export buttons
        indiv_export_layout = QHBoxLayout()
        indiv_export_layout.addStretch()

        indiv_csv_btn = QPushButton("Export Individual Hours CSV")
        indiv_csv_btn.clicked.connect(self.export_individual_hours_csv)
        indiv_csv_btn.setFixedHeight(35)
        indiv_csv_btn.setStyleSheet("QPushButton { background-color: #10b981; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold; }")

        indiv_pdf_btn = QPushButton("Export Individual Hours PDF")
        indiv_pdf_btn.clicked.connect(self.export_individual_hours_pdf)
        indiv_pdf_btn.setFixedHeight(35)
        indiv_pdf_btn.setStyleSheet("QPushButton { background-color: #ef4444; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold; }")

        indiv_export_layout.addWidget(indiv_csv_btn)
        indiv_export_layout.addWidget(indiv_pdf_btn)
        reports_layout.addLayout(indiv_export_layout)

        # Employee hours table in a scrollable container
        table_container = QFrame()
        table_container.setFrameStyle(QFrame.Shape.Box)
        table_container.setStyleSheet("QFrame { border: 2px solid #e5e7eb; border-radius: 8px; background: white; }")
        table_container.setMinimumHeight(300)

        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(10, 10, 10, 10)

        self.indiv_table = QTableWidget()
        self.indiv_table.setColumnCount(6)
        self.indiv_table.setHorizontalHeaderLabels([
            "Employee Name", "Total Hours", "Average Daily Hours",
            "Total Absences", "Attendance %", "Overtime Hours"
        ])
        self.indiv_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.indiv_table.setMinimumHeight(250)
        self.indiv_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.indiv_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.indiv_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.indiv_table.setAlternatingRowColors(True)
        self.indiv_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #e5e7eb;
                background: white;
                selection-background-color: transparent;
                selection-color: inherit;
            }
            QTableWidget::item {
                border: none;
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: transparent;
                color: inherit;
            }
            QHeaderView::section {
                background: #f3f4f6;
                padding: 8px;
                border: 1px solid #e5e7eb;
                font-weight: bold;
            }
        """)

        table_layout.addWidget(self.indiv_table)
        reports_layout.addWidget(table_container)

        # Summary label
        self.indiv_summary_label = QLabel("Total: 0 hours")
        self.indiv_summary_label.setStyleSheet("color: #1f2937; font-size: 14px; font-weight: bold; padding: 10px; background: #f0f9ff; border-radius: 6px;")
        reports_layout.addWidget(self.indiv_summary_label)

        # Create scroll area for the entire reports page
        self.reports_scroll = QScrollArea()
        self.reports_scroll.setWidgetResizable(True)
        self.reports_scroll.setWidget(self.reports_main_widget)
        self.reports_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.reports_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.reports_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: #f9fafb;
            }
            QScrollBar:vertical {
                background: #f3f4f6;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #9ca3af;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #6b7280;
            }
        """)

        self.content_stack.addWidget(self.reports_scroll)

        # Internal state for selected employee
        self._selected_emp_id = None

    def switch_tab(self, tab_name):
        if tab_name == self.current_tab:
            return

        # Reset previous button
        prev_btn = self.tab_buttons[self.current_tab]
        prev_btn.setStyleSheet(self.inactive_style)

        # Activate new button
        new_btn = self.tab_buttons[tab_name]
        new_btn.setStyleSheet(self.active_style)

        # Switch content
        if tab_name == "attendance":
            self.content_stack.setCurrentWidget(self.attendance_page)
            self.reports_refresh_timer.stop()
        elif tab_name == "employee_management":
            self.content_stack.setCurrentWidget(self.employee_management_page)
            self.reports_refresh_timer.stop()
        elif tab_name == "reports":
            # Create chart lazily and safely
            try:
                self._ensure_reports_chart()
            except Exception as e:
                print(f"Chart init error: {e}")
            self.content_stack.setCurrentWidget(self.reports_scroll)
            # Do not force reset to Daily; refresh using current selection/state
            self.update_reports_view()
            self.reports_refresh_timer.start()

        self.current_tab = tab_name

    def _ensure_reports_chart(self):
        """Replace the placeholder with a chart widget lazily."""
        try:
            if self.reports_chart is None and hasattr(self, 'chart_container_layout'):
                if getattr(self, '_reports_placeholder', None) is not None:
                    self.chart_container_layout.removeWidget(self._reports_placeholder)
                    self._reports_placeholder.deleteLater()
                    self._reports_placeholder = None

                # Create the chart widget with proper sizing
                self.reports_chart = ReportsChartWidget()
                self.reports_chart.setMinimumHeight(450)
                self.reports_chart.setMaximumHeight(550)
                self.chart_container_layout.addWidget(self.reports_chart)

                print("Chart widget created and added to layout")
        except Exception as e:
            print(f"Failed to create reports chart: {e}")
            self.reports_chart = None

    def _on_indiv_search_text_changed(self, _text: str):
        # Debounce frequent queries
        if self.indiv_search_timer.isActive():
            self.indiv_search_timer.stop()
        self.indiv_search_timer.start()

    def _perform_indiv_search(self):
        try:
            from ..database.db_queries import search_employees
            q = self.indiv_search_input.text().strip()
            self.indiv_results.clear()
            if not q:
                return
            rows = search_employees(q, limit=50) or []
            for r in rows:
                item = QListWidgetItem(f"{r['full_name']} ({r['employee_id']})")
                item.setData(Qt.ItemDataRole.UserRole, r['employee_id'])
                item.setData(Qt.ItemDataRole.UserRole + 1, r['full_name'])
                self.indiv_results.addItem(item)
        except Exception as e:
            print(f"Employee search failed: {e}")

    def _on_indiv_result_clicked(self, item: QListWidgetItem):
        try:
            emp_id = item.data(Qt.ItemDataRole.UserRole)
            full_name = item.data(Qt.ItemDataRole.UserRole + 1)
            self._selected_emp_id = emp_id
            self.selected_emp_label.setText(f"Selected: {full_name} – {emp_id}")
            self._update_indiv_table()
        except Exception as e:
            print(f"Selecting employee failed: {e}")

    def _on_indiv_selection_changed(self, *_):
        # Refresh individual table when Monthly/Yearly view changes
        self._update_indiv_table()

    def _update_indiv_table(self):
        emp_id = getattr(self, '_selected_emp_id', None)
        view = self.indiv_view_combo.currentText() if self.indiv_view_combo.count() else "Monthly"

        if not emp_id:
            # Default: show all employees aggregated for the selected period
            try:
                from ..database.db_queries import get_all_employees_hours_for_month, get_all_employees_hours_for_year
                if view == "Monthly":
                    today = QDate.currentDate()
                    year = today.year()
                    month = today.month()
                    rows = get_all_employees_hours_for_month(year, month) or []
                    self.indiv_table.setColumnCount(6)
                    self.indiv_table.setHorizontalHeaderLabels([
                        "Employee Name", "Total Hours", "Average Daily Hours",
                        "Total Absences", "Attendance %", "Overtime Hours"
                    ])
                    self.indiv_table.setRowCount(len(rows))

                    total_hours = 0.0
                    total_absences = 0
                    total_overtime = 0.0

                    for i, r in enumerate(rows):
                        name = r.get('full_name', '')
                        hours = float(r.get('hours', 0) or 0)
                        absences = int(r.get('absences', 0) or 0)
                        worked_days = int(r.get('worked_days', 0) or 0)
                        expected_days = int(r.get('expected_days', 0) or 0)
                        overtime = float(r.get('overtime', 0) or 0)

                        # Calculate derived values
                        avg_daily_hours = round(hours / worked_days, 2) if worked_days > 0 else 0
                        attendance_pct = round((worked_days / expected_days) * 100, 1) if expected_days > 0 else 0

                        # Set table items
                        self.indiv_table.setItem(i, 0, QTableWidgetItem(name))
                        self.indiv_table.setItem(i, 1, QTableWidgetItem(str(round(hours, 2))))
                        self.indiv_table.setItem(i, 2, QTableWidgetItem(str(avg_daily_hours)))
                        self.indiv_table.setItem(i, 3, QTableWidgetItem(str(absences)))
                        self.indiv_table.setItem(i, 4, QTableWidgetItem(f"{attendance_pct}%"))
                        self.indiv_table.setItem(i, 5, QTableWidgetItem(str(round(overtime, 2))))

                        total_hours += hours
                        total_absences += absences
                        total_overtime += overtime

                    self.indiv_summary_label.setText(
                        f"Employees: {len(rows)}  •  Total Hours: {round(total_hours, 2)}  •  "
                        f"Total Absences: {total_absences}  •  Total Overtime: {round(total_overtime, 2)}"
                    )
                    self.selected_emp_label.setText("Selected: All employees – Monthly view")
                else:
                    today = QDate.currentDate()
                    year = today.year()
                    rows = get_all_employees_hours_for_year(year) or []
                    self.indiv_table.setColumnCount(6)
                    self.indiv_table.setHorizontalHeaderLabels([
                        "Employee Name", "Total Hours", "Average Daily Hours",
                        "Total Absences", "Attendance %", "Overtime Hours"
                    ])
                    self.indiv_table.setRowCount(len(rows))

                    total_hours = 0.0
                    total_absences = 0
                    total_overtime = 0.0

                    for i, r in enumerate(rows):
                        name = r.get('full_name', '')
                        hours = float(r.get('hours', 0) or 0)
                        absences = int(r.get('absences', 0) or 0)
                        worked_days = int(r.get('worked_days', 0) or 0)
                        expected_days = int(r.get('expected_days', 0) or 0)
                        overtime = float(r.get('overtime', 0) or 0)

                        # Calculate derived values
                        avg_daily_hours = round(hours / worked_days, 2) if worked_days > 0 else 0
                        attendance_pct = round((worked_days / expected_days) * 100, 1) if expected_days > 0 else 0

                        # Set table items
                        self.indiv_table.setItem(i, 0, QTableWidgetItem(name))
                        self.indiv_table.setItem(i, 1, QTableWidgetItem(str(round(hours, 2))))
                        self.indiv_table.setItem(i, 2, QTableWidgetItem(str(avg_daily_hours)))
                        self.indiv_table.setItem(i, 3, QTableWidgetItem(str(absences)))
                        self.indiv_table.setItem(i, 4, QTableWidgetItem(f"{attendance_pct}%"))
                        self.indiv_table.setItem(i, 5, QTableWidgetItem(str(round(overtime, 2))))

                        total_hours += hours
                        total_absences += absences
                        total_overtime += overtime

                    self.indiv_summary_label.setText(
                        f"Employees: {len(rows)}  •  Total Hours: {round(total_hours, 2)}  •  "
                        f"Total Absences: {total_absences}  •  Total Overtime: {round(total_overtime, 2)}"
                    )
                    self.selected_emp_label.setText("Selected: All employees – Yearly view")
            except Exception as e:
                print(f"Failed to load default employee hours: {e}")
                self.indiv_table.setRowCount(0)
                self.indiv_summary_label.setText("No data available")
            return

        # Individual employee view
        try:
            from ..database.db_queries import get_employee_monthly_hours, get_employee_yearly_hours
            total_hours = 0
            total_absences = 0
            total_overtime = 0

            if view == "Monthly":
                import datetime, calendar
                year = datetime.date.today().year
                rows = get_employee_monthly_hours(emp_id, year) or []

                # Create a dict for easier lookup
                months_data = {int(r['month']): r for r in rows}

                self.indiv_table.setColumnCount(6)
                self.indiv_table.setHorizontalHeaderLabels([
                    "Month", "Total Hours", "Average Daily Hours",
                    "Total Absences", "Attendance %", "Overtime Hours"
                ])
                self.indiv_table.setRowCount(12)

                for m in range(1, 13):
                    month_data = months_data.get(m, {})
                    hours = float(month_data.get('hours', 0) or 0)
                    absences = int(month_data.get('absences', 0) or 0)
                    worked_days = int(month_data.get('worked_days', 0) or 0)
                    expected_days = int(month_data.get('expected_days', 0) or 0)
                    overtime = float(month_data.get('overtime', 0) or 0)

                    # Calculate derived values
                    avg_daily_hours = round(hours / worked_days, 2) if worked_days > 0 else 0
                    attendance_pct = round((worked_days / expected_days) * 100, 1) if expected_days > 0 else 0

                    # Set table items
                    self.indiv_table.setItem(m-1, 0, QTableWidgetItem(calendar.month_name[m]))
                    self.indiv_table.setItem(m-1, 1, QTableWidgetItem(str(round(hours, 2))))
                    self.indiv_table.setItem(m-1, 2, QTableWidgetItem(str(avg_daily_hours)))
                    self.indiv_table.setItem(m-1, 3, QTableWidgetItem(str(absences)))
                    self.indiv_table.setItem(m-1, 4, QTableWidgetItem(f"{attendance_pct}%" if expected_days > 0 else "--"))
                    self.indiv_table.setItem(m-1, 5, QTableWidgetItem(str(round(overtime, 2))))

                    total_hours += hours
                    total_absences += absences
                    total_overtime += overtime

                self.indiv_summary_label.setText(
                    f"Yearly Total ({year}): {round(total_hours, 2)} hours  •  "
                    f"Total Absences: {total_absences}  •  Total Overtime: {round(total_overtime, 2)}"
                )
            else:
                rows = get_employee_yearly_hours(emp_id) or []
                self.indiv_table.setColumnCount(6)
                self.indiv_table.setHorizontalHeaderLabels([
                    "Year", "Total Hours", "Average Daily Hours",
                    "Total Absences", "Attendance %", "Overtime Hours"
                ])
                self.indiv_table.setRowCount(len(rows))

                for i, r in enumerate(rows):
                    year = r['year']
                    hours = float(r.get('hours', 0) or 0)
                    absences = int(r.get('absences', 0) or 0)
                    worked_days = int(r.get('worked_days', 0) or 0)
                    expected_days = int(r.get('expected_days', 0) or 0)
                    overtime = float(r.get('overtime', 0) or 0)

                    # Calculate derived values
                    avg_daily_hours = round(hours / worked_days, 2) if worked_days > 0 else 0
                    attendance_pct = round((worked_days / expected_days) * 100, 1) if expected_days > 0 else 0

                    # Set table items
                    self.indiv_table.setItem(i, 0, QTableWidgetItem(str(year)))
                    self.indiv_table.setItem(i, 1, QTableWidgetItem(str(round(hours, 2))))
                    self.indiv_table.setItem(i, 2, QTableWidgetItem(str(avg_daily_hours)))
                    self.indiv_table.setItem(i, 3, QTableWidgetItem(str(absences)))
                    self.indiv_table.setItem(i, 4, QTableWidgetItem(f"{attendance_pct}%" if expected_days > 0 else "--"))
                    self.indiv_table.setItem(i, 5, QTableWidgetItem(str(round(overtime, 2))))

                    total_hours += hours
                    total_absences += absences
                    total_overtime += overtime

                self.indiv_summary_label.setText(
                    f"All Years Total: {round(total_hours, 2)} hours  •  "
                    f"Total Absences: {total_absences}  •  Total Overtime: {round(total_overtime, 2)}"
                )
        except Exception as e:
            print(f"Failed to update individual table: {e}")
            # Graceful fallback - show basic table with placeholders
            self.indiv_table.setColumnCount(6)
            self.indiv_table.setHorizontalHeaderLabels([
                "Employee Name", "Total Hours", "Average Daily Hours",
                "Total Absences", "Attendance %", "Overtime Hours"
            ])
            self.indiv_table.setRowCount(1)
            self.indiv_table.setItem(0, 0, QTableWidgetItem("Data unavailable"))
            for col in range(1, 6):
                self.indiv_table.setItem(0, col, QTableWidgetItem("--"))
            self.indiv_summary_label.setText("Error loading data")

    def update_reports_view(self, period_text=None):
        # Map between display text and internal period code
        periods = {"Daily": "daily", "Weekly": "weekly", "Monthly": "monthly", "Yearly": "yearly"}
        display_for = {v: k for k, v in periods.items()}

        # If the user selected a new period via the combo, update internal state.
        if isinstance(period_text, str) and period_text:
            self.report_period = periods.get(period_text, getattr(self, 'report_period', 'daily'))
        else:
            # No explicit period passed (e.g., auto-refresh) -> keep current selection/state.
            if not getattr(self, 'report_period', None):
                # Initialize from combo if available, else default to daily
                if hasattr(self, 'period_combo') and self.period_combo and self.period_combo.count():
                    self.report_period = periods.get(self.period_combo.currentText(), 'daily')
                else:
                    self.report_period = 'daily'

        # Build title from current internal state
        display_text = display_for.get(self.report_period, 'Daily')
        title = f"{display_text} Attendance Report"

        # Fetch and plot
        labels, present, late, absent = self.get_report_data(self.report_period)

        if hasattr(self, 'reports_chart') and self.reports_chart and MATPLOTLIB_AVAILABLE and getattr(self.reports_chart, 'canvas', None):
            try:
                self.reports_chart.plot(labels, present, late, absent, title)
            except Exception as e:
                print(f"Failed to update reports chart: {e}")

        # Update individual summary (keep it fresh when switching periods)
        try:
            self._update_indiv_table()
        except Exception as e:
            print(f"Failed to update individual summary: {e}")

        if hasattr(self, 'reports_chart_header'):
            self.reports_chart_header.setText(f"📊 {title}")

    def get_report_data(self, period):
        try:
            data = get_department_attendance(period)
            labels = [d['department'] for d in data]
            present = [d.get('present', 0) for d in data]
            late = [d.get('late', 0) for d in data]
            # Prefer DB 'absent' when present; for daily period, derive if missing/zero
            if period == 'daily':
                total = [d.get('total_employees', 0) for d in data]
                absent = [max(0, (total[i] or 0) - (int(present[i] or 0) + int(late[i] or 0))) for i in range(len(data))]
            else:
                absent = [d.get('absent', 0) for d in data]
            return labels, present, late, absent
        except Exception as e:
            print(f"Failed to get report data: {e}")
            return [], [], [], []

    def export_report_csv(self):
        from PyQt6.QtCore import QDate

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export CSV",
            f"attendance_report_{self.report_period}.csv",
            "CSV Files (*.csv)"
        )
        if not path:
            return

        today = QDate.currentDate()

        # Determine period label
        if self.report_period == "daily":
            period_label = today.toString("yyyy-MM-dd")
        elif self.report_period == "weekly":
            start = today.addDays(-7)
            period_label = f"{start.toString('yyyy-MM-dd')} to {today.toString('yyyy-MM-dd')}"
        elif self.report_period == "monthly":
            period_label = today.toString("MMMM yyyy")
        elif self.report_period == "yearly":
            period_label = today.toString("yyyy")
        else:
            period_label = today.toString("yyyy-MM-dd")

        # Write CSV
        with open(path, "w", encoding="utf-8") as f:
            f.write("Period,Department,Total Employees,Present,Late,Absent\n")
            for d in get_department_attendance(self.report_period):
                f.write(
                    f"{period_label},{d['department']},{d['total_employees']},{d['present']},{d['late']},{d['absent']}\n"
                )

        QMessageBox.information(self, "Export Successful", f"Report exported to {path}")

    def export_report_pdf(self):
        from PyQt6.QtGui import QPdfWriter, QPainter, QFont, QTextDocument
        from PyQt6.QtCore import QDate, QSizeF
        from PyQt6.QtGui import QPageSize, QPageLayout

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export PDF",
            f"attendance_report_{self.report_period}.pdf",
            "PDF Files (*.pdf)"
        )
        if not path:
            return

        # Get report data
        data = get_department_attendance(self.report_period)

        # Period label (Month/Year/Daily)
        today = QDate.currentDate()
        if self.report_period == "monthly":
            period_label = today.toString("MMMM yyyy")
        elif self.report_period == "yearly":
            period_label = today.toString("yyyy")
        else:
            period_label = today.toString("MMMM d, yyyy")

        # Build HTML report
        html = f"""
        <h2 style="text-align:center;">{self.report_period.capitalize()} Attendance Report – {period_label}</h2>
        <br>
        <table border="1" cellspacing="0" cellpadding="40" width="100%">
            <thead>
                <tr style="background-color:#f3f4f6;">
                    <th align="left">Department</th>
                    <th align="center">Total Employees</th>
                    <th align="center">Present</th>
                    <th align="center">Late</th>
                    <th align="center">Absent</th>
                </tr>
            </thead>
            <tbody>
        """
        for d in data:
            html += f"""
                <tr>
                    <td>{d['department']}</td>
                    <td align="center">{d['total_employees']}</td>
                    <td align="center">{d['present']}</td>
                    <td align="center">{d['late']}</td>
                    <td align="center">{d['absent']}</td>
                </tr>
            """
        html += "</tbody></table>"

        # PDF Writer
        writer = QPdfWriter(path)
        writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        writer.setPageOrientation(QPageLayout.Orientation.Portrait)

        # QTextDocument to render HTML
        doc = QTextDocument()
        doc.setDefaultFont(QFont("Inter", 10))
        doc.setHtml(html)

        # Use QPainter safely
        painter = QPainter(writer)
        doc.setPageSize(QSizeF(writer.width(), writer.height()))
        doc.drawContents(painter)
        painter.end()

        QMessageBox.information(self, "Export Successful", f"Report exported to {path}")

    def export_individual_hours_csv(self):
        """Export individual working hours table to CSV"""
        from PyQt6.QtCore import QDate

        # Get current data from the individual table
        row_count = self.indiv_table.rowCount()
        column_count = self.indiv_table.columnCount()

        if row_count == 0:
            QMessageBox.warning(self, "No Data", "No individual hours data available to export.")
            return

        # Get selected employee info for filename
        emp_id = getattr(self, '_selected_emp_id', None)
        view = self.indiv_view_combo.currentText() if self.indiv_view_combo.count() else "Monthly"

        if emp_id:
            filename = f"individual_hours_{emp_id}_{view.lower()}.csv"
        else:
            filename = f"all_employees_hours_{view.lower()}.csv"

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Individual Hours CSV",
            filename,
            "CSV Files (*.csv)"
        )
        if not path:
            return

        # Write CSV
        with open(path, "w", encoding="utf-8") as f:
            # Write headers
            headers = []
            for col in range(column_count):
                header_item = self.indiv_table.horizontalHeaderItem(col)
                headers.append(header_item.text() if header_item else f"Column {col + 1}")
            f.write(",".join(headers) + "\n")

            # Write data rows
            for row in range(row_count):
                row_data = []
                for col in range(column_count):
                    item = self.indiv_table.item(row, col)
                    row_data.append(item.text() if item else "")
                f.write(",".join(row_data) + "\n")

        QMessageBox.information(self, "Export Successful", f"Individual hours exported to {path}")

    def export_individual_hours_pdf(self):
        """Export individual working hours table to PDF"""
        from PyQt6.QtGui import QPdfWriter, QPainter, QFont, QTextDocument
        from PyQt6.QtCore import QDate, QSizeF
        from PyQt6.QtGui import QPageSize, QPageLayout

        # Get current data from the individual table
        row_count = self.indiv_table.rowCount()
        column_count = self.indiv_table.columnCount()

        if row_count == 0:
            QMessageBox.warning(self, "No Data", "No individual hours data available to export.")
            return

        # Get selected employee info for filename and title
        emp_id = getattr(self, '_selected_emp_id', None)
        view = self.indiv_view_combo.currentText() if self.indiv_view_combo.count() else "Monthly"

        if emp_id:
            filename = f"individual_hours_{emp_id}_{view.lower()}.pdf"
            title = f"Individual Working Hours Report - {self.selected_emp_label.text()}"
        else:
            filename = f"all_employees_hours_{view.lower()}.pdf"
            title = f"All Employees Working Hours Report - {view} View"

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Individual Hours PDF",
            filename,
            "PDF Files (*.pdf)"
        )
        if not path:
            return

        today = QDate.currentDate()
        period_label = today.toString("MMMM d, yyyy")

        # Build HTML report
        html = f"""
        <h2 style="text-align:center;">{title}</h2>
        <p style="text-align:center;">Generated on: {period_label}</p>
        <br>
        <table border="1" cellspacing="0" cellpadding="10" width="100%">
            <thead>
                <tr style="background-color:#f3f4f6;">
        """

        # Add table headers
        for col in range(column_count):
            header_item = self.indiv_table.horizontalHeaderItem(col)
            header_text = header_item.text() if header_item else f"Column {col + 1}"
            html += f'<th align="center">{header_text}</th>'

        html += """
                </tr>
            </thead>
            <tbody>
        """

        # Add table data
        for row in range(row_count):
            html += "<tr>"
            for col in range(column_count):
                item = self.indiv_table.item(row, col)
                cell_text = item.text() if item else ""
                html += f'<td align="center">{cell_text}</td>'
            html += "</tr>"

        html += """
            </tbody>
        </table>
        """

        # Add summary from the summary label
        summary_text = self.indiv_summary_label.text()
        html += f'<br><p style="text-align:center; font-weight:bold;">{summary_text}</p>'

        # PDF Writer
        writer = QPdfWriter(path)
        writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        writer.setPageOrientation(QPageLayout.Orientation.Portrait)

        # QTextDocument to render HTML
        doc = QTextDocument()
        doc.setDefaultFont(QFont("Inter", 10))
        doc.setHtml(html)

        # Use QPainter safely
        painter = QPainter(writer)
        doc.setPageSize(QSizeF(writer.width(), writer.height()))
        doc.drawContents(painter)
        painter.end()

        QMessageBox.information(self, "Export Successful", f"Individual hours exported to {path}")

    def load_employee_data(self):
        """Load employee data from database into self.employee_data dict."""
        try:
            employees = get_all_employees() or []
            self.employee_data = {}
            for emp in employees:
                self.employee_data[emp['employee_id']] = {
                    'id': emp['employee_id'],
                    'name': emp['full_name'],
                    'position': emp.get('position', ''),
                    'department': emp.get('department', ''),
                    'image_path': emp.get('image_path'),
                    'leave_credits': emp.get('leave_credits', 15),
                    'absences': 0,
                }
        except Exception as e:
            print(f"Error loading employee data: {e}")
            self.employee_data = {}
