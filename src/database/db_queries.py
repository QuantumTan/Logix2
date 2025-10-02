# db_queries.py
import pymysql
from datetime import datetime
import hashlib

from .db_config import get_db_connection


def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


# ============================================
# EMPLOYEE FUNCTIONS (with soft delete)
# ============================================

def get_all_employees():
    """Fetch all ACTIVE employees from the database."""
    conn = get_db_connection()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM employees WHERE is_active = TRUE")
            employees = cursor.fetchall()
        conn.close()
        return employees
    return []


def update_employee(employee_id, full_name, position, department, image_path=None, leave_credits=None):
    """Update an existing employee."""
    conn = get_db_connection()
    if conn:
        with conn.cursor() as cursor:
            set_clause = "full_name = %s, position = %s, department = %s"
            params = [full_name, position, department]
            if image_path is not None:
                set_clause += ", image_path = %s"
                params.append(image_path)
            if leave_credits is not None:
                set_clause += ", leave_credits = %s"
                params.append(leave_credits)
            params.append(employee_id)
            cursor.execute(f"UPDATE employees SET {set_clause} WHERE employee_id = %s", params)
            conn.commit()
        conn.close()


def delete_employee(employee_id):
    """Soft delete an employee (mark as inactive instead of deleting)."""
    conn = get_db_connection()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE employees SET is_active = FALSE WHERE employee_id = %s", (employee_id,))
            conn.commit()
        conn.close()


def employee_check_in(employee_id):
    """Handle employee check-in, compute status, and insert record if not already checked in."""
    conn = get_db_connection()
    if conn:
        with conn.cursor() as cursor:
            # Check if employee exists AND is active
            cursor.execute("SELECT * FROM employees WHERE employee_id = %s AND is_active = TRUE", (employee_id,))
            if not cursor.fetchone():
                return False
            # Check if already checked in today
            cursor.execute("SELECT * FROM attendance_records WHERE employee_id = %s AND date = CURDATE()",
                           (employee_id,))
            if cursor.fetchone():
                return False
            check_in = datetime.now()
            # Assume office start time is 8:00 AM
            start_time = check_in.replace(hour=8, minute=0, second=0, microsecond=0)
            late_threshold = start_time.replace(minute=15)
            status = 'Late' if check_in > late_threshold else 'Present'
            cursor.execute("""
                           INSERT INTO attendance_records (employee_id, check_in, status, date)
                           VALUES (%s, %s, %s, CURDATE())
                           """, (employee_id, check_in, status))
            conn.commit()
        conn.close()
        return True
    return False


