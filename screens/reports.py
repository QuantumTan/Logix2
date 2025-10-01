from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QHBoxLayout
)
from PyQt6.QtCore import Qt, QTimer
from database.db_queries import get_all_employees, get_employee_details_by_date_range, get_employee_monthly_attendance_details
import datetime

class ReportsScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Employee Attendance & Working Hours Report")
        self.setGeometry(300, 150, 1200, 700)
        layout = QVBoxLayout()

        # Employee and Month Selection
        selection_layout = QHBoxLayout()

        selection_layout.addWidget(QLabel("Select Employee:"))
        self.employee_selector = QComboBox()
        self.employee_selector.currentIndexChanged.connect(self.update_report)
        selection_layout.addWidget(self.employee_selector)

        selection_layout.addWidget(QLabel("Select Month:"))
        self.month_selector = QComboBox()
        months = ["January", "February", "March", "April", "May", "June",
                 "July", "August", "September", "October", "November", "December"]
        for i, month in enumerate(months, 1):
            self.month_selector.addItem(month, i)
        self.month_selector.setCurrentIndex(datetime.datetime.now().month - 1)  # Current month
        self.month_selector.currentIndexChanged.connect(self.update_report)
        selection_layout.addWidget(self.month_selector)

        layout.addLayout(selection_layout)

        # Monthly Summary Table
        self.monthly_summary_table = QTableWidget()
        self.monthly_summary_table.setColumnCount(3)
        self.monthly_summary_table.setHorizontalHeaderLabels(["Month", "Total Hours", "Total Absences"])
        self.monthly_summary_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.monthly_summary_table.setMaximumHeight(150)
        layout.addWidget(QLabel("Monthly Summary"))
        layout.addWidget(self.monthly_summary_table)

        # Detailed Daily Attendance Table
        self.daily_table = QTableWidget()
        self.daily_table.setColumnCount(5)
        self.daily_table.setHorizontalHeaderLabels(["Date", "Check In", "Check Out", "Status", "Daily Hours"])
        self.daily_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(QLabel("Daily Attendance Details"))
        layout.addWidget(self.daily_table)

        # Summary Labels
        summary_layout = QHBoxLayout()
        self.yearly_label = QLabel("Yearly Total Hours: 0")
        self.yearly_absences_label = QLabel("Yearly Total Absences: 0")
        self.monthly_label = QLabel("Monthly Total Hours: 0")
        self.monthly_absences_label = QLabel("Monthly Total Absences: 0")

        summary_layout.addWidget(self.yearly_label)
        summary_layout.addWidget(self.yearly_absences_label)
        summary_layout.addWidget(self.monthly_label)
        summary_layout.addWidget(self.monthly_absences_label)
        layout.addLayout(summary_layout)

        self.setLayout(layout)
        self.load_employees()

    def load_employees(self):
        try:
            employees = get_all_employees()
            self.employee_selector.clear()
            self.employee_map = {}

            if not employees:
                print("Warning: No employees found in database")
                return

            for emp in employees:
                label = f"{emp['employee_id']} - {emp['full_name']}"
                self.employee_selector.addItem(label)
                self.employee_map[label] = emp['employee_id']

            print(f"Successfully loaded {len(employees)} employees into reports screen")

            # Only call update_report if we have employees and the combo box is ready
            if employees and self.employee_selector.count() > 0:
                # Use QTimer to ensure the combo box is fully initialized
                QTimer.singleShot(100, self.update_report)

        except Exception as e:
            print(f"Error loading employees in reports screen: {e}")
            self.employee_map = {}

    def update_report(self):
        label = self.employee_selector.currentText()

        if not label:
            return

        if label not in self.employee_map:
            print(f"Error: Label '{label}' not found in employee_map")
            print(f"Available keys: {list(self.employee_map.keys())}")
            return

        emp_id = self.employee_map[label]

        now = datetime.datetime.now()
        year = now.year

        # Get yearly summary data for all months
        monthly_data = []
        yearly_total_hours = 0
        yearly_total_absences = 0

        for month in range(1, 13):
            period_start = datetime.date(year, month, 1)
            if month == 12:
                period_end = datetime.date(year + 1, 1, 1)
            else:
                period_end = datetime.date(year, month + 1, 1)

            # Get employee details for the specific month using date range
            details = get_employee_details_by_date_range(emp_id, period_start, period_end)
            hours = details.get('hours', 0)
            absences = details.get('absences', 0)
            monthly_data.append((period_start.strftime('%B'), hours, absences))
            yearly_total_hours += hours
            yearly_total_absences += absences

        # Update monthly summary table (show all months)
        self.monthly_summary_table.setRowCount(len(monthly_data))
        for r, (month, hours, absences) in enumerate(monthly_data):
            self.monthly_summary_table.setItem(r, 0, QTableWidgetItem(month))
            self.monthly_summary_table.setItem(r, 1, QTableWidgetItem(str(hours)))
            self.monthly_summary_table.setItem(r, 2, QTableWidgetItem(str(absences)))

        # Get selected month details
        selected_month = self.month_selector.currentData()
        period_start = datetime.date(year, selected_month, 1)
        if selected_month == 12:
            period_end = datetime.date(year + 1, 1, 1)
        else:
            period_end = datetime.date(year, selected_month + 1, 1)

        # Get detailed daily attendance for selected month
        daily_records = get_employee_monthly_attendance_details(emp_id, period_start, period_end)

        # Update daily attendance table
        self.daily_table.setRowCount(len(daily_records))
        monthly_total_hours = 0
        monthly_total_absences = 0

        for r, record in enumerate(daily_records):
            self.daily_table.setItem(r, 0, QTableWidgetItem(record['date']))
            self.daily_table.setItem(r, 1, QTableWidgetItem(record['check_in']))
            self.daily_table.setItem(r, 2, QTableWidgetItem(record['check_out']))
            self.daily_table.setItem(r, 3, QTableWidgetItem(record['status']))
            self.daily_table.setItem(r, 4, QTableWidgetItem(str(record['daily_hours'])))

            monthly_total_hours += record['daily_hours']
            if record['status'] == 'Absent':
                monthly_total_absences += 1

        # Update summary labels
        self.yearly_label.setText(f"Yearly Total Hours: {yearly_total_hours}")
        self.yearly_absences_label.setText(f"Yearly Total Absences: {yearly_total_absences}")
        self.monthly_label.setText(f"Monthly Total Hours: {round(monthly_total_hours, 2)}")
        self.monthly_absences_label.setText(f"Monthly Total Absences: {monthly_total_absences}")
