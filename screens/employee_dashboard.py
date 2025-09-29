
import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QSizePolicy, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, QTime, QDate
from PyQt6.QtGui import QFont, QPixmap
from .emp_details import EmployeeDetailsModal
from database.db_queries import get_today_attendance, get_today_stats, get_employee_by_id, get_employee_details, employee_check_in, employee_check_out

class AttendanceDashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LOGIX - Attendance Monitoring System")
        self.setGeometry(200, 100, 1500, 950)

        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
            }
        """)

        main_layout = QVBoxLayout()

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

        # Buttons layout (vertical)
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(10)

        staff_btn = QPushButton("Staff Login")
        staff_btn.setStyleSheet("background-color: white; color: #f87171; padding: 10px 20px; border-radius: 8px; font-weight: bold;")
        staff_btn.setFixedWidth(120)

        admin_btn = QPushButton("Admin Login")
        admin_btn.setStyleSheet("background-color: white; color: #f87171; padding: 10px 20px; border-radius: 8px; font-weight: bold;")
        admin_btn.setFixedWidth(120)

        buttons_layout.addWidget(staff_btn)
        buttons_layout.addWidget(admin_btn)

        right_layout.addLayout(date_layout)
        right_layout.addStretch()
        right_layout.addLayout(buttons_layout)

        header_layout.addLayout(left_layout)
        header_layout.addStretch()
        header_layout.addLayout(right_layout)

        header_frame.setLayout(header_layout)

        # === Check-in Frame ===
        checkin_frame = QFrame()
        checkin_frame.setFixedWidth(400)
        checkin_frame.setFixedHeight(300)
        checkin_frame.setStyleSheet("""
        padding: 20px;
        background-color: white;
        border-radius: 8px;
        border: 1px solid rgba(0, 0, 255, 0.2);
        margin-top: 20px;
        """)

        checkin_main_layout = QVBoxLayout()

        # Top label
        attendance_label = QLabel("Employee Attendance")
        attendance_label.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        attendance_label.setStyleSheet("color: Blue; margin-bottom: 8px; border: transparent;")
        attendance_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Input field
        self.checkin_id = QLineEdit()
        self.checkin_id.setPlaceholderText("Enter Employee ID")
        self.checkin_id.setFixedHeight(60)
        self.checkin_id.setStyleSheet("border: 2px solid #e5e7eb; border-radius: 8px; padding: 10px;")

        # Buttons in a row
        buttons_row = QHBoxLayout()
        checkin_btn = QPushButton("Check In")
        checkin_btn.setStyleSheet("background-color: #10b981; color: white; padding: 10px 20px; border-radius: 8px; margin-top: 20px;")
        checkin_btn.clicked.connect(self.handle_checkin)

        checkout_btn = QPushButton("Check Out")
        checkout_btn.setStyleSheet("background-color: #f87171; color: white; padding: 10px 20px; border-radius: 8px; margin-top: 20px;")
        checkout_btn.clicked.connect(self.handle_checkout)

        buttons_row.addWidget(checkin_btn)
        buttons_row.addWidget(checkout_btn)

        # Assemble
        checkin_main_layout.addWidget(attendance_label)
        checkin_main_layout.addWidget(self.checkin_id)
        checkin_main_layout.addLayout(buttons_row)
        checkin_main_layout.addStretch(1)

        checkin_frame.setLayout(checkin_main_layout)

        # === Stats Layout ===
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)

        # Current Time Card
        self.time_label = QLabel("Current Time\n--:--:-- --")
        self.time_label.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setStyleSheet("background: #eff6ff; color: #3b82f6; font-size: 16px; padding: 20px; border-radius: 10px; margin-top: 20px; margin-bottom: 20px;")

        # Stat Cards (label top left, number bottom right)
        self.present_card, self.present_number = self.create_stat_card(0, "Present", "#dcfce7", "green")
        self.late_card, self.late_number = self.create_stat_card(0, "Late", "#fef3c7", "orange")
        self.absent_card, self.absent_number = self.create_stat_card(0, "Absent", "#fee2e2", "red")

        stats_layout.addWidget(self.time_label)
        stats_layout.addWidget(self.present_card)
        stats_layout.addWidget(self.late_card)
        stats_layout.addWidget(self.absent_card)

        # === Employee Table ===
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Employee ID", "Employee Name", "Check In", "Check Out", "Status", "Action"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # === Add to Main Layout ===
        checkin_row = QHBoxLayout()
        checkin_row.addStretch(1)
        checkin_row.addWidget(checkin_frame)
        checkin_row.addStretch(1)

        main_layout.addWidget(header_frame)
        main_layout.addLayout(checkin_row)
        main_layout.addLayout(stats_layout)
        main_layout.addWidget(self.table)

        self.setLayout(main_layout)

        # Timer to update time
        timer = QTimer(self)
        timer.timeout.connect(self.update_time)
        timer.start(1000)

        # Connect staff/admin login buttons
        staff_btn.clicked.connect(self.show_staff_login)
        admin_btn.clicked.connect(self.show_admin_login)

        # Initial load so table persists across restarts (data pulled from DB)
        self.load_attendance_data()

        # refresh to keep in sync with staff adn admin
        self.attendance_refresh_timer = QTimer(self)
        self.attendance_refresh_timer.setInterval(3000)
        self.attendance_refresh_timer.timeout.connect(self.load_attendance_data)
        self.attendance_refresh_timer.start()

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

    def update_time(self):
        current_time = QTime.currentTime().toString("hh:mm:ss AP")
        self.time_label.setText(f"Current Time\n{current_time}")

    def load_attendance_data(self):
        attendance = get_today_attendance()
        self.table.setRowCount(len(attendance))
        for r, data in enumerate(attendance):
            self.table.setItem(r, 0, QTableWidgetItem(data['employee_id']))
            self.table.setItem(r, 1, QTableWidgetItem(data['full_name']))
            self.table.setItem(r, 2, QTableWidgetItem(data['check_in']))
            self.table.setItem(r, 3, QTableWidgetItem(data['check_out']))
            self.table.setItem(r, 4, QTableWidgetItem(data['status']))
            view_btn = QPushButton("VIEW")
            view_btn.setStyleSheet("background-color: #f87171; color: white; padding: 5px; border-radius: 6px; margin: 2px;")
            view_btn.clicked.connect(lambda checked, emp_id=data['employee_id']: self.show_employee_details(emp_id))
            self.table.setCellWidget(r, 5, view_btn)

        stats = get_today_stats()
        self.present_number.setText(str(stats.get('present', 0)))
        self.late_number.setText(str(stats.get('late', 0)))
        self.absent_number.setText(str(stats.get('absent', 0)))

    def handle_checkin(self):
        emp_id = self.checkin_id.text().strip()
        if not emp_id:
            QMessageBox.warning(self, "Error", "Enter Employee ID")
            return
        if employee_check_in(emp_id):
            QMessageBox.information(self, "Success", "Checked in successfully!")
            self.load_attendance_data()
        else:
            QMessageBox.warning(self, "Error", "Invalid ID, already checked in, or error.")

    def handle_checkout(self):
        emp_id = self.checkin_id.text().strip()
        if not emp_id:
            QMessageBox.warning(self, "Error", "Enter Employee ID")
            return
        if employee_check_out(emp_id):
            QMessageBox.information(self, "Success", "Checked out successfully!")
            self.load_attendance_data()
        else:
            QMessageBox.warning(self, "Error", "Not checked in today or error.")

    def show_employee_details(self, employee_id):
        basic = get_employee_by_id(employee_id)
        if basic:
            details = get_employee_details(employee_id)
            employee_data = {
                'id': basic['employee_id'],
                'name': basic['full_name'],
                'position': basic['position'],
                'department': basic['department'],
                'image_path': basic.get('image_path'),
                **details
            }
            modal = EmployeeDetailsModal(employee_data, self)
            modal.exec()

    # functions for showing screens and dashboards

    def show_staff_login(self):
        from screens.login_screens.staff_login import StaffLoginScreen
        self.staff_login = StaffLoginScreen()
        self.staff_login.login_successful.connect(self.open_staff_dashboard)
        self.staff_login.show()

    def show_admin_login(self):
        from screens.login_screens.admin_login import AdminLoginScreen
        self.admin_login = AdminLoginScreen()
        self.admin_login.login_successful.connect(self.open_admin_dashboard)
        self.admin_login.show()

    def open_staff_dashboard(self):
        from screens.staff_dashboard import StaffDashboard
        self.staff_dashboard = StaffDashboard()
        self.staff_dashboard.show()
        self.close()

    def open_admin_dashboard(self):
        from screens.admin_dashboard import AdminDashboard
        self.admin_dashboard = AdminDashboard()
        self.admin_dashboard.show()
        self.close()

    def closeEvent(self, event):
        try:
            if hasattr(self, 'attendance_refresh_timer'):
                self.attendance_refresh_timer.stop()
        except Exception:
            pass
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AttendanceDashboard()
    window.show()
    sys.exit(app.exec())
