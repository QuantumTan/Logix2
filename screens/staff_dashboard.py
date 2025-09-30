# screens/staff_dashboard.py
import sys
from PyQt6.QtWidgets import QWidget, QMessageBox, QApplication, QInputDialog, QHBoxLayout, QVBoxLayout, QFrame, QLabel
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from database.db_queries import update_employee
from .base_dashboard import DashboardBase
from screens.add_employee_modal import AddEmployeeModal
from screens.emp_details import EmployeeDetailsModal

class StaffDashboard(DashboardBase):
    def __init__(self):
        super().__init__(title_suffix="Staff Dashboard")
        # No stat cards setup - removed entirely

        self.setup_attendance_page()
        self.setup_employee_management_page()
        self.setup_reports_page()

        self.logout_btn.clicked.connect(self.handle_logout)
        self.add_emp_btn.clicked.connect(self.show_add_employee_modal)

        self.switch_tab("attendance")

    def show_employee_details(self, emp_id):
        if emp_id in self.employee_data:
            dlg = EmployeeDetailsModal(self.employee_data[emp_id], self)
            dlg.exec()

    def show_add_employee_modal(self):
        dlg = AddEmployeeModal(self)
        dlg.employee_added.connect(self._handle_add_employee)
        dlg.exec()

    def handle_edit_employee(self, emp_id):
        initial = self.employee_data[emp_id]
        modal = AddEmployeeModal(self, initial=initial, mode="edit")
        modal.employee_added.connect(self._handle_update_employee)
        modal.exec()

    def handle_delete_employee(self, emp_id):
        QMessageBox.warning(self, "Permission Denied", "Staff cannot delete employees!")

    def handle_edit_leave(self, emp_id):
        current = self.employee_data[emp_id]['leave_credits']
        new, ok = QInputDialog.getInt(self, "Edit Leave Credits", f"Current: {current}", current, 0, 100)
        if ok:
            update_employee(emp_id, self.employee_data[emp_id]['name'], self.employee_data[emp_id]['position'], self.employee_data[emp_id]['department'], self.employee_data[emp_id].get('image_path'), leave_credits=new)
            self.load_employee_data()
            self.load_employee_table()

    def handle_logout(self):
        from .employee_dashboard import AttendanceDashboard
        self.main_dashboard = AttendanceDashboard()
        self.main_dashboard.showMaximized()
        self.close()

# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     window = StaffDashboard()
#     window.showMaximized()
#     sys.exit(app.exec())