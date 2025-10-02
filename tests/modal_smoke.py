import sys
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import QTimer

# Ensure we can import project modules when run from project root
from src.screens.add_employee_modal import AddEmployeeModal

def main():
    app = QApplication(sys.argv)
    parent = QWidget()
    parent.setWindowTitle("Parent Test Window")
    parent.show()

    dlg = AddEmployeeModal(parent)
    dlg.show()

    # Close the dialog and parent shortly after showing
    QTimer.singleShot(200, dlg.close)
    QTimer.singleShot(250, parent.close)
    QTimer.singleShot(300, app.quit)

    sys.exit(app.exec())

if __name__ == "__main__":
    main()

