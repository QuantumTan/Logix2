# screens/add_employee_modal.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QLineEdit,
    QPushButton, QFileDialog, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap

class AddEmployeeModal(QDialog):
    employee_added = pyqtSignal(dict)

    def __init__(self, parent: QWidget | None = None, initial: dict | None = None, mode: str = "add"):
        try:
            super().__init__(parent)
            self.setModal(True)
            self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
            self.mode = mode if mode in ("add", "edit") else "add"
            self.initial = initial or {}
            self.setWindowTitle("Edit Employee" if self.mode == "edit" else "Add Employee")
            self.setFixedSize(720, 460)

            self._selected_image_path: str | None = None
            self._build_ui()
            if self.mode == "edit":
                self._prefill()
        except Exception as e:
            print(f"Error initializing AddEmployeeModal: {e}")
            # Try minimal initialization
            super().__init__(parent)
            self.setWindowTitle("Add Employee")
            self.setFixedSize(400, 300)
            layout = QVBoxLayout(self)
            label = QLabel("Modal failed to load properly. Please try again.")
            layout.addWidget(label)
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(self.reject)
            layout.addWidget(close_btn)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        card = QFrame()
        card.setStyleSheet("QFrame { background:#f5f6ff; border:1px solid #e5e7eb; border-radius:8px; }")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(22, 18, 22, 18)
        card_layout.setSpacing(16)

        img_row = QHBoxLayout()
        img_col = QVBoxLayout()
        img_lbl = QLabel("Upload Image")
        # Use default system font to avoid font issues
        img_lbl.setFont(QFont())
        self._img_box = QLabel()
        self._img_box.setFixedSize(140, 140)
        self._img_box.setStyleSheet("background:white;border:1px dashed #cbd5e1;border-radius:8px; color:#9ca3af;")
        self._img_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._img_box.setText("Select")

        pick_btn = QPushButton("Browse...")
        pick_btn.setStyleSheet("QPushButton{background:#3b82f6;color:white;padding:6px 10px;border-radius:6px;}")
        pick_btn.clicked.connect(self._pick_image)

        img_col.addWidget(img_lbl)
        img_col.addWidget(self._img_box)
        img_col.addWidget(pick_btn)
        img_col.addStretch()

        form_col = QVBoxLayout()

        row1 = QHBoxLayout()
        self._name = self._labeled_lineedit("Full name", placeholder="e.g. Jane Doe")
        self._position = self._labeled_lineedit("Position", placeholder="e.g. Developer")
        row1.addLayout(self._name[0])
        row1.addSpacing(14)
        row1.addLayout(self._position[0])

        row2 = QHBoxLayout()
        self._dept = self._labeled_lineedit("Department", placeholder="e.g. IT")
        row2.addLayout(self._dept[0])
        row2.addStretch()

        form_col.addLayout(row1)
        form_col.addSpacing(8)
        form_col.addLayout(row2)
        form_col.addStretch()

        img_row.addLayout(img_col)
        img_row.addSpacing(20)
        img_row.addLayout(form_col)

        actions = QHBoxLayout()
        actions.addStretch()
        cancel = QPushButton("Cancel")
        cancel.setStyleSheet("QPushButton{background:#fca5a5;color:white;padding:10px 14px;border-radius:10px;font-weight:bold}")
        add = QPushButton("Save" if self.mode == "edit" else "Add employee")
        add.setStyleSheet("QPushButton{background:#10b981;color:white;padding:10px 14px;border-radius:10px;font-weight:bold}")
        cancel.clicked.connect(self.reject)
        add.clicked.connect(self._submit)
        actions.addWidget(cancel)
        actions.addSpacing(8)
        actions.addWidget(add)

        card_layout.addLayout(img_row)
        card_layout.addLayout(actions)

        root.addWidget(card)

    def _labeled_lineedit(self, label: str, placeholder: str = ""):
        col = QVBoxLayout()
        lab = QLabel(label)
        lab.setFont(QFont())
        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        edit.setFixedHeight(40)
        edit.setStyleSheet("QLineEdit{background:white;border:2px solid #e5e7eb;border-radius:10px;padding:6px 10px;} QLineEdit:focus{border-color:#60a5fa;background:#ffffff;}")
        col.addWidget(lab)
        col.addWidget(edit)
        return col, edit

    def _prefill(self):
        name = self.initial.get("name", "")
        dept = self.initial.get("department", "")
        pos = self.initial.get("position", "")
        self._name[1].setText(name)
        self._dept[1].setText(dept)
        self._position[1].setText(pos)
        if self.initial.get("image_path"):
            pm = QPixmap(self.initial["image_path"])
            if not pm.isNull():
                pm = pm.scaled(140, 140, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self._img_box.setPixmap(pm)
                self._img_box.setText("")
                self._selected_image_path = self.initial["image_path"]
            else:
                self._img_box.setText("Image failed to load")

    def _pick_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            pm = QPixmap(path)
            if not pm.isNull():
                pm = pm.scaled(140, 140, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self._img_box.setPixmap(pm)
                self._img_box.setText("")
                self._selected_image_path = path
            else:
                self._img_box.setText("Image failed to load")
                self._selected_image_path = None

    def _submit(self):
        name = self._name[1].text().strip()
        dept = self._dept[1].text().strip()
        pos = self._position[1].text().strip()

        if not name or not dept or not pos:
            for widget in (self._name[1], self._dept[1], self._position[1]):
                if not widget.text().strip():
                    widget.setStyleSheet("QLineEdit{background:#fff1f2;border:2px solid #ef4444;border-radius:10px;padding:6px 10px;}")
            return

        if self.mode == "edit" and self.initial.get("id") is not None:
            try:
                new_id = int(self.initial["id"])
            except Exception:
                new_id = self._generate_id()
        else:
            new_id = self._generate_id()
        emp = {"id": new_id, "name": name, "department": dept, "position": pos, "image_path": self._selected_image_path}
        self.employee_added.emit(emp)
        self.accept()

    def _generate_id(self) -> int:
        parent = self.parent()
        if parent and hasattr(parent, "employee_data") and isinstance(parent.employee_data, dict) and parent.employee_data:
            try:
                nums = [int(k) for k in parent.employee_data.keys()]
                base = max(nums) + 1 if nums else 10000
                return int(base)
            except Exception:
                return 10000
        return 10000
