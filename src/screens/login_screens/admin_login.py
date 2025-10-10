# screens/login_screens/admin_login.py
import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap
from ...database.db_queries import authenticate_user

class AdminLoginScreen(QWidget):
    login_successful = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("LOGIX - Admin Login")
        self.setGeometry(300, 150, 450, 600)
        self.setFixedSize(450, 600)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        container = QFrame()
        container.setStyleSheet("QFrame { background-color: white; border-radius: 20px; margin: 10px; }")

        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        header_frame = self.create_header()

        content_frame = self.create_content()

        container_layout.addWidget(header_frame)
        container_layout.addWidget(content_frame)

        container.setLayout(container_layout)
        main_layout.addWidget(container)

        self.setLayout(main_layout)

        self.setStyleSheet("QWidget { background-color: #f5f5f5; }")

    def create_header(self):
        header_frame = QFrame()
        header_frame.setFixedHeight(180)
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-top-left-radius: 20px;
                border-top-right-radius: 20px;
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
            }
        """)

        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(30, 20, 30, 20)

        logo_title_layout = QHBoxLayout()

        logo_label = QLabel()
        pixmap = QPixmap("assets/logix.png")
        pixmap = pixmap.scaled(60, 90, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        logo_label.setPixmap(pixmap)
        logo_label.setStyleSheet("background-color: transparent; color: #000000;")

        text_layout = QVBoxLayout()

        title_label = QLabel("LOGIX")
        title_label.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #000000; background-color: transparent; margin-bottom: 5px;")

        subtitle1_label = QLabel("Login to access admin management<br>dashboard")
        subtitle1_label.setFont(QFont("Inter", 11))
        subtitle1_label.setStyleSheet("color: #000000; background-color: transparent;")

        text_layout.addWidget(title_label)
        text_layout.addWidget(subtitle1_label)
        text_layout.addStretch()

        logo_title_layout.addWidget(logo_label)
        logo_title_layout.addLayout(text_layout)
        logo_title_layout.addStretch()

        header_layout.addStretch()
        header_layout.addLayout(logo_title_layout)
        header_layout.addStretch()

        header_frame.setLayout(header_layout)
        return header_frame

    def create_content(self):
        content_frame = QFrame()
        content_frame.setStyleSheet("QFrame { background-color: white; }")

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(40, 40, 40, 40)
        content_layout.setSpacing(25)

        username_label = QLabel("Admin Username")
        username_label.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        username_label.setStyleSheet("color: #333333; margin-bottom: 10px;")

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter admin username")
        self.username_input.setFixedHeight(50)
        self.username_input.setStyleSheet("""
            QLineEdit {
                background-color: #f5f5f5;
                border: 2px solid #e0e0e0;
                border-radius: 12px;
                padding: 10px 15px;
                font-size: 14px;
                color: #333333;
            }
            QLineEdit:focus {
                border: 2px solid #60a5fa;
                background-color: white;
            }
        """)

        password_label = QLabel("Password")
        password_label.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        password_label.setStyleSheet("color: #333333; margin-bottom: 10px;")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter admin password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFixedHeight(50)
        self.password_input.setStyleSheet("""
            QLineEdit {
                background-color: #f5f5f5;
                border: 2px solid #e0e0e0;
                border-radius: 12px;
                padding: 10px 15px;
                font-size: 14px;
                color: #333333;
            }
            QLineEdit:focus {
                border: 2px solid #60a5fa;
                background-color: white;
            }
        """)

        self.login_btn = QPushButton("Login as Admin")
        self.login_btn.setFixedHeight(55)
        self.login_btn.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border-radius: 15px;
                border: none;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        self.login_btn.clicked.connect(self.handle_login)

        content_layout.addWidget(username_label)
        content_layout.addWidget(self.username_input)
        content_layout.addWidget(password_label)
        content_layout.addWidget(self.password_input)
        content_layout.addWidget(self.login_btn)
        content_layout.addStretch()

        content_frame.setLayout(content_layout)
        return content_frame

    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Validation Error", "Please enter both username and password.")
            return

        if authenticate_user(username, password, 'Admin'):
            self.login_successful.emit()
            self.close()
        else:
            QMessageBox.warning(self, "Login Failed", "Invalid credentials.")

# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     window = AdminLoginScreen()
#     window.show()
#     sys.exit(app.exec())