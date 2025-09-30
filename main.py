# main.py
import sys
import os
import traceback
from PyQt6.QtWidgets import QApplication


def main():
    """Main function to run the LOGIX Attendance Monitoring System"""
    try:
        # Add the current directory to Python path
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))

        from database.db_setup import create_database_and_tables
        from screens.employee_dashboard import AttendanceDashboard

        print("Initializing database...")
        create_database_and_tables()

        print("Starting application...")
        app = QApplication(sys.argv)

        # Show the main employee dashboard
        window = AttendanceDashboard()
        window.showMaximized()

        # Run the application
        sys.exit(app.exec())

    except Exception as e:
        print(f"Error starting application: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()