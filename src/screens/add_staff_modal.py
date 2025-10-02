# screens/add_staff_modal.py
# Note: Assuming this is similar to add_employee_modal, but for staff. If not provided, create as below.

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QLineEdit,
    QPushButton, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

class AddStaffModal(QDialog):
    staff_added = pyqtSignal(dict)

    def __init__(self, parent: QWidget | None = None, initial: dict | None = None, mode: str = "add"):
        super().__init__(parent)
        self.setModal(True)
        self.mode = mode if mode in ("add", "edit") else "add"
        self.initial = initial or {}
        self.setWindowTitle("Edit Staff" if self.mode == "edit" else "Add Staff")
        self.setFixedSize(600, 400)

        self._build_ui()
        if self.mode == "edit":
            self._prefill()
        self._center_on_parent()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        card = QFrame()
        card.setStyleSheet("QFrame { background:#f5f6ff; border:1px solid #e5e7eb; border-radius:8px; }")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(22, 18, 22, 18)
        card_layout.setSpacing(16)

        form_col = QVBoxLayout()

        row1 = QHBoxLayout()
        self._full_name = self._labeled_lineedit("Full Name", placeholder="e.g. Jane Doe")
        self._username = self._labeled_lineedit("Username", placeholder="e.g. jane")
        # Make username read-only in edit mode
        if self.mode == "edit":
            self._username[1].setReadOnly(True)
            self._username[1].setStyleSheet("QLineEdit{background:#f3f4f6;border:2px solid #e5e7eb;border-radius:10px;padding:6px 10px;color:#6b7280;}")
        row1.addLayout(self._full_name[0])
        row1.addSpacing(14)
        row1.addLayout(self._username[0])

        row2 = QHBoxLayout()
        self._role = self._labeled_lineedit("Role", placeholder="Staff")
        self._role[1].setText("Staff")  # Set fixed text
        self._role[1].setReadOnly(True)  # Make it non-editable
        self._role[1].setStyleSheet("QLineEdit{background:#f3f4f6;border:2px solid #e5e7eb;border-radius:10px;padding:6px 10px;color:#6b7280;}")
        self._position = self._labeled_lineedit("Position", placeholder="e.g. HR Officer")
        row2.addLayout(self._role[0])
        row2.addSpacing(14)
        row2.addLayout(self._position[0])

        row3 = QHBoxLayout()
        self._password = self._labeled_lineedit("Password",
                                                placeholder="Enter password" if self.mode == "add" else "Leave blank to keep current")
        self._password[1].setEchoMode(QLineEdit.EchoMode.Password)
        row3.addLayout(self._password[0])
        row3.addStretch()

        form_col.addLayout(row1)
        form_col.addSpacing(8)
        form_col.addLayout(row2)
        form_col.addSpacing(8)
        form_col.addLayout(row3)
        form_col.addStretch()

        actions = QHBoxLayout()
        actions.addStretch()
        cancel = QPushButton("Cancel")
        cancel.setStyleSheet(
            "QPushButton{background:#fca5a5;color:white;padding:10px 14px;border-radius:10px;font-weight:bold}")
        add = QPushButton("Save" if self.mode == "edit" else "Add Staff")
        add.setStyleSheet(
            "QPushButton{background:#10b981;color:white;padding:10px 14px;border-radius:10px;font-weight:bold}")
        cancel.clicked.connect(self.reject)
        add.clicked.connect(self._submit)
        actions.addWidget(cancel)
        actions.addSpacing(8)
        actions.addWidget(add)

        card_layout.addLayout(form_col)
        card_layout.addLayout(actions)

        root.addWidget(card)

    def _labeled_lineedit(self, label: str, placeholder: str = ""):
        col = QVBoxLayout()
        lab = QLabel(label)
        lab.setFont(QFont("Inter", 10, QFont.Weight.Bold))
        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        edit.setFixedHeight(40)
        edit.setStyleSheet("QLineEdit{background:white;border:2px solid #e5e7eb;border-radius:10px;padding:6px 10px;} QLineEdit:focus{border-color:#60a5fa;background:#ffffff;}")
        col.addWidget(lab)
        col.addWidget(edit)
        return col, edit

    def _prefill(self):
        self._full_name[1].setText(self.initial.get("full_name", ""))
        self._username[1].setText(self.initial.get("username", ""))
        self._role[1].setText(self.initial.get("role", ""))
        self._position[1].setText(self.initial.get("position", ""))

    def _submit(self):
        full_name = self._full_name[1].text().strip()
        username = self._username[1].text().strip()
        role = self._role[1].text().strip()
        position = self._position[1].text().strip()
        password = self._password[1].text().strip()

        if not full_name or not username or not role or not position:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Validation Error", "Please fill in all required fields.")
            return

        if self.mode == "add" and not password:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Validation Error", "Password is required for new staff.")
            return

        staff = {
            "username": username,
            "full_name": full_name,
            "role": role,
            "position": position,
            "is_active": self.initial.get("is_active", True)  # Preserve is_active status
        }
        if password:
            staff["password"] = password

        self.staff_added.emit(staff)
        self.accept()

    def _center_on_parent(self):
        if self.parent():
            pg = self.parent().geometry()
            self.move(pg.x() + (pg.width() - self.width()) // 2,
                      pg.y() + (pg.height() - self.height()) // 2)
        else:
            scr = self.screen().geometry()
            self.move(scr.x() + (scr.width() - self.width()) // 2,
                      scr.y() + (scr.height() - self.height()) // 2)