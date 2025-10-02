import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from src.screens.admin_dashboard import AdminDashboard

def main():
    app = QApplication(sys.argv)
    dash = AdminDashboard()
    dash.show()

    # Switch to employee management and open Add Employee dialog
    def open_modal():
        dash.switch_tab("employee_management")
        dash.show_add_employee_modal()
    QTimer.singleShot(200, open_modal)

    # Close after a short while
    QTimer.singleShot(800, dash.close)
    QTimer.singleShot(900, app.quit)

    sys.exit(app.exec())

if __name__ == "__main__":
    main()

