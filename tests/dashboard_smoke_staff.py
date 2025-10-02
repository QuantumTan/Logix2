import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from src.screens.staff_dashboard import StaffDashboard

def main():
    app = QApplication(sys.argv)
    dash = StaffDashboard()
    dash.show()

    # Open Add Employee modal after the window shows
    QTimer.singleShot(200, dash.show_add_employee_modal)
    # Close dashboard after a short while
    QTimer.singleShot(800, dash.close)
    QTimer.singleShot(900, app.quit)

    sys.exit(app.exec())

if __name__ == "__main__":
    main()

