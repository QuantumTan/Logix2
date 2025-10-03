# screens/admin_dashboard.py
import sys
from PyQt6.QtWidgets import QWidget, QMessageBox, QHBoxLayout, QPushButton, QTableWidgetItem, QTableWidget, QHeaderView, \
    QVBoxLayout, QLineEdit, QApplication, QInputDialog, QFrame, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from .base_dashboard import DashboardBase
from .add_employee_modal import AddEmployeeModal
from .emp_details import EmployeeDetailsModal
from .add_staff_modal import AddStaffModal
from .change_password_modal import ChangePasswordModal
from ..database.db_queries import get_all_staff, add_or_update_staff, delete_staff, update_employee, delete_employee, \
    get_employee_by_id, get_employee_details


class AdminDashboard(DashboardBase):
    def __init__(self):
        super().__init__(title_suffix="Admin Dashboard")
        # No stat cards setup - removed entirely

        self.setup_attendance_page()
        self.setup_employee_management_page()
        self.setup_reports_page()
        self._setup_staff_accounts_tab()

        self.logout_btn.clicked.connect(self.handle_logout)
        self.add_emp_btn.clicked.connect(self.show_add_employee_modal)

        self.switch_tab("attendance")

    def _setup_staff_accounts_tab(self):
        self.staff_accounts_btn = QPushButton("Staff Accounts")
        self.staff_accounts_btn.setStyleSheet(
            "QPushButton { background-color: white; color: red; padding: 5px 30px; border-radius: 15px; font-weight: bold; border: 2px solid red; height: 30px; } QPushButton:hover { background-color: #fef2f2; }")
        self.staff_accounts_btn.clicked.connect(lambda: self.switch_tab("staff_accounts"))
        self.tabs_layout.insertWidget(3, self.staff_accounts_btn)
        self.tab_buttons["staff_accounts"] = self.staff_accounts_btn

        self.staff_accounts_page = QWidget()
        staff_layout = QVBoxLayout(self.staff_accounts_page)

        # === Add Staff button (top-right) ===
        top_btn_layout = QHBoxLayout()
        top_btn_layout.addStretch()  # pushes button to the right
        self.add_staff_btn = QPushButton("Add Staff")
        self.add_staff_btn.setStyleSheet(
            """
            QPushButton {background:#06b6d4;color:white;padding:8px 16px;
            border-radius:8px;font-weight:bold;}          """
        )
        self.add_staff_btn.clicked.connect(self.show_add_staff_modal)
        top_btn_layout.addWidget(self.add_staff_btn, alignment=Qt.AlignmentFlag.AlignRight)
        staff_layout.addLayout(top_btn_layout)

        # === Search bar (full width below button) ===
        self.staff_search = QLineEdit()
        self.staff_search.setPlaceholderText("🔍 Search staff...")
        self.staff_search.setFixedHeight(35)
        self.staff_search.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 2px solid #e5e7eb;

                padding: 8px 12px;
                border-radius: 800px;
                font-size: 14px;
                color: #374151;
            }
            QLineEdit:focus {
                border-color: #60a5fa;
                outline: none;
            }
        """)
        self.staff_search.textChanged.connect(self.filter_staff_table)
        staff_layout.addWidget(self.staff_search)

        # === Staff table ===
        self.staff_table = QTableWidget()
        self.staff_table.setColumnCount(5)
        self.staff_table.setHorizontalHeaderLabels(["Full Name", "Username", "Role", "Position", "Action"])
        self.staff_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.staff_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.load_staff_table()

        staff_layout.addWidget(self.staff_table)
        self.content_stack.addWidget(self.staff_accounts_page)

    def load_staff_table(self):
        staff = get_all_staff()
        self.staff_table.setRowCount(len(staff))
        for r, s in enumerate(staff):
            self.staff_table.setItem(r, 0, QTableWidgetItem(s['full_name']))
            self.staff_table.setItem(r, 1, QTableWidgetItem(s['username']))
            self.staff_table.setItem(r, 2, QTableWidgetItem(s['role']))
            self.staff_table.setItem(r, 3, QTableWidgetItem(s['position']))

            action_widget = QWidget()
            h = QHBoxLayout(action_widget)
            h.setContentsMargins(0, 0, 0, 0)
            h.setSpacing(4)

            edit_btn = QPushButton("Edit")
            edit_btn.setStyleSheet(
                "QPushButton{background:#60a5fa;color:white;padding:4px 8px;border-radius:6px;font-size:10px;}")
            edit_btn.setFixedWidth(100)

            change_pwd_btn = QPushButton("🔑 Password")
            change_pwd_btn.setStyleSheet(
                "QPushButton{background:#f59e0b;color:white;padding:4px 8px;border-radius:6px;font-size:10px;}")
            change_pwd_btn.setFixedWidth(100)

            delete_btn = QPushButton("Delete")
            delete_btn.setStyleSheet(
                "QPushButton{background:#ef4444;color:white;padding:4px 8px;border-radius:6px;font-size:10px;}")
            delete_btn.setFixedWidth(100)

            username = s['username']
            edit_btn.clicked.connect(self._make_edit_staff_handler(username))
            change_pwd_btn.clicked.connect(self._make_change_password_handler(username))
            delete_btn.clicked.connect(self._make_delete_staff_handler(username))

            h.addWidget(edit_btn)
            h.addWidget(change_pwd_btn)
            h.addWidget(delete_btn)
            h.addStretch()
            self.staff_table.setCellWidget(r, 4, action_widget)

        self.filter_staff_table()  # Apply any initial filter

    def filter_staff_table(self):
        search_text = self.staff_search.text().lower()
        for row in range(self.staff_table.rowCount()):
            match = False
            for col in range(4):  # Columns: Full Name, Username, Role, Position
                item = self.staff_table.item(row, col)
                if item and search_text in item.text().lower():
                    match = True
                    break
            self.staff_table.setRowHidden(row, not match)

    def show_add_staff_modal(self):
        dlg = AddStaffModal(self)
        dlg.staff_added.connect(self._handle_add_staff)
        dlg.exec()

    def _make_edit_staff_handler(self, username):
        def handler():
            try:
                from ..database.db_config import get_db_connection
                conn = get_db_connection()
                if conn:
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT * FROM staff_users WHERE username = %s", (username,))
                        complete_user = cursor.fetchone()
                    conn.close()

                    if complete_user:
                        dlg = AddStaffModal(self, initial=complete_user, mode="edit")
                        dlg.staff_added.connect(self._handle_update_staff)
                        dlg.exec()
            except Exception as e:
                print(f"Error in edit staff handler: {e}")
                QMessageBox.critical(self, "Error", f"Failed to load staff data: {str(e)}")

        return handler

    def _make_change_password_handler(self, username):
        def handler():
            staff = get_all_staff()
            user = next((s for s in staff if s['username'] == username), None)
            if user:
                modal = ChangePasswordModal(self, username=username, full_name=user['full_name'])
                modal.password_changed.connect(
                    lambda u, p: self._update_staff_password(u, user, p))
                modal.exec()

        return handler

    def _update_staff_password(self, username, user, new_password):
        """Handle staff password update with proper error handling"""
        try:
            add_or_update_staff(username, user['full_name'], user['role'], user['position'], new_password, True, mode='update')
            QMessageBox.information(self, "Success", f"Password updated successfully for {user['full_name']}")
            self.load_staff_table()
        except Exception as e:
            print(f"Error updating password: {e}")
            QMessageBox.critical(self, "Error", f"Failed to update password: {str(e)}")

    def _make_delete_staff_handler(self, username):
        def handler():
            if QMessageBox.warning(self, "Confirm", "Delete staff?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
                delete_staff(username)
                self.load_staff_table()

        return handler

    def _handle_add_staff(self, staff):
        try:
            add_or_update_staff(staff['username'], staff['full_name'], staff['role'], staff['position'], staff['password'], True, mode='add')
            QMessageBox.information(self, "Success", f"Staff member {staff['full_name']} added successfully!")
            self.load_staff_table()
        except Exception as e:
            print(f"Error adding staff: {e}")
            QMessageBox.critical(self, "Error", f"Failed to add staff: {str(e)}")

    def _handle_update_staff(self, staff):
        try:
            # Convert is_active from database integer (1/0) to boolean, then back to what the function expects
            is_active = bool(staff.get('is_active', True))
            add_or_update_staff(
                staff['username'],
                staff['full_name'],
                staff['role'],
                staff['position'],
                staff.get('password'),
                is_active,
                mode='update'
            )
            QMessageBox.information(self, "Success", f"Staff member {staff['full_name']} updated successfully!")
            self.load_staff_table()
        except Exception as e:
            print(f"Error updating staff: {e}")
            QMessageBox.critical(self, "Error", f"Failed to update staff: {str(e)}")

    def switch_tab(self, tab_name):
        if tab_name == "staff_accounts":
            for btn in self.tab_buttons.values():
                if btn != self.staff_accounts_btn:
                    btn.setStyleSheet(
                        "QPushButton { background-color: white; color: #f87171; padding: 5px 30px; border-radius: 15px; font-weight: bold; border: 2px solid #f87171; height: 30px; } QPushButton:hover { background-color: #fef2f2; }")
            self.staff_accounts_btn.setStyleSheet(
                "QPushButton { background-color: #f87171; color: white; padding: 5px 30px; border-radius: 15px; font-weight: bold; border: 2px solid #f87171; height: 30px; } QPushButton:hover { background-color: #ef4444; }")
            self.content_stack.setCurrentWidget(self.staff_accounts_page)
            self.current_tab = tab_name
            return
        super().switch_tab(tab_name)

    def show_employee_details(self, emp_id):
        basic = get_employee_by_id(emp_id)
        if basic:
            details = get_employee_details(emp_id)
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

    def show_add_employee_modal(self):
        try:
            print("[AdminDashboard] Opening AddEmployeeModal (non-blocking)...")
            dlg = AddEmployeeModal(self)
            dlg.setWindowModality(Qt.WindowModality.ApplicationModal)
            dlg.employee_added.connect(self._handle_add_employee)
            if not hasattr(self, '_open_dialogs'):
                self._open_dialogs = []
            self._open_dialogs.append(dlg)
            dlg.finished.connect(lambda _=0, d=dlg: self._open_dialogs.remove(d) if hasattr(self, '_open_dialogs') and d in self._open_dialogs else None)
            dlg.show()
            print("[AdminDashboard] Dialog shown.")
        except Exception as e:
            print(f"[AdminDashboard] Error showing AddEmployeeModal: {e}")

    def _handle_add_employee(self, emp):
        """Persist a newly added employee (admin) and refresh the table."""
        try:
            from ..database.db_queries import add_employee, set_employee_image_path
            import os, shutil

            print(f"[AdminDashboard] Adding employee: {emp}")

            image_dir = 'assets/employees'
            os.makedirs(image_dir, exist_ok=True)

            # Insert first to get DB-generated employee_id
            new_id = add_employee(
                full_name=emp['name'],
                position=emp['position'],
                department=emp['department'],
                leave_credits=15,
                is_active=True
            )
            if not new_id:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Error",
                    "Failed to add employee to database.\n\n"
                    "Check the console for detailed error messages.")
                return

            # Copy image (if any) and update image_path
            img_path = emp.get('image_path')
            if img_path and os.path.isfile(img_path):
                ext = os.path.splitext(img_path)[1]
                saved_image_path = os.path.join(image_dir, f"{new_id}{ext}")
                try:
                    shutil.copy(img_path, saved_image_path)
                    print(f"[AdminDashboard] Image copied to: {saved_image_path}")
                    set_employee_image_path(new_id, saved_image_path)
                except Exception as e:
                    print(f"[AdminDashboard] Warning: failed to copy image: {e}")

            print(f"[AdminDashboard] Employee added successfully, refreshing table...")
            self.load_employee_data()
            self.load_employee_table()
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Success", f"Employee {emp['name']} added successfully!")
        except Exception as e:
            print(f"[AdminDashboard] Error adding employee: {e}")
            import traceback
            traceback.print_exc()
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Failed to add employee:\n{str(e)}")

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

    def _handle_update_employee(self, emp: dict):
        """Persist edits to an existing employee and refresh the table.
        emp: dict with keys id, name, department, position, image_path
        """
        try:
            import os
            import shutil
            image_dir = 'assets/employees'
            os.makedirs(image_dir, exist_ok=True)

            img_path = emp.get('image_path')
            # If a new image was picked (not already copied under assets/employees), copy it
            if img_path and not os.path.normpath(img_path).startswith(os.path.normpath(image_dir)):
                ext = os.path.splitext(img_path)[1]
                new_path = os.path.join(image_dir, f"{str(emp['id'])}{ext}")
                try:
                    shutil.copy(img_path, new_path)
                    emp['image_path'] = new_path
                except Exception as e:
                    print(f"[AdminDashboard] Warning: failed to copy new image: {e}")
                    # Keep existing path if copy fails

            # Update in DB
            update_employee(
                emp['id'],
                emp['name'],
                emp['position'],
                emp['department'],
                emp.get('image_path')
            )

            # Refresh UI
            self.load_employee_data()
            self.load_employee_table()
            QMessageBox.information(self, "Success", f"Employee {emp['name']} updated successfully!")
        except Exception as e:
            print(f"[AdminDashboard] Error updating employee: {e}")
            QMessageBox.critical(self, "Error", "Failed to update employee.")

    def handle_delete_employee(self, emp_id):
        if QMessageBox.warning(self, "Confirm Delete", "Are you sure?",
                               QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            delete_employee(emp_id)
            self.load_employee_data()
            self.load_employee_table()

    def handle_edit_leave(self, emp_id):
        current = self.employee_data[emp_id]['leave_credits']
        new, ok = QInputDialog.getInt(self, "Edit Leave Credits", f"Current: {current}", current, 0, 100)
        if ok:
            update_employee(emp_id, self.employee_data[emp_id]['name'], self.employee_data[emp_id]['position'],
                            self.employee_data[emp_id]['department'], self.employee_data[emp_id].get('image_path'),
                            leave_credits=new)
            self.load_employee_data()
            self.load_employee_table()

    def handle_logout(self):
        from .employee_dashboard import AttendanceDashboard
        self.main_dashboard = AttendanceDashboard()
        self.main_dashboard.showMaximized()
        self.close()
