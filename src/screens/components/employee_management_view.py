# screens/components/employee_management_view.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QTableWidget, QHeaderView
from PyQt6.QtCore import Qt


class EmployeeManagementView(QWidget):
    """Encapsulated Employee Management tab UI. Owner wires handlers/data."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        top_btn_layout = QHBoxLayout()
        top_btn_layout.addStretch()
        self.add_emp_btn = QPushButton("Add Employee")
        self.add_emp_btn.setStyleSheet(
            "QPushButton {background:#06b6d4;color:white;padding:8px 16px;"
            "border-radius:8px;font-weight:bold;}"
        )
        top_btn_layout.addWidget(self.add_emp_btn, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addLayout(top_btn_layout)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Search employee...")
        self.search_edit.setFixedHeight(35)
        self.search_edit.setStyleSheet(
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
                border-color: #60a5fa;
                outline: none;
            }
            """
        )
        layout.addWidget(self.search_edit)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Employee ID",
            "Name",
            "Position",
            "Department",
            "Absences",
            "Leave Credits",
            "Actions",
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

