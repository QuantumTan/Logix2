#!/usr/bin/env python3
"""Debug script to test reports functionality"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_queries import (
    get_all_employees,
    get_employee_details_by_date_range,
    get_employee_monthly_attendance_details
)
import datetime

def test_reports():
    print("Testing reports functionality...")

    # Test 1: Get all employees
    print("\n1. Testing get_all_employees():")
    employees = get_all_employees()
    print(f"Found {len(employees)} employees:")
    for emp in employees[:3]:  # Show first 3
        print(f"  - {emp['employee_id']}: {emp['full_name']}")

    if not employees:
        print("No employees found! This is why reports are empty.")
        return

    # Test 2: Test date range function with first employee
    first_emp = employees[0]['employee_id']
    print(f"\n2. Testing get_employee_details_by_date_range() for employee {first_emp}:")

    # Test current month
    now = datetime.datetime.now()
    start_date = datetime.date(now.year, now.month, 1)
    if now.month == 12:
        end_date = datetime.date(now.year + 1, 1, 1)
    else:
        end_date = datetime.date(now.year, now.month + 1, 1)

    print(f"Date range: {start_date} to {end_date}")
    details = get_employee_details_by_date_range(first_emp, start_date, end_date)
    print(f"Details: {details}")

    # Test 3: Test detailed attendance function
    print(f"\n3. Testing get_employee_monthly_attendance_details() for employee {first_emp}:")
    daily_records = get_employee_monthly_attendance_details(first_emp, start_date, end_date)
    print(f"Found {len(daily_records)} daily records:")
    for record in daily_records[:5]:  # Show first 5
        print(f"  - {record}")

if __name__ == "__main__":
    test_reports()