def employee_check_out(employee_id):
    """Handle employee check-out if checked in and not yet checked out."""
    conn = get_db_connection()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                           SELECT record_id
                           FROM attendance_records
                           WHERE employee_id = %s AND date = CURDATE() AND check_out IS NULL
                           """, (employee_id,))
            rec = cursor.fetchone()
            if not rec:
                return False
            check_out = datetime.now()
            cursor.execute("UPDATE attendance_records SET check_out = %s WHERE record_id = %s",
                           (check_out, rec['record_id']))
            conn.commit()
        conn.close()
        return True
    return False


def get_employee_details(employee_id, period='month'):
    """Get computed details for an ACTIVE employee."""
    conn = get_db_connection()
    if conn:
        with conn.cursor() as cursor:
            # Check if employee is active
            cursor.execute("SELECT leave_credits FROM employees WHERE employee_id = %s AND is_active = TRUE",
                           (employee_id,))
            res = cursor.fetchone()
            if not res:
                return {}
            leave_credits = res['leave_credits'] if res else 15

            # Base query for period
            if period == 'month':
                where_period = "AND date >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH)"
            else:
                where_period = ""

            # Absences
            cursor.execute(f"""
                SELECT COUNT(*) as absences FROM attendance_records
                WHERE employee_id = %s AND status = 'Absent' {where_period}
            """, (employee_id,))
            absences = cursor.fetchone()['absences']

            # Working hours (sum hours)
            cursor.execute(f"""
                SELECT SUM(TIMESTAMPDIFF(MINUTE, check_in, IFNULL(check_out, NOW())) / 60.0) as hours
                FROM attendance_records WHERE employee_id = %s {where_period}
            """, (employee_id,))
            hours = cursor.fetchone()['hours'] or 0

            # Total days, present days
            cursor.execute(f"""
                SELECT COUNT(*) as total_days, SUM(CASE WHEN status IN ('Present', 'Late') THEN 1 ELSE 0 END) as present_days
                FROM attendance_records WHERE employee_id = %s {where_period}
            """, (employee_id,))
            res = cursor.fetchone()
            total_days = res['total_days'] or 0
            present_days = res['present_days'] or 0
            # formulas attendance and average
            attendance_rate = (present_days / total_days * 100) if total_days > 0 else 0
            avg_hours = hours / present_days if present_days > 0 else 0


            # Status
            if attendance_rate > 95:
                status = 'Excellent'
            elif attendance_rate > 85:
                status = 'Good'
            else:
                status = 'Needs Improvement'

        conn.close()
        return {
            'absences': absences,
            'hours': round(hours),
            'leave_credits': leave_credits,
            'attendance_rate': round(attendance_rate),
            'avg_hours': round(avg_hours, 1),
            'status': status
        }
    return {}


def get_employee_details_by_date_range(employee_id, start_date, end_date):
    """Get computed details for an ACTIVE employee within a specific date range."""
    conn = get_db_connection()
    if conn:
        with conn.cursor() as cursor:
            # Check if employee is active
            cursor.execute("SELECT leave_credits FROM employees WHERE employee_id = %s AND is_active = TRUE",
                           (employee_id,))
            res = cursor.fetchone()
            if not res:
                return {}
            leave_credits = res['leave_credits'] if res else 15

            # Date range filter
            where_period = "AND date >= %s AND date < %s"

            # Absences
            cursor.execute(f"""
                SELECT COUNT(*) as absences FROM attendance_records
                WHERE employee_id = %s AND status = 'Absent' {where_period}
            """, (employee_id, start_date, end_date))
            absences = cursor.fetchone()['absences']

            # Working hours (sum hours)
            cursor.execute(f"""
                SELECT SUM(TIMESTAMPDIFF(MINUTE, check_in, IFNULL(check_out, NOW())) / 60.0) as hours
                FROM attendance_records WHERE employee_id = %s {where_period}
            """, (employee_id, start_date, end_date))
            hours = cursor.fetchone()['hours'] or 0

            # Total days, present days
            cursor.execute(f"""
                SELECT COUNT(*) as total_days, SUM(CASE WHEN status IN ('Present', 'Late') THEN 1 ELSE 0 END) as present_days
                FROM attendance_records WHERE employee_id = %s {where_period}
            """, (employee_id, start_date, end_date))
            res = cursor.fetchone()
            total_days = res['total_days'] or 0
            present_days = res['present_days'] or 0
            # formulas attendance and average
            attendance_rate = (present_days / total_days * 100) if total_days > 0 else 0
            avg_hours = hours / present_days if present_days > 0 else 0

            # Status
            if attendance_rate > 95:
                status = 'Excellent'
            elif attendance_rate > 85:
                status = 'Good'
            else:
                status = 'Needs Improvement'

        conn.close()
        return {
            'absences': absences,
            'hours': round(hours),
            'leave_credits': leave_credits,
            'attendance_rate': round(attendance_rate),
            'avg_hours': round(avg_hours, 1),
            'status': status
        }
    return {}


def get_employee_by_id(employee_id):
    """Fetch basic employee info by ID (only active)."""
    conn = get_db_connection()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM employees WHERE employee_id = %s AND is_active = TRUE", (employee_id,))
            emp = cursor.fetchone()
        conn.close()
        return emp
    return None


def get_department_attendance(period='daily'):
    """Get attendance aggregates by department for ACTIVE employees only."""
    conn = get_db_connection()
    if conn:
        with conn.cursor() as cursor:
            if period == 'daily':
                where = "AND a.date = CURDATE()"
            elif period == 'weekly':
                where = "AND a.date >= DATE_SUB(CURDATE(), INTERVAL 1 WEEK)"
            elif period == 'monthly':
                where = "AND a.date >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH)"
            elif period == 'yearly':
                where = "AND a.date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)"
            else:
                where = ""

            cursor.execute(f'''
                SELECT e.department,
                       COUNT(e.employee_id) as total_employees,
                       SUM(CASE WHEN a.status IN ('Present', 'Late') THEN 1 ELSE 0 END) as present,
                       SUM(CASE WHEN a.status = 'Late' THEN 1 ELSE 0 END) as late,
                       SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) as absent
                FROM employees e
                LEFT JOIN attendance_records a ON e.employee_id = a.employee_id {where}
                WHERE e.is_active = TRUE
                GROUP BY e.department
            ''')
            data = cursor.fetchall()
            for d in data:
                d['present'] = d['present'] or 0
                d['late'] = d['late'] or 0
                d['absent'] = d['absent'] or 0
            return data
        conn.close()
    return []


def get_today_attendance():
    """Fetch today's attendance with ACTIVE employee details only."""
    conn = get_db_connection()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                           SELECT e.employee_id, e.full_name, a.check_in, a.check_out, a.status
                           FROM employees e
                                    LEFT JOIN attendance_records a
                                              ON e.employee_id = a.employee_id AND a.date = CURDATE()
                           WHERE e.is_active = TRUE
                           """)
            attendance = cursor.fetchall()
            for row in attendance:
                if row['check_in'] is None:
                    row['status'] = 'Absent'
                    row['check_in'] = '--'
                    row['check_out'] = '--'
                else:
                    row['check_in'] = row['check_in'].strftime('%H:%M') if row['check_in'] else '--'
                    row['check_out'] = row['check_out'].strftime('%H:%M') if row['check_out'] else '--'
        conn.close()
        return attendance
    return []


def get_today_stats(for_date=None):
    """Get attendance stats for ACTIVE employees only."""
    from datetime import date
    if for_date is None:
        for_date = date.today()
    conn = get_db_connection()
    if conn:
        with conn.cursor() as cursor:
            # Get total active employees
            cursor.execute("SELECT COUNT(*) as total FROM employees WHERE is_active = TRUE")
            total_active = cursor.fetchone()['total']

            # Get attendance counts
            cursor.execute("""
                           SELECT COALESCE(SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END), 0) as present,
                                  COALESCE(SUM(CASE WHEN a.status = 'Late' THEN 1 ELSE 0 END), 0)    as late
                           FROM attendance_records a
                                    INNER JOIN employees e ON a.employee_id = e.employee_id
                           WHERE a.date = %s
                             AND e.is_active = TRUE
                           """, (for_date,))
            stats = cursor.fetchone()

            present = stats['present'] if stats else 0
            late = stats['late'] if stats else 0
            # absent formula
            absent = total_active - (present + late)

            result = {'present': present, 'late': late, 'absent': absent}
        conn.close()
        return result
    return {'present': 0, 'late': 0, 'absent': 0}


def get_employee_monthly_hours(employee_id: str, year: int):
    """Return a list of enhanced monthly data for the given employee and year.
    Includes hours, absences, worked_days, expected_days, and overtime.
    """
    conn = get_db_connection()
    if not conn:
        return []
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    MONTH(date) AS month,
                    ROUND(SUM(TIMESTAMPDIFF(MINUTE, check_in, IFNULL(check_out, NOW()))/60.0), 2) AS hours,
                    COUNT(CASE WHEN status = 'Absent' THEN 1 END) AS absences,
                    COUNT(CASE WHEN status IN ('Present', 'Late') THEN 1 END) AS worked_days,
                    COUNT(DISTINCT date) AS expected_days,
                    ROUND(SUM(CASE 
                        WHEN TIMESTAMPDIFF(MINUTE, check_in, IFNULL(check_out, NOW()))/60.0 > 8 
                        THEN TIMESTAMPDIFF(MINUTE, check_in, IFNULL(check_out, NOW()))/60.0 - 8 
                        ELSE 0 
                    END), 2) AS overtime
                FROM attendance_records
                WHERE employee_id = %s AND YEAR(date) = %s
                GROUP BY MONTH(date)
                ORDER BY month
                """,
                (employee_id, year)
            )
            rows = cursor.fetchall() or []
            # Normalize None values to 0
            for r in rows:
                r['hours'] = r['hours'] or 0
                r['absences'] = r['absences'] or 0
                r['worked_days'] = r['worked_days'] or 0
                r['expected_days'] = r['expected_days'] or 0
                r['overtime'] = r['overtime'] or 0
            return rows
    finally:
        conn.close()


