# screens/change_password_modal.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QLineEdit,
    QPushButton, QWidget, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class ChangePasswordModal(QDialog):
    password_changed = pyqtSignal(str, str)  # username, new_password

    def __init__(self, parent: QWidget | None = None, username: str = "", full_name: str = ""):
        super().__init__(parent)
        self.setModal(True)
        self.username = username
        self.full_name = full_name
        self.setWindowTitle(f"Change Password - {full_name}")
        self.setFixedSize(450, 300)

        self._build_ui()
        self._center_on_parent()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        card = QFrame()
        card.setStyleSheet("QFrame { background:#f8fafc; border:1px solid #e5e7eb; border-radius:10px; }")
        v = QVBoxLayout(card)
        v.setContentsMargins(18, 18, 18, 18)
        v.setSpacing(16)

        header_label = QLabel(f"Change password for: {self.full_name} ({self.username})")
        header_label.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        header_label.setStyleSheet("color: #374151; margin-bottom: 10px;")
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(header_label)

        new_password_label = QLabel("New Password")
        new_password_label.setFont(QFont("Inter", 10, QFont.Weight.Bold))
        self.new_password_edit = QLineEdit()
        self.new_password_edit.setPlaceholderText("Enter new password")
        self.new_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password_edit.setFixedHeight(40)
        self.new_password_edit.setStyleSheet(
            "QLineEdit{background:white;border:2px solid #e5e7eb;border-radius:10px;padding:6px 10px;}"
            "QLineEdit:focus{border-color:#06b6d4;}"
        )

        confirm_password_label = QLabel("Confirm New Password")
        confirm_password_label.setFont(QFont("Inter", 10, QFont.Weight.Bold))
        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setPlaceholderText("Confirm new password")
        self.confirm_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_edit.setFixedHeight(40)
        self.confirm_password_edit.setStyleSheet(
            "QLineEdit{background:white;border:2px solid #e5e7eb;border-radius:10px;padding:6px 10px;}"
            "QLineEdit:focus{border-color:#06b6d4;}"
        )

        v.addWidget(new_password_label)
        v.addWidget(self.new_password_edit)
        v.addWidget(confirm_password_label)
        v.addWidget(self.confirm_password_edit)
        v.addStretch()

        actions = QHBoxLayout()
        actions.addStretch()
        cancel = QPushButton("Cancel")
        cancel.setStyleSheet("QPushButton{background:#94a3b8;color:white;padding:10px 14px;border-radius:10px;font-weight:bold}")
        change_btn = QPushButton("Change Password")
        change_btn.setStyleSheet("QPushButton{background:#06b6d4;color:white;padding:10px 14px;border-radius:10px;font-weight:bold}")
        cancel.clicked.connect(self.reject)
        change_btn.clicked.connect(self._change_password)
        actions.addWidget(cancel)
        actions.addSpacing(8)
        actions.addWidget(change_btn)

        v.addLayout(actions)
        root.addWidget(card)

    def _change_password(self):
        new_password = self.new_password_edit.text().strip()
        confirm_password = self.confirm_password_edit.text().strip()

        if not new_password:
            QMessageBox.warning(self, "Validation Error", "Please enter a new password.")
            self.new_password_edit.setStyleSheet("QLineEdit{background:#fff1f2;border:2px solid #ef4444;border-radius:10px;padding:6px 10px;}")
            return

        if new_password != confirm_password:
            QMessageBox.warning(self, "Validation Error", "Passwords do not match.")
            self.new_password_edit.setStyleSheet("QLineEdit{background:#fff1f2;border:2px solid #ef4444;border-radius:10px;padding:6px 10px;}")
            self.confirm_password_edit.setStyleSheet("QLineEdit{background:#fff1f2;border:2px solid #ef4444;border-radius:10px;padding:6px 10px;}")
            return

        if len(new_password) < 4:
            QMessageBox.warning(self, "Validation Error", "Password must be at least 4 characters long.")
            self.new_password_edit.setStyleSheet("QLineEdit{background:#fff1f2;border:2px solid #ef4444;border-radius:10px;padding:6px 10px;}")
            return

        self.password_changed.emit(self.username, new_password)
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