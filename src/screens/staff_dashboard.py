# screens/staff_dashboard.py
from PyQt6.QtWidgets import QWidget, QMessageBox, QInputDialog, QHBoxLayout, QTableWidgetItem, QPushButton
from PyQt6.QtCore import Qt

from ..database.db_queries import update_employee, get_employee_by_id, get_employee_details
from .base_dashboard import DashboardBase
from .add_employee_modal import AddEmployeeModal
from .emp_details import EmployeeDetailsModal

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
            self.table.setItem(row, 0, QTableWidgetItem(str(emp['id'])))
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

    def show_add_employee_modal(self):
        try:
            print("[StaffDashboard] Opening AddEmployeeModal (non-blocking)...")
            dlg = AddEmployeeModal(self)
            dlg.setWindowModality(Qt.WindowModality.ApplicationModal)
            dlg.employee_added.connect(self._handle_add_employee)
            # keep reference to prevent GC
            if not hasattr(self, '_open_dialogs'):
                self._open_dialogs = []
            self._open_dialogs.append(dlg)
            dlg.finished.connect(lambda _=0, d=dlg: self._open_dialogs.remove(d) if hasattr(self, '_open_dialogs') and d in self._open_dialogs else None)
            dlg.show()
            print("[StaffDashboard] Dialog shown.")
        except Exception as e:
            print(f"[StaffDashboard] Error showing AddEmployeeModal: {e}")

    def handle_edit_employee(self, emp_id):
        initial = self.employee_data[emp_id]
        modal = AddEmployeeModal(self, initial=initial, mode="edit")
        modal.setWindowModality(Qt.WindowModality.ApplicationModal)
        modal.employee_added.connect(self._handle_update_employee)
        if not hasattr(self, '_open_dialogs'):
            self._open_dialogs = []
        self._open_dialogs.append(modal)
        modal.finished.connect(lambda _=0, d=modal: self._open_dialogs.remove(d) if hasattr(self, '_open_dialogs') and d in self._open_dialogs else None)
        modal.show()

    def _handle_add_employee(self, emp):
        """Persist a newly added employee and refresh the table.
        emp: dict with keys name, department, position, image_path (id from modal is ignored)
        """
        try:
            from ..database.db_queries import add_employee, set_employee_image_path
            import os, shutil
            image_dir = 'assets/employees'
            os.makedirs(image_dir, exist_ok=True)

            # First, insert employee to get DB-assigned ID
            new_id = add_employee(
                full_name=emp['name'],
                position=emp['position'],
                department=emp['department'],
                leave_credits=15,
                is_active=True
            )
            if not new_id:
                QMessageBox.critical(self, "Error", "Failed to add employee to database.")
                return

            # If an image is provided, copy it and update image_path
            img_path = emp.get('image_path')
            if img_path and os.path.isfile(img_path):
                ext = os.path.splitext(img_path)[1]
                saved_image_path = os.path.join(image_dir, f"{new_id}{ext}")
                try:
                    shutil.copy(img_path, saved_image_path)
                    # Update DB with the saved image path
                    set_employee_image_path(new_id, saved_image_path)
                except Exception as e:
                    print(f"[StaffDashboard] Warning: failed to copy image: {e}")

            # Refresh in-memory and table
            self.load_employee_data()
            self.load_employee_table()
            QMessageBox.information(self, "Success", f"Employee {emp['name']} added successfully!")
        except Exception as e:
            print(f"[StaffDashboard] Error adding employee: {e}")

    def _handle_update_employee(self, emp):
        import os
        import shutil
        image_dir = 'assets/employees'
        os.makedirs(image_dir, exist_ok=True)
        if emp.get('image_path') and not emp['image_path'].startswith(image_dir):
            ext = os.path.splitext(emp['image_path'])[1]
            new_path = os.path.join(image_dir, f"{str(emp['id'])}{ext}")
            shutil.copy(emp['image_path'], new_path)
            emp['image_path'] = new_path
        update_employee(emp['id'], emp['name'], emp['position'], emp['department'], emp['image_path'])
        self.load_employee_data()
        self.load_employee_table()


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
