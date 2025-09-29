# screens/emp_details.py
from PyQt6.QtWidgets import (
    QDialog, QLabel, QVBoxLayout, QHBoxLayout,
    QFrame, QPushButton, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap


class EmployeeDetailsModal(QDialog):
    def __init__(self, employee_data, parent=None):
        super().__init__(parent)
        self.employee_data = employee_data
        self.init_ui()
        self.center_on_parent()

    def center_on_parent(self):
        if self.parent():
            parent_geom = self.parent().geometry()
            x = parent_geom.x() + (parent_geom.width() - self.width()) // 2
            y = parent_geom.y() + (parent_geom.height() - self.height()) // 2
            self.move(x, y)
        else:
            screen = self.screen().geometry()
            x = screen.x() + (screen.width() - self.width()) // 2
            y = screen.y() + (screen.height() - self.height()) // 2
            self.move(x, y)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def init_ui(self):
        self.setWindowTitle("Employee Details")
        self.setModal(True)
        self.setFixedSize(1000, 800)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # --- Header ---
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(
                    spread:pad,
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #60a5fa,
                    stop:1 #fca5a5
                );
                border-radius: 0px;
                padding: 20px;
            }
        """)
        header_layout = QHBoxLayout()

        title_label = QLabel("Employee Details")
        title_label.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        title_label.setStyleSheet("color: white; background: transparent; margin-left: 15px;")

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_frame.setLayout(header_layout)

        # --- Scroll Area ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_frame = QFrame()
        content_frame.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                padding: 30px;
            }
        """)
        content_layout = QVBoxLayout()

        # --- Info Card ---
        info_card = QFrame()
        info_card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                padding: 20px;
                border: 1px solid #e5e7eb;
            }
        """)
        info_layout = QHBoxLayout()

        if self.employee_data.get('image_path'):
            img_label = QLabel()
            pixmap = QPixmap(self.employee_data['image_path']).scaled(
                300, 300, Qt.AspectRatioMode.KeepAspectRatio
            )
            img_label.setPixmap(pixmap)
            img_label.setStyleSheet("border: 1px solid #e5e7eb; border-radius: 10px;")
            info_layout.addWidget(img_label)
            info_layout.addSpacing(20)
            img_label.setFixedWidth(300)

        left_info = QVBoxLayout()
        name_label = QLabel("Name")
        name_label.setFont(QFont("Inter", 10))
        name_label.setStyleSheet("color: #6b7280; margin-bottom: 5px;")
        name_value = QLabel(self.employee_data.get("name", "John Doe"))
        name_value.setFont(QFont("Inter", 16, QFont.Weight.Bold))
        name_value.setStyleSheet("color: #111827; margin-bottom: 15px;")

        position_label = QLabel("Position")
        position_label.setFont(QFont("Inter", 10))
        position_label.setStyleSheet("color: #6b7280; margin-bottom: 5px;")
        position_value = QLabel(self.employee_data.get("position", "Missionary"))
        position_value.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        position_value.setStyleSheet("color: #111827; margin-bottom: 20px;")

        dept_label = QLabel("Department")
        dept_label.setFont(QFont("Inter", 10))
        dept_label.setStyleSheet("color: #6b7280; margin-bottom: 5px;")
        dept_value = QLabel(self.employee_data.get("department", "IT"))
        dept_value.setFont(QFont("Inter", 12))
        dept_value.setStyleSheet("color: #111827;")

        left_info.addWidget(name_label)
        left_info.addWidget(name_value)
        left_info.addWidget(position_label)
        left_info.addWidget(position_value)
        left_info.addWidget(dept_label)
        left_info.addWidget(dept_value)

        info_layout.addLayout(left_info)
        info_layout.addStretch()
        info_card.setLayout(info_layout)

        # --- Stats Cards (Absences / Hours / Leave) ---
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)

        absences_card = self.create_stat_card(
            "Absences",
            str(self.employee_data.get('absences', 0)),
            "This month",
            "#fee2e2",
            "#dc2626"
        )
        hours_card = self.create_stat_card(
            "Working Hours",
            f"{self.employee_data.get('hours', 168)}h",
            "This month",
            "#dbeafe",
            "#2563eb"
        )
        leave_card = self.create_stat_card(
            "Leave Credits",
            str(self.employee_data.get("leave_credits", 15)),
            "Days Remaining",
            "#fef3c7",
            "#d97706"
        )

        stats_layout.addWidget(absences_card, 1)
        stats_layout.addWidget(hours_card, 1)
        stats_layout.addWidget(leave_card, 1)

        # --- Performance Summary ---
        performance_card = QFrame()
        performance_card.setStyleSheet("""
            QFrame {
                background-color: #dcfce7;
                border-radius: 10px;
                padding: 20px;
                margin-top: 15px;
            }
        """)
        perf_layout = QVBoxLayout()
        perf_title = QLabel("Performance Summary")
        perf_title.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        perf_title.setStyleSheet("color: #166534; margin-bottom: 15px;")

        metrics_layout = QVBoxLayout()
        attendance_row = self.create_metric_row("Attendance Rate", f"{self.employee_data.get('attendance_rate', 90)}%")
        hours_row = self.create_metric_row("Average Daily Hours", f"{self.employee_data.get('avg_hours', 7.9)} h")
        status_row = self.create_metric_row("Status", self.employee_data.get("status", "Good"))
        metrics_layout.addLayout(attendance_row)
        metrics_layout.addLayout(hours_row)
        metrics_layout.addLayout(status_row)

        perf_layout.addWidget(perf_title)
        perf_layout.addLayout(metrics_layout)
        performance_card.setLayout(perf_layout)

        # add to content layout
        content_layout.addWidget(info_card)
        content_layout.addLayout(stats_layout)
        content_layout.addWidget(performance_card)
        content_layout.addStretch()
        content_frame.setLayout(content_layout)
        scroll.setWidget(content_frame)

        main_layout.addWidget(header_frame)
        main_layout.addWidget(scroll)
        self.setLayout(main_layout)

    def create_stat_card(self, title, value, subtitle, bg_color, text_color):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border-radius: 10px;
                padding: 20px;
            }}
        """)
        layout = QHBoxLayout()

        # Left side (title + subtitle)
        left_layout = QVBoxLayout()
        title_label = QLabel(title)
        title_label.setFont(QFont("Inter", 10, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {text_color}; margin-bottom: 5px;")
        title_label.setWordWrap(True)
        title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        subtitle_label = QLabel(subtitle)
        subtitle_label.setFont(QFont("Inter", 10))
        subtitle_label.setStyleSheet(f"color: {text_color};")
        subtitle_label.setWordWrap(True)
        subtitle_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        left_layout.addWidget(title_label)
        left_layout.addWidget(subtitle_label)

        # Right side (big number)
        value_label = QLabel(value)
        value_label.setFont(QFont("Inter", 24, QFont.Weight.Bold))
        value_label.setStyleSheet(f"color: {text_color};")
        value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        value_label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)

        layout.addLayout(left_layout)
        layout.addWidget(value_label)

        card.setLayout(layout)
        return card

    def create_metric_row(self, label, value):
        row_layout = QHBoxLayout()
        label_widget = QLabel(label)
        label_widget.setFont(QFont("Inter", 12))
        label_widget.setStyleSheet("color: #166534;")

        value_widget = QLabel(value)
        value_widget.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        value_widget.setStyleSheet("color: #166534;")
        value_widget.setAlignment(Qt.AlignmentFlag.AlignRight)

        row_layout.addWidget(label_widget)
        row_layout.addWidget(value_widget)
        row_layout.setContentsMargins(0, 5, 0, 5)
        return row_layout
