# db_queries.py
"""
Thin compatibility facade that re-exports functions split across smaller modules
(auth, employees, attendance) to avoid a monolithic file. Existing imports
like `from ..database.db_queries import ...` continue to work.
"""
from __future__ import annotations

# Re-export utilities
from .utils import hash_password  # noqa: F401

# Re-export domain functions
from .employees import (
    get_all_employees,
    get_employee_by_id,
    add_employee,
    set_employee_image_path,
    update_employee,
    delete_employee,
    search_employees,
)

from .auth import (
    authenticate_user,
    add_or_update_staff,
    get_all_staff,
    delete_staff,
)

from .attendance import (
    employee_check_in,
    employee_check_out,
    get_employee_details,
    get_department_attendance,
    get_today_attendance,
    get_today_stats,
    get_employee_monthly_hours,
    get_all_employees_hours_for_month,
    get_all_employees_hours_for_year,
    get_employee_yearly_hours,
    get_employee_details_by_date_range,
    get_employee_monthly_attendance_details,
)

__all__ = [
    # utils
    'hash_password',
    # employees
    'get_all_employees', 'get_employee_by_id', 'add_employee', 'set_employee_image_path',
    'update_employee', 'delete_employee', 'search_employees',
    # auth
    'authenticate_user', 'add_or_update_staff', 'get_all_staff', 'delete_staff',
    # attendance
    'employee_check_in', 'employee_check_out', 'get_employee_details', 'get_department_attendance',
    'get_today_attendance', 'get_today_stats', 'get_employee_monthly_hours',
    'get_all_employees_hours_for_month', 'get_all_employees_hours_for_year', 'get_employee_yearly_hours',
    'get_employee_details_by_date_range', 'get_employee_monthly_attendance_details',
]
