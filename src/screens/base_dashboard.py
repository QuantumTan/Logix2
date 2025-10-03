# screens/base_dashboard.py
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QSizePolicy, QStackedWidget,
    QFileDialog, QMessageBox, QInputDialog, QComboBox, QScrollArea, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, QTimer, QTime, QDate
from PyQt6.QtGui import QFont, QPixmap, QPainter, QPageLayout, QPageSize, QPdfWriter

from ..database.db_queries import get_all_employees, get_employee_details, get_department_attendance, update_employee, delete_employee, get_today_attendance, get_today_stats
from ..widgets.reports_chart import ReportsChartWidget
import os
import shutil

# New imports for refactor
from ..config import (
    ATTENDANCE_REFRESH_MS,
    REPORTS_REFRESH_MS,
    INDIV_SEARCH_DEBOUNCE_MS,
    TIME_TICK_MS,
    TIME_DISPLAY_FORMAT,
    DATE_DISPLAY_FORMAT,
)
from ..utils.export_helpers import (
    format_period_label,
    export_department_attendance_csv,
    build_department_attendance_html,
    export_html_to_pdf,
    export_qtablewidget_to_csv,
    build_qtablewidget_html,
)
from .components.employee_management_view import EmployeeManagementView
from .components.reports_view import ReportsView


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

        self.date_label = QLabel(QDate.currentDate().toString(DATE_DISPLAY_FORMAT))
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
        self.time_label.setStyleSheet("background: #eff6ff; color: #3b82f6; font-size: 25px; padding: 20px; border-radius: 10px;")
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
        self.timer.start(TIME_TICK_MS)

        # Setup common pages
        self.setup_attendance_page()
        self.setup_employee_management_page()
        self.setup_reports_page()

        # Initial stats update
        self.update_stats()

        # Periodic attendance refresh (no event bus)
        self.attendance_refresh_timer = QTimer(self)
        self.attendance_refresh_timer.setInterval(ATTENDANCE_REFRESH_MS)
        self.attendance_refresh_timer.timeout.connect(lambda: [self.refresh_attendance_view(), self.update_stats()])
        self.attendance_refresh_timer.start()

        # Reports tab auto-refresh timer - disabled for new reports screen
        self.reports_refresh_timer = QTimer(self)
        self.reports_refresh_timer.setInterval(REPORTS_REFRESH_MS)
        self.reports_refresh_timer.timeout.connect(self.update_reports_view)

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
        text_label.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        text_label.setStyleSheet(f"color: {fg_color}; margin: 10px")
        text_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        number_label = QLabel(str(number))
        number_label.setFont(QFont("Inter", 18, QFont.Weight.Bold))
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
        current_time = QTime.currentTime().toString(TIME_DISPLAY_FORMAT)
        self.time_label.setText(f"Current Time\n{current_time}")

    def setup_attendance_page(self):
        # Revert to inline UI setup to avoid any component-parent lifecycle issues
        if hasattr(self, 'attendance_page') and self.attendance_page is not None:
            return
        self.attendance_page = QWidget()
        attendance_layout = QVBoxLayout(self.attendance_page)

        self.attendance_search = QLineEdit()
        self.attendance_search.setPlaceholderText("🔍 Search attendance...")
        self.attendance_search.setFixedHeight(35)
        self.attendance_search.setStyleSheet(
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
        self.attendance_search.textChanged.connect(self.filter_attendance_table)
        attendance_layout.addWidget(self.attendance_search)

        self.attendance_table = QTableWidget()
        self.attendance_table.setColumnCount(6)
        self.attendance_table.setHorizontalHeaderLabels([
            "Employee ID", "Employee Name", "Check In", "Check Out", "Status", "Action"
        ])
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
        try:
            from ..database.db_queries import get_employee_by_id, get_employee_details
            basic = get_employee_by_id(emp_id)
            if basic:
                details = get_employee_details(emp_id)
                employee_data = {
                    'id': basic['employee_id'],
                    'name': basic['full_name'],
                    'position': basic['position'],
                    'department': basic['department'],
                    'image_path': basic.get('image_path'),
                    **(details or {})
                }
                from .emp_details import EmployeeDetailsModal
                modal = EmployeeDetailsModal(employee_data, self)
                modal.exec()
        except Exception as e:
            print(f"Failed to show employee details: {e}")

    def setup_employee_management_page(self):
        # Replace inline UI with component while keeping attribute names and signals
        if hasattr(self, 'employee_management_page') and self.employee_management_page is not None:
            return
        view = EmployeeManagementView(self)
        self.employee_management_page = view
        self.add_emp_btn = view.add_emp_btn
        self.search = view.search_edit
        self.table = view.table
        self.search.textChanged.connect(self.filter_employee_table)
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
            self.table.setCellWidget(row, 6, action_widget)

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
        # Replace inline UI with component and wire up signals/buttons
        if hasattr(self, 'reports_page') and self.reports_page is not None:
            return

        view = ReportsView(self)
        # Alias commonly used attributes for backward compatibility
        self.reports_main_widget = view.main_widget
        self.period_combo = view.period_combo
        self.reports_chart_header = view.reports_chart_header
        self.reports_chart = view.reports_chart
        self._reports_placeholder = view._reports_placeholder
        self.chart_container_layout = view.chart_container_layout
        self.indiv_search_input = view.indiv_search_input
        self.indiv_search_timer = view.indiv_search_timer
        self.indiv_results = view.indiv_results
        self.selected_emp_label = view.selected_emp_label
        self.indiv_view_combo = view.indiv_view_combo
        self.indiv_table = view.indiv_table
        self.indiv_summary_label = view.indiv_summary_label

        # Wire signals
        self.period_combo.currentTextChanged.connect(self.update_reports_view)
        view.export_csv_btn.clicked.connect(self.export_report_csv)
        view.export_pdf_btn.clicked.connect(self.export_report_pdf)

        self.indiv_search_timer.setInterval(INDIV_SEARCH_DEBOUNCE_MS)
        self.indiv_search_input.textChanged.connect(self._on_indiv_search_text_changed)
        self.indiv_search_timer.timeout.connect(self._perform_indiv_search)
        self.indiv_results.itemClicked.connect(self._on_indiv_result_clicked)
        self.indiv_view_combo.currentTextChanged.connect(self._on_indiv_selection_changed)

        # Wire individual exports
        view.indiv_export_csv_btn.clicked.connect(self.export_individual_hours_csv)
        view.indiv_export_pdf_btn.clicked.connect(self.export_individual_hours_pdf)

        # Content widget is the scroll area itself
        self.reports_scroll = view
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
                from ..database.db_queries import get_all_employees_hours_for_month, get_all_employees_hours_for_year, get_all_employees
                if view == "Monthly":
                    today = QDate.currentDate()
                    year = today.year()
                    month = today.month()
                    rows = get_all_employees_hours_for_month(year, month) or []

                    if not rows:
                        emps = get_all_employees() or []
                        import datetime as _dt
                        import calendar as _cal
                        first_of_month = _dt.date(year, month, 1)
                        last_of_month = _dt.date(year, month, _cal.monthrange(year, month)[1])
                        cap_end = min(last_of_month, _dt.date.today())
                        def _count_weekdays(start: _dt.date, end: _dt.date) -> int:
                            d = start
                            cnt = 0
                            one = _dt.timedelta(days=1)
                            while d <= end:
                                if d.weekday() < 5:
                                    cnt += 1
                                d += one
                            return max(cnt, 0)
                        synthesized = []
                        for e in emps:
                            created_at = e.get('created_at')
                            hire_date = created_at.date() if created_at else first_of_month
                            eff_start = max(first_of_month, hire_date)
                            expected_days = _count_weekdays(eff_start, cap_end) if eff_start <= cap_end else 0
                            synthesized.append({
                                'full_name': e.get('full_name', ''),
                                'hours': 0.0,
                                'absences': expected_days,
                                'worked_days': 0,
                                'expected_days': expected_days,
                                'overtime': 0.0,
                            })
                        rows = synthesized

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

                        avg_daily_hours = round(hours / worked_days, 2) if worked_days > 0 else 0
                        attendance_pct = round((worked_days / expected_days) * 100, 1) if expected_days > 0 else 0

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

                    if not rows:
                        emps = get_all_employees() or []
                        import datetime as _dt
                        jan1 = _dt.date(year, 1, 1)
                        dec31 = _dt.date(year, 12, 31)
                        cap_end = min(dec31, _dt.date.today())
                        def _count_weekdays(start: _dt.date, end: _dt.date) -> int:
                            d = start
                            cnt = 0
                            one = _dt.timedelta(days=1)
                            while d <= end:
                                if d.weekday() < 5:
                                    cnt += 1
                                d += one
                            return max(cnt, 0)
                        synthesized = []
                        for e in emps:
                            created_at = e.get('created_at')
                            hire_date = created_at.date() if created_at else jan1
                            eff_start = max(jan1, hire_date)
                            expected_days = _count_weekdays(eff_start, cap_end) if eff_start <= cap_end else 0
                            synthesized.append({
                                'full_name': e.get('full_name', ''),
                                'hours': 0.0,
                                'absences': expected_days,
                                'worked_days': 0,
                                'expected_days': expected_days,
                                'overtime': 0.0,
                                'year': year
                            })
                        rows = synthesized

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

                        avg_daily_hours = round(hours / worked_days, 2) if worked_days > 0 else 0
                        attendance_pct = round((worked_days / expected_days) * 100, 1) if expected_days > 0 else 0

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

                    avg_daily_hours = round(hours / worked_days, 2) if worked_days > 0 else 0
                    attendance_pct = round((worked_days / expected_days) * 100, 1) if expected_days > 0 else 0

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
                if not rows:
                    try:
                        from ..database.db_queries import get_employee_by_id
                        import datetime as _dt
                        today = _dt.date.today()
                        year = today.year
                        emp = get_employee_by_id(emp_id) or {}
                        created_at = emp.get('created_at')
                        hire_date = created_at.date() if created_at else _dt.date(year, 1, 1)
                        start = max(_dt.date(year, 1, 1), hire_date)
                        end = min(_dt.date(year, 12, 31), today)
                        one = _dt.timedelta(days=1)
                        wd = 0
                        d = start
                        while d <= end:
                            if d.weekday() < 5:
                                wd += 1
                            d += one
                        rows = [{
                            'year': year,
                            'hours': 0.0,
                            'worked_days': 0,
                            'attended_days': 0,
                            'overtime': 0.0,
                            'expected_days': wd,
                            'absences': wd
                        }]
                    except Exception as _e:
                        rows = []
                self.indiv_table.setColumnCount(6)
                self.indiv_table.setHorizontalHeaderLabels([
                    "Year", "Total Hours", "Average Daily Hours",
                    "Total Absences", "Attendance %", "Overtime Hours"
                ])
                self.indiv_table.setRowCount(len(rows))

                for i, r in enumerate(rows):
                    year = r.get('year') or QDate.currentDate().year()
                    hours = float(r.get('hours', 0) or 0)
                    absences = int(r.get('absences', 0) or 0)
                    worked_days = int(r.get('worked_days', 0) or 0)
                    expected_days = int(r.get('expected_days', 0) or 0)
                    overtime = float(r.get('overtime', 0) or 0)

                    avg_daily_hours = round(hours / worked_days, 2) if worked_days > 0 else 0
                    attendance_pct = round((worked_days / expected_days) * 100, 1) if expected_days > 0 else 0

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

        if isinstance(period_text, str) and period_text:
            self.report_period = periods.get(period_text, getattr(self, 'report_period', 'daily'))
        else:
            if not getattr(self, 'report_period', None):
                if hasattr(self, 'period_combo') and self.period_combo and self.period_combo.count():
                    self.report_period = periods.get(self.period_combo.currentText(), 'daily')
                else:
                    self.report_period = 'daily'

        display_text = display_for.get(self.report_period, 'Daily')
        title = f"{display_text} Attendance Report"

        labels, present, late, absent = self.get_report_data(self.report_period)

        if hasattr(self, 'reports_chart') and self.reports_chart and getattr(self.reports_chart, 'canvas', None):
            try:
                self.reports_chart.plot(labels, present, late, absent, title)
            except Exception as e:
                print(f"Failed to update reports chart: {e}")

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
        # Use helper utilities to export department attendance CSV
        from PyQt6.QtCore import QDate
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export CSV",
            f"attendance_report_{getattr(self, 'report_period', 'daily')}.csv",
            "CSV Files (*.csv)"
        )
        if not path:
            return

        today = QDate.currentDate()
        period_label = format_period_label(getattr(self, 'report_period', 'daily'), today)
        rows = get_department_attendance(getattr(self, 'report_period', 'daily'))
        export_department_attendance_csv(rows, period_label, path)
        QMessageBox.information(self, "Export Successful", f"Report exported to {path}")

    def export_report_pdf(self):
        # Build HTML using helpers and render to PDF
        from PyQt6.QtCore import QDate
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export PDF",
            f"attendance_report_{getattr(self, 'report_period', 'daily')}.pdf",
            "PDF Files (*.pdf)"
        )
        if not path:
            return

        data = get_department_attendance(getattr(self, 'report_period', 'daily'))
        today = QDate.currentDate()
        display = getattr(self, 'report_period', 'daily').capitalize()
        period_label = format_period_label(getattr(self, 'report_period', 'daily'), today)
        html = build_department_attendance_html(f"{display} Attendance Report", period_label, data)
        export_html_to_pdf(html, path)
        QMessageBox.information(self, "Export Successful", f"Report exported to {path}")

    def export_individual_hours_csv(self):
        """Export individual working hours table to CSV using helpers"""
        row_count = self.indiv_table.rowCount()
        if row_count == 0:
            QMessageBox.warning(self, "No Data", "No individual hours data available to export.")
            return

        emp_id = getattr(self, '_selected_emp_id', None)
        view = self.indiv_view_combo.currentText() if self.indiv_view_combo.count() else "Monthly"
        filename = f"individual_hours_{emp_id}_{view.lower()}.csv" if emp_id else f"all_employees_hours_{view.lower()}.csv"
        path, _ = QFileDialog.getSaveFileName(self, "Export Individual Hours CSV", filename, "CSV Files (*.csv)")
        if not path:
            return
        export_qtablewidget_to_csv(self.indiv_table, path)
        QMessageBox.information(self, "Export Successful", f"Individual hours exported to {path}")

    def export_individual_hours_pdf(self):
        """Export individual working hours table to PDF using helpers"""
        row_count = self.indiv_table.rowCount()
        if row_count == 0:
            QMessageBox.warning(self, "No Data", "No individual hours data available to export.")
            return

        emp_id = getattr(self, '_selected_emp_id', None)
        view = self.indiv_view_combo.currentText() if self.indiv_view_combo.count() else "Monthly"
        if emp_id:
            filename = f"individual_hours_{emp_id}_{view.lower()}.pdf"
            title = f"Individual Working Hours Report - {self.selected_emp_label.text()}"
        else:
            filename = f"all_employees_hours_{view.lower()}.pdf"
            title = f"All Employees Working Hours Report - {view} View"

        path, _ = QFileDialog.getSaveFileName(self, "Export Individual Hours PDF", filename, "PDF Files (*.pdf)")
        if not path:
            return

        from PyQt6.QtCore import QDate
        today = QDate.currentDate()
        subtitle = f"Generated on: {today.toString('MMMM d, yyyy')}"
        html = build_qtablewidget_html(self.indiv_table, title, subtitle=subtitle, summary_text=self.indiv_summary_label.text())
        export_html_to_pdf(html, path)
        QMessageBox.information(self, "Export Successful", f"Individual hours exported to {path}")

    def load_employee_data(self):
        """Load employee data from database into self.employee_data dict."""
        try:
            employees = get_all_employees() or []
            self.employee_data = {}
            for emp in employees:
                emp_id = emp['employee_id']
                details = {}
                try:
                    details = get_employee_details(emp_id, 'month') or {}
                except Exception as _e:
                    details = {}
                self.employee_data[emp_id] = {
                    'id': emp_id,
                    'name': emp['full_name'],
                    'position': emp.get('position', ''),
                    'department': emp.get('department', ''),
                    'image_path': emp.get('image_path'),
                    'leave_credits': details.get('leave_credits', emp.get('leave_credits', 15)),
                    'absences': int(details.get('absences', 0) or 0),
                }
        except Exception as e:
            print(f"Error loading employee data: {e}")
            self.employee_data = {}
