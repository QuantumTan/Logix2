# screens/base_dashboard.py
import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QSizePolicy, QStackedWidget,
    QFileDialog, QMessageBox, QInputDialog, QComboBox
)
from PyQt6.QtCore import Qt, QTimer, QTime, QDate
from PyQt6.QtGui import QFont, QPixmap, QPainter, QPageLayout, QPageSize, QPdfWriter

from database.db_queries import get_all_employees, get_employee_details, get_department_attendance, add_employee, update_employee, delete_employee, get_today_attendance, get_today_stats
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
                self.figure = self._Figure(figsize=(10, 6), tight_layout=True)
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
        ##removed because database has been implemented
        pass

    def plot(self, labels: list[str], present: list[int], late: list[int], title: str):
        """Plot method for dynamic data"""
        try:
            if not MATPLOTLIB_AVAILABLE or not self.canvas or not self.figure:
                return

            # Clear and create single plot
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            x = list(range(len(labels)))
            ax.bar(x, present, color="#10b981", label="Present", alpha=0.8)
            ax.bar(x, late, bottom=present, color="#f59e0b", label="Late", alpha=0.8)
            ax.set_xticks(x)
            ax.set_xticklabels(labels)
            ax.set_title(title, fontweight='bold')
            ax.set_ylabel('Number of Employees')
            ax.grid(True, axis='y', linestyle='--', alpha=0.3)
            ax.legend()
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

        # Reports tab auto-refresh timer
        self.reports_refresh_timer = QTimer(self)
        self.reports_refresh_timer.setInterval(10000)  # 10 seconds
        self.reports_refresh_timer.timeout.connect(lambda: self.update_reports_view(self.period_combo.currentText()))

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
        rows = [row for row in self.attendance_rows if text in row.get('full_name', '').lower() or text in row.get('employee_id', '').lower()]
        self.attendance_table.setRowCount(len(rows))
        for r, data in enumerate(rows):
            self.attendance_table.setItem(r, 0, QTableWidgetItem(data.get('employee_id', '')))
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
        self.load_employee_table()

        emp_layout.addWidget(self.table)
        self.content_stack.addWidget(self.employee_management_page)

    def load_employee_table(self):
        self.load_employee_data()
        self.table.setRowCount(len(self.employee_data))
        keys = list(self.employee_data.keys())
        for row in range(len(keys)):
            emp_id = keys[row]
            emp = self.employee_data[emp_id]
            self.table.setItem(row, 0, QTableWidgetItem(emp['id']))
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
        text = text.lower()
        row = 0
        for emp_id, emp in self.employee_data.items():
            if text in emp['name'].lower() or text in emp['id'].lower() or text in emp['position'].lower() or text in emp['department'].lower():
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
        self.reports_page = QWidget()
        reports_layout = QVBoxLayout(self.reports_page)

        # Period selector
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
        pdf_btn = QPushButton("Export PDF")
        pdf_btn.clicked.connect(self.export_report_pdf)
        period_layout.addWidget(csv_btn)
        period_layout.addWidget(pdf_btn)

        reports_layout.addLayout(period_layout)

        # Chart header
        self.reports_chart_header = QLabel("📊 Daily Attendance Report")
        self.reports_chart_header.setFont(QFont("Inter", 16, QFont.Weight.Bold))
        self.reports_chart_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        reports_layout.addWidget(self.reports_chart_header)

        # --- Cards and Chart Layout ---
        main_hbox = QHBoxLayout()

        # Chart placeholder (left)
        self.reports_chart = None
        self._reports_placeholder = QLabel("Open the Reports tab to load charts.")
        self._reports_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._reports_placeholder.setStyleSheet(
            "color:#6b7280; font-size: 14px; padding: 40px; background: white; border-radius: 8px;")
        main_hbox.addWidget(self._reports_placeholder, stretch=1)

        # Cards VBox (right)
        self.cards_vbox = QVBoxLayout()
        self.cards_vbox.setSpacing(20)

        # Attendance Rate Card
        self.attendance_rate_card = QWidget()
        ar_vbox = QVBoxLayout(self.attendance_rate_card)
        ar_vbox.setContentsMargins(16, 12, 16, 12)
        ar_vbox.setSpacing(8)
        ar_label = QLabel("Attendance Rate")
        ar_label.setFont(QFont("Inter", 12))
        ar_label.setStyleSheet("color: #374151; margin-bottom: 4px;")
        ar_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.attendance_rate_value = QLabel("--%")
        self.attendance_rate_value.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        self.attendance_rate_value.setStyleSheet("color: #1f2937;")
        self.attendance_rate_value.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)
        ar_vbox.addWidget(ar_label)
        ar_vbox.addStretch(1)
        ar_vbox.addWidget(self.attendance_rate_value)
        self.attendance_rate_card.setStyleSheet("background:#f1f5f9; border-radius:10px;")
        self.cards_vbox.addWidget(self.attendance_rate_card)

        # Employees Present Card
        self.total_present_card = QWidget()
        tp_vbox = QVBoxLayout(self.total_present_card)
        tp_vbox.setContentsMargins(16, 12, 16, 12)
        tp_vbox.setSpacing(8)
        present_label = QLabel("Employees Present")
        present_label.setFont(QFont("Inter", 12))
        present_label.setStyleSheet("color: #10b981; margin-bottom: 4px;")
        present_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.total_present_value = QLabel("--")
        self.total_present_value.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        self.total_present_value.setStyleSheet("color: #10b981;")
        self.total_present_value.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)
        tp_vbox.addWidget(present_label)
        tp_vbox.addStretch(1)
        tp_vbox.addWidget(self.total_present_value)
        self.total_present_card.setStyleSheet("background:#dcfce7; border-radius:10px;")
        self.cards_vbox.addWidget(self.total_present_card)

        # Late Arrivals Card
        self.total_late_card = QWidget()
        tl_vbox = QVBoxLayout(self.total_late_card)
        tl_vbox.setContentsMargins(16, 12, 16, 12)
        tl_vbox.setSpacing(8)
        late_label = QLabel("Late Arrivals")
        late_label.setFont(QFont("Inter", 12))
        late_label.setStyleSheet("color: #f59e0b; margin-bottom: 4px;")
        late_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.total_late_value = QLabel("--")
        self.total_late_value.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        self.total_late_value.setStyleSheet("color: #f59e0b;")
        self.total_late_value.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)
        tl_vbox.addWidget(late_label)
        tl_vbox.addStretch(1)
        tl_vbox.addWidget(self.total_late_value)
        self.total_late_card.setStyleSheet("background:#fef3c7; border-radius:10px;")
        self.cards_vbox.addWidget(self.total_late_card)

        main_hbox.addLayout(self.cards_vbox, stretch=0)

        reports_layout.addLayout(main_hbox)
        self.content_stack.addWidget(self.reports_page)
        # Do not call update_reports_view here; wait until tab is shown

    def _ensure_reports_chart(self):
        if self.reports_chart is None:
            layout = self.reports_page.layout().itemAt(2).layout()  # main_hbox
            if self._reports_placeholder is not None:
                layout.removeWidget(self._reports_placeholder)
                self._reports_placeholder.deleteLater()
                self._reports_placeholder = None
            self.reports_chart = ReportsChartWidget()
            layout.insertWidget(0, self.reports_chart, stretch=1)

    def update_reports_view(self, period_text):
        periods = {"Daily": "daily", "Weekly": "weekly", "Monthly": "monthly", "Yearly": "yearly"}
        self.report_period = periods.get(period_text, "daily")
        labels, present, late = self.get_report_data(self.report_period)
        title = f"{period_text} Attendance Report"

        # --- Fetch stats for cards ---
        stats = get_today_stats()
        total_present = stats.get('present', 0)
        total_late = stats.get('late', 0)
        total = total_present + total_late + stats.get('absent', 0)
        attendance_rate = int((total_present / total * 100) if total > 0 else 0)

        self.attendance_rate_value.setText(f"{attendance_rate}%")
        self.total_present_value.setText(str(total_present))
        self.total_late_value.setText(str(total_late))

        # Update chart if available
        if self.reports_chart and MATPLOTLIB_AVAILABLE and getattr(self.reports_chart, 'canvas', None):
            try:
                self.reports_chart.figure.clear()
                ax = self.reports_chart.figure.add_subplot(111)
                import numpy as np
                x = np.arange(len(labels))
                width = 0.35
                ax.bar(x - width/2, present, width, label='Present', color='#10b981')
                ax.bar(x + width/2, late, width, label='Late', color='#f59e0b')
                ax.set_xticks(x)
                ax.set_xticklabels(labels)
                ax.set_ylabel('Employees')
                ax.set_title(title, fontweight='bold')
                ax.legend(loc='upper right')
                self.reports_chart.canvas.draw()
            except Exception as e:
                print(f"Failed to update reports chart: {e}")

        self.reports_chart_header.setText(f"📊 {title}")

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
            # Ensure chart is created only when entering the Reports tab
            self._ensure_reports_chart()
            self.content_stack.setCurrentWidget(self.reports_page)
            # Update reports chart once the widget exists
            self.update_reports_view("Daily")
            self.reports_refresh_timer.start()
        self.current_tab = tab_name

    def get_report_data(self, period):
        data = get_department_attendance(period)
        labels = [d['department'] for d in data]
        present = [d['present'] for d in data]
        late = [d['late'] for d in data]
        return labels, present, late

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
            period_label = today.toString("yyyy-MM-dd")  # 2025-09-30
        elif self.report_period == "weekly":
            start = today.addDays(-7)
            period_label = f"{start.toString('yyyy-MM-dd')} to {today.toString('yyyy-MM-dd')}"
        elif self.report_period == "monthly":
            period_label = today.toString("MMMM yyyy")  # September 2025
        elif self.report_period == "yearly":
            period_label = today.toString("yyyy")  # 2025
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
            period_label = today.toString("MMMM yyyy")  # e.g. September 2025
        elif self.report_period == "yearly":
            period_label = today.toString("yyyy")  # e.g. 2025
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
        doc.setDefaultFont(QFont("Inter", 80))
        doc.setHtml(html)

        # Use QPainter safely
        painter = QPainter(writer)
        doc.setPageSize(QSizeF(writer.width(), writer.height()))
        doc.drawContents(painter)
        painter.end()

        QMessageBox.information(self, "Export Successful", f"Report exported to {path}")

    def _handle_add_employee(self, emp):
        image_dir = 'assets/employees'
        os.makedirs(image_dir, exist_ok=True)
        if emp.get('image_path'):
            ext = os.path.splitext(emp['image_path'])[1]
            new_path = os.path.join(image_dir, f"{emp['id']}{ext}")
            shutil.copy(emp['image_path'], new_path)
            emp['image_path'] = new_path
        add_employee(emp['id'], emp['name'], emp['position'], emp['department'], emp['image_path'])
        self.load_employee_data()
        self.load_employee_table()

    def _handle_update_employee(self, emp):
        image_dir = 'assets/employees'
        os.makedirs(image_dir, exist_ok=True)
        if emp.get('image_path') and not emp['image_path'].startswith(image_dir):
            ext = os.path.splitext(emp['image_path'])[1]
            new_path = os.path.join(image_dir, f"{emp['id']}{ext}")
            shutil.copy(emp['image_path'], new_path)
            emp['image_path'] = new_path
        update_employee(emp['id'], emp['name'], emp['position'], emp['department'], emp['image_path'])
        self.load_employee_data()
        self.load_employee_table()

    def closeEvent(self, event):
        try:
            if hasattr(self, 'reports_chart') and self.reports_chart:
                self.reports_chart.close()
            if hasattr(self, 'timer'):
                self.timer.stop()
            if hasattr(self, 'attendance_refresh_timer'):
                self.attendance_refresh_timer.stop()
            if hasattr(self, 'reports_refresh_timer'):
                self.reports_refresh_timer.stop()
        except Exception as e:
            print(f"Error during DashboardBase close: {e}")
        super().closeEvent(event)

    # fetches data frm db
    def load_employee_data(self):
        """Load employee data from database"""
        try:
            from database.db_queries import get_all_employees
            employees = get_all_employees()
            self.employee_data = {}
            for emp in employees:
                self.employee_data[emp['employee_id']] = {
                    'id': emp['employee_id'],
                    'name': emp['full_name'],
                    'position': emp['position'],
                    'department': emp['department'],
                    'image_path': emp.get('image_path'),
                    'leave_credits': emp.get('leave_credits', 15),
                    'absences': 0
                }
        except Exception as e:
            print(f"Error loading employee data: {e}")
            self.employee_data = {}