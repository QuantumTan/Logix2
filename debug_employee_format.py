#!/usr/bin/env python3
"""Debug script to check employee data format"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_queries import get_all_employees

def check_employee_format():
    print("Checking employee data format...")

    employees = get_all_employees()
    print(f"\nFound {len(employees)} employees:")
    for emp in employees:
        print(f"Raw data: {emp}")
        print(f"employee_id: '{emp['employee_id']}'")
        print(f"full_name: '{emp['full_name']}'")
        label = f"{emp['employee_id']} - {emp['full_name']}"
        print(f"Generated label: '{label}'")
        print("---")

if __name__ == "__main__":
    check_employee_format()
