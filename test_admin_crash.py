#!/usr/bin/env python3
"""Test admin dashboard specifically"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    print("Testing admin dashboard import...")
    from screens.admin_dashboard import AdminDashboard
    print("✓ Admin dashboard import successful")

    print("Testing base dashboard import...")
    from screens.base_dashboard import DashboardBase
    print("✓ Base dashboard import successful")

    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)

    print("Testing AdminDashboard creation...")
    admin_dashboard = AdminDashboard()
    print("✓ AdminDashboard created successfully")

    print("All admin dashboard tests passed")

except Exception as e:
    print(f"ERROR in admin dashboard: {e}")
    import traceback
    traceback.print_exc()