def get_employee_yearly_hours(employee_id: str):
    """Return a list of enhanced yearly data across all years for the employee.
    Includes hours, absences, worked_days, expected_days, and overtime.
    """
    conn = get_db_connection()
    if not conn:
        return []
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    YEAR(date) AS year,
                    ROUND(SUM(TIMESTAMPDIFF(MINUTE, check_in, IFNULL(check_out, NOW()))/60.0), 2) AS hours,
                    COUNT(CASE WHEN status = 'Absent' THEN 1 END) AS absences,
                    COUNT(CASE WHEN status IN ('Present', 'Late') THEN 1 END) AS worked_days,
                    COUNT(DISTINCT date) AS expected_days,
                    ROUND(SUM(CASE 
                        WHEN TIMESTAMPDIFF(MINUTE, check_in, IFNULL(check_out, NOW()))/60.0 > 8 
                        THEN TIMESTAMPDIFF(MINUTE, check_in, IFNULL(check_out, NOW()))/60.0 - 8 
                        ELSE 0 
                    END), 2) AS overtime
                FROM attendance_records
                WHERE employee_id = %s
                GROUP BY YEAR(date)
                ORDER BY year
                """,
                (employee_id,)
            )
            rows = cursor.fetchall() or []
            for r in rows:
                r['hours'] = r['hours'] or 0
                r['absences'] = r['absences'] or 0
                r['worked_days'] = r['worked_days'] or 0
                r['expected_days'] = r['expected_days'] or 0
                r['overtime'] = r['overtime'] or 0
            return rows
    finally:
        conn.close()


def search_employees(query: str, limit: int = 50):
    """Search ACTIVE employees by ID or full name, limited for performance."""
    q = (query or '').strip()
    if not q:
        return []
    conn = get_db_connection()
    if not conn:
        return []
    try:
        with conn.cursor() as cursor:
            like = f"%{q}%"
            cursor.execute(
                """
                SELECT employee_id, full_name
                FROM employees
                WHERE is_active = TRUE
                  AND (CAST(employee_id AS CHAR) LIKE %s OR full_name LIKE %s)
                ORDER BY full_name ASC
                LIMIT %s
                """,
                (like, like, int(max(1, min(limit, 500))))
            )
            return cursor.fetchall() or []
    finally:
        conn.close()


def get_all_employees_hours_for_month(year: int, month: int):
    """Return enhanced monthly data for all active employees for a specific month/year.
    Includes hours, absences, worked_days, expected_days, and overtime.
    """
    conn = get_db_connection()
    if not conn:
        return []
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    e.employee_id,
                    e.full_name,
                    ROUND(COALESCE(SUM(TIMESTAMPDIFF(MINUTE, a.check_in, IFNULL(a.check_out, NOW()))/60.0), 0), 2) AS hours,
                    COUNT(CASE WHEN a.status = 'Absent' THEN 1 END) AS absences,
                    COUNT(CASE WHEN a.status IN ('Present', 'Late') THEN 1 END) AS worked_days,
                    COUNT(DISTINCT a.date) AS expected_days,
                    ROUND(COALESCE(SUM(CASE 
                        WHEN TIMESTAMPDIFF(MINUTE, a.check_in, IFNULL(a.check_out, NOW()))/60.0 > 8 
                        THEN TIMESTAMPDIFF(MINUTE, a.check_in, IFNULL(a.check_out, NOW()))/60.0 - 8 
                        ELSE 0 
                    END), 0), 2) AS overtime
                FROM employees e
                LEFT JOIN attendance_records a ON e.employee_id = a.employee_id 
                    AND YEAR(a.date) = %s AND MONTH(a.date) = %s
                WHERE e.is_active = TRUE
                GROUP BY e.employee_id, e.full_name
                ORDER BY e.full_name
                """,
                (year, month)
            )
            rows = cursor.fetchall() or []
            for r in rows:
                r['hours'] = r['hours'] or 0
                r['absences'] = r['absences'] or 0
                r['worked_days'] = r['worked_days'] or 0
                r['expected_days'] = r['expected_days'] or 0
                r['overtime'] = r['overtime'] or 0
            return rows
    finally:
        conn.close()


