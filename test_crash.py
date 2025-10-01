#!/usr/bin/env python3
"""Test script to isolate the crash issue"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    print("Testing PyQt6 basic import...")
    from PyQt6.QtWidgets import QApplication, QWidget
    print("✓ PyQt6 basic import successful")

    print("Testing database imports...")
    from database.db_queries import get_all_employees
    print("✓ Database imports successful")

    print("Testing employee dashboard import...")
    from screens.employee_dashboard import AttendanceDashboard
    print("✓ Employee dashboard import successful")

    print("Testing QApplication creation...")
    app = QApplication(sys.argv)
    print("✓ QApplication created successfully")

    print("Testing AttendanceDashboard creation...")
    window = AttendanceDashboard()
    print("✓ AttendanceDashboard created successfully")

    print("All tests passed - no crash detected in basic initialization")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
