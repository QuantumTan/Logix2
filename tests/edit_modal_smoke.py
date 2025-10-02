import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from src.screens.staff_dashboard import StaffDashboard

new_emp_id = None


def main():
    app = QApplication(sys.argv)
    dash = StaffDashboard()
    dash.show()

    def add_then_edit():
        global new_emp_id
        # Programmatically add an employee
        emp = {
            'id': 12001,  # choose a likely free ID
            'name': 'Test User',
            'department': 'QA',
            'position': 'Tester',
            'image_path': None,
        }
        dash._handle_add_employee(emp)
        new_emp_id = emp['id']
        # Open edit modal
        dash.handle_edit_employee(new_emp_id)

    # Schedule add and then edit
    QTimer.singleShot(200, add_then_edit)
    # Close after a short while
    QTimer.singleShot(1200, dash.close)
    QTimer.singleShot(1400, app.quit)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