def get_all_employees_hours_for_year(year: int):
    """Return enhanced yearly data for all active employees for a specific year.
    Includes hours, absences, worked_days, expected_days, and overtime.
    """
    conn = get_db_connection()
    if not conn:
        return []
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    e.employee_id,
                    e.full_name,
                    ROUND(COALESCE(SUM(TIMESTAMPDIFF(MINUTE, a.check_in, IFNULL(a.check_out, NOW()))/60.0), 0), 2) AS hours,
                    COUNT(CASE WHEN a.status = 'Absent' THEN 1 END) AS absences,
                    COUNT(CASE WHEN a.status IN ('Present', 'Late') THEN 1 END) AS worked_days,
                    COUNT(DISTINCT a.date) AS expected_days,
                    ROUND(COALESCE(SUM(CASE 
                        WHEN TIMESTAMPDIFF(MINUTE, a.check_in, IFNULL(a.check_out, NOW()))/60.0 > 8 
                        THEN TIMESTAMPDIFF(MINUTE, a.check_in, IFNULL(a.check_out, NOW()))/60.0 - 8 
                        ELSE 0 
                    END), 0), 2) AS overtime
                FROM employees e
                LEFT JOIN attendance_records a ON e.employee_id = a.employee_id 
                    AND YEAR(a.date) = %s
                WHERE e.is_active = TRUE
                GROUP BY e.employee_id, e.full_name
                ORDER BY e.full_name
                """,
                (year,)
            )
            rows = cursor.fetchall() or []
            for r in rows:
                r['hours'] = r['hours'] or 0
                r['absences'] = r['absences'] or 0
                r['worked_days'] = r['worked_days'] or 0
                r['expected_days'] = r['expected_days'] or 0
                r['overtime'] = r['overtime'] or 0
            return rows
    finally:
        conn.close()


# ============================================
# AUTHENTICATION FUNCTIONS (with soft delete)
# ============================================

def authenticate_user(username, password, role):
    """Authenticate ACTIVE staff/admin user only."""
    conn = get_db_connection()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                           SELECT *
                           FROM staff_users
                           WHERE username = %s
                             AND role = %s
                             AND is_active = TRUE
                           """, (username, role))
            user = cursor.fetchone()
        conn.close()
        if user and user['password_hash'] == hash_password(password):
            return True
    return False


