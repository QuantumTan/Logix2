# screens/staff_dashboard.py
import sys
from PyQt6.QtWidgets import QWidget, QMessageBox, QApplication, QInputDialog, QHBoxLayout, QVBoxLayout, QFrame, QLabel, \
    QTableWidgetItem, QPushButton
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



    # overrides the base_dashboard method to delete button in the employee management table
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

            # Action cell (no Delete button)
            action_widget = QWidget()
            h = QHBoxLayout(action_widget)
            h.setContentsMargins(0, 0, 0, 0)
            h.setSpacing(4)

            edit_btn = QPushButton("Edit")
            edit_btn.setStyleSheet(
                "QPushButton{background:#60a5fa;color:white;padding:4px 8px;border-radius:6px;font-size:10px;}")
            edit_btn.setFixedWidth(130)

            leave_btn = QPushButton("Edit Leave")
            leave_btn.setStyleSheet(
                "QPushButton{background:#f59e0b;color:white;padding:4px 8px;border-radius:6px;font-size:10px;}")
            leave_btn.setFixedWidth(130)

            edit_btn.clicked.connect(lambda checked, eid=emp_id: self.handle_edit_employee(eid))
            leave_btn.clicked.connect(lambda checked, eid=emp_id: self.handle_edit_leave(eid))

            h.addWidget(edit_btn)
            h.addWidget(leave_btn)
            h.addStretch()
            self.table.setCellWidget(row, 6, action_widget)

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

    # def handle_delete_employee(self, emp_id):
    #     QMessageBox.warning(self, "Permission Denied", "Staff cannot delete employees!")

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