def add_or_update_staff(username, full_name, role, position, password=None, is_active=True, mode='add'):
    """Add or update staff user."""
    conn = get_db_connection()
    if conn:
        with conn.cursor() as cursor:
            # Convert is_active to proper boolean/int for database
            is_active_val = 1 if is_active else 0

            if mode == 'add':
                password_hash = hash_password(password)
                cursor.execute("""
                               INSERT INTO staff_users (username, full_name, role, position, password_hash, is_active)
                               VALUES (%s, %s, %s, %s, %s, %s)
                               """, (username, full_name, role, position, password_hash, is_active_val))
            else:
                if password:
                    password_hash = hash_password(password)
                    cursor.execute("""
                                   UPDATE staff_users
                                   SET full_name     = %s,
                                       role          = %s,
                                       position      = %s,
                                       password_hash = %s,
                                       is_active     = %s
                                   WHERE username = %s
                                   """, (full_name, role, position, password_hash, is_active_val, username))
                else:
                    cursor.execute("""
                                   UPDATE staff_users
                                   SET full_name = %s,
                                       role      = %s,
                                       position  = %s,
                                       is_active = %s
                                   WHERE username = %s
                                   """, (full_name, role, position, is_active_val, username))
            conn.commit()
        conn.close()


def get_all_staff():
    """Fetch all ACTIVE staff users."""
    conn = get_db_connection()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                           SELECT username, full_name, role, position
                           FROM staff_users
                           WHERE role = 'Staff'
                             AND is_active = TRUE
                           """)
            staff = cursor.fetchall()
        conn.close()
        return staff
    return []


def delete_staff(username):
    """Soft delete a staff user (mark as inactive instead of deleting)."""
    conn = get_db_connection()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE staff_users SET is_active = FALSE WHERE username = %s", (username,))
            conn.commit()
        conn.close()


def get_employee_monthly_attendance_details(employee_id, start_date, end_date):
    """Get detailed monthly attendance records for an employee within a specific date range."""
    conn = get_db_connection()
    if conn:
        with conn.cursor() as cursor:
            # Check if employee is active
            cursor.execute("SELECT full_name FROM employees WHERE employee_id = %s AND is_active = TRUE",
                           (employee_id,))
            res = cursor.fetchone()
            if not res:
                return []

            # Get detailed attendance records for the date range
            cursor.execute("""
                SELECT 
                    date,
                    check_in,
                    check_out,
                    status,
                    CASE 
                        WHEN check_in IS NOT NULL AND check_out IS NOT NULL THEN
                            ROUND(TIMESTAMPDIFF(MINUTE, check_in, check_out) / 60.0, 2)
                        WHEN check_in IS NOT NULL AND check_out IS NULL THEN
                            ROUND(TIMESTAMPDIFF(MINUTE, check_in, NOW()) / 60.0, 2)
                        ELSE 0
                    END as daily_hours
                FROM attendance_records 
                WHERE employee_id = %s AND date >= %s AND date < %s
                ORDER BY date ASC
            """, (employee_id, start_date, end_date))

            records = cursor.fetchall() or []

            # Format the records for display
            formatted_records = []
            for record in records:
                formatted_records.append({
                    'date': record['date'].strftime('%Y-%m-%d') if record['date'] else '',
                    'check_in': record['check_in'].strftime('%H:%M') if record['check_in'] else '--',
                    'check_out': record['check_out'].strftime('%H:%M') if record['check_out'] else '--',
                    'status': record['status'] or 'Absent',
                    'daily_hours': record['daily_hours'] or 0
                })

        conn.close()
        return formatted_records
    return []


def add_employee(employee_id, full_name, position, department, image_path=None, leave_credits=15, is_active=True):
    """Insert a new employee. Returns True on success, False otherwise."""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO employees (employee_id, full_name, position, department, image_path, leave_credits, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (employee_id, full_name, position, department, image_path, leave_credits, is_active)
                )
                conn.commit()
            return True
        except Exception:
            conn.rollback()
            return False
        finally:
            conn.close()
    return False
