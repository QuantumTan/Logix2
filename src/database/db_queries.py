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


def get_next_employee_id(min_start: int = 10000) -> int:
    """Return the next available employee_id using MAX(employee_id)+1 across ALL rows.
    Ensures the starting range at min_start (default 10000).
    Fallbacks to min_start on any error.
    """
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                # Use parameter for min_start to avoid SQL injection and to compute default base
                cursor.execute(
                    "SELECT COALESCE(MAX(employee_id), %s - 1) + 1 AS next_id FROM employees",
                    (min_start,)
                )
                row = cursor.fetchone()
                # row may be dict due to DictCursor
                next_val = None
                if row is not None:
                    next_val = row.get('next_id') if isinstance(row, dict) else (row[0] if len(row) > 0 else None)
                if next_val is None:
                    return min_start
                try:
                    next_int = int(next_val)
                except Exception:
                    return min_start
                return next_int if next_int >= min_start else min_start
        except Exception:
            return min_start
        finally:
            conn.close()
    return min_start


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
            # Check if employee is active and get creation date
            cursor.execute("""
                SELECT leave_credits, created_at 
                FROM employees 
                WHERE employee_id = %s AND is_active = TRUE
            """, (employee_id,))
            res = cursor.fetchone()
            if not res:
                return {}
            leave_credits = res['leave_credits'] if res else 15

            # Use created_at for more accurate absence calculation
            employee_start_date = res.get('created_at')
            if not employee_start_date:
                # Fallback to first attendance record if created_at is null
                cursor.execute("""
                    SELECT MIN(date) as first_attendance 
                    FROM attendance_records 
                    WHERE employee_id = %s
                """, (employee_id,))
                first_record = cursor.fetchone()
                employee_start_date = first_record['first_attendance'] if first_record and first_record['first_attendance'] else datetime.now().date()

            # Base query for period
            if period == 'month':
                # Calculate from max(employee_start_date, 1_month_ago) to today
                cursor.execute("""
                    SELECT GREATEST(
                        DATE_SUB(CURDATE(), INTERVAL 1 MONTH), 
                        DATE(%s)
                    ) as effective_start_date
                """, (employee_start_date,))
                effective_start = cursor.fetchone()['effective_start_date']
                where_period = "AND date >= %s"
                date_params = (employee_id, effective_start)
            else:
                where_period = ""
                date_params = (employee_id,)

            # Calculate working days only from effective start date
            if period == 'month':
                cursor.execute("""
                    SELECT COUNT(*) as working_days
                    FROM (
                        SELECT DATE_ADD(%s, INTERVAL seq.seq DAY) as work_date
                        FROM (
                            SELECT 0 as seq UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9 UNION
                            SELECT 10 UNION SELECT 11 UNION SELECT 12 UNION SELECT 13 UNION SELECT 14 UNION SELECT 15 UNION SELECT 16 UNION SELECT 17 UNION SELECT 18 UNION SELECT 19 UNION
                            SELECT 20 UNION SELECT 21 UNION SELECT 22 UNION SELECT 23 UNION SELECT 24 UNION SELECT 25 UNION SELECT 26 UNION SELECT 27 UNION SELECT 28 UNION SELECT 29 UNION SELECT 30
                        ) seq
                        WHERE DATE_ADD(%s, INTERVAL seq.seq DAY) <= CURDATE()
                        AND WEEKDAY(DATE_ADD(%s, INTERVAL seq.seq DAY)) < 5
                    ) working_dates
                """, (effective_start, effective_start, effective_start))
                working_days = cursor.fetchone()['working_days'] or 0
            else:
                working_days = 30

            # Get days with attendance records
            cursor.execute(f"""
                SELECT COUNT(DISTINCT date) as attended_days
                FROM attendance_records 
                WHERE employee_id = %s {where_period}
            """, date_params)
            attended_days = cursor.fetchone()['attended_days'] or 0

            # Calculate absences as working days minus attended days
            absences = max(0, working_days - attended_days) if period == 'month' else 0

            # For non-month periods, use the old logic
            if period != 'month':
                cursor.execute(f"""
                    SELECT COUNT(*) as absences FROM attendance_records
                    WHERE employee_id = %s AND status = 'Absent' {where_period}
                """, date_params)
                absences = cursor.fetchone()['absences']

            # Working hours (sum hours)
            cursor.execute(f"""
                SELECT SUM(TIMESTAMPDIFF(MINUTE, check_in, IFNULL(check_out, NOW())) / 60.0) as hours
                FROM attendance_records WHERE employee_id = %s {where_period}
            """, date_params)
            hours = cursor.fetchone()['hours'] or 0

            # Total days, present days
            cursor.execute(f"""
                SELECT COUNT(*) as total_days, SUM(CASE WHEN status IN ('Present', 'Late') THEN 1 ELSE 0 END) as present_days
                FROM attendance_records WHERE employee_id = %s {where_period}
            """, date_params)
            res = cursor.fetchone()
            total_days = res['total_days'] or 0
            present_days = res['present_days'] or 0

            # For month period, use working days as the base for attendance rate calculation
            if period == 'month':
                attendance_rate = (present_days / working_days * 100) if working_days > 0 else 100
            else:
                attendance_rate = (present_days / total_days * 100) if total_days > 0 else 100

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
    """Get computed details for an ACTIVE employee within a specific date range.
    Absences are computed as working weekdays without a Present/Late record
    between effective_start (max of hire date and start_date) and effective_end
    (min of end_date and tomorrow), excluding weekends and future days.
    """
    conn = get_db_connection()
    if conn:
        with conn.cursor() as cursor:
            # Load employee and ensure active
            cursor.execute("SELECT leave_credits, created_at FROM employees WHERE employee_id = %s AND is_active = TRUE", (employee_id,))
            emp = cursor.fetchone()
            if not emp:
                return {}
            leave_credits = emp.get('leave_credits', 15)
            created_at = emp.get('created_at')

            from datetime import date as _date, timedelta as _td
            today = _date.today()
            # Cap end to tomorrow (exclusive) to avoid future days
            cap_end_exclusive = min(end_date, today + _td(days=1))
            hire_date = created_at.date() if created_at else None
            effective_start = max(start_date, hire_date) if hire_date else start_date

            if effective_start >= cap_end_exclusive:
                return {
                    'absences': 0,
                    'hours': 0,
                    'leave_credits': leave_credits,
                    'attendance_rate': 0,
                    'avg_hours': 0.0,
                    'status': 'Needs Improvement'
                }

            # Present days within range
            cursor.execute(
                """
                SELECT COUNT(DISTINCT date) AS present_days
                FROM attendance_records
                WHERE employee_id = %s AND date >= %s AND date < %s
                  AND status IN ('Present','Late')
                  AND WEEKDAY(date) < 5
                """,
                (employee_id, effective_start, cap_end_exclusive)
            )
            present_days = (cursor.fetchone() or {}).get('present_days', 0) or 0

            # Hours within range
            cursor.execute(
                """
                SELECT SUM(TIMESTAMPDIFF(MINUTE, check_in, IFNULL(check_out, NOW())) / 60.0) AS hours
                FROM attendance_records
                WHERE employee_id = %s AND date >= %s AND date < %s
                """,
                (employee_id, effective_start, cap_end_exclusive)
            )
            hours = (cursor.fetchone() or {}).get('hours', 0) or 0

            # Working weekdays in range
            d = effective_start
            working_days = 0
            while d < cap_end_exclusive:
                if d.weekday() < 5:
                    working_days += 1
                d += _td(days=1)

            absences = max(0, working_days - present_days)
            attendance_rate = (present_days / working_days * 100) if working_days > 0 else 0
            avg_hours = (hours / present_days) if present_days > 0 else 0

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
            # Get data for each month
            cursor.execute(
                """
                SELECT 
                    MONTH(date) AS month,
                    ROUND(SUM(TIMESTAMPDIFF(MINUTE, check_in, IFNULL(check_out, NOW()))/60.0), 2) AS hours,
                    COUNT(CASE WHEN status IN ('Present', 'Late') THEN 1 END) AS worked_days,
                    COUNT(DISTINCT date) AS attended_days,
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

            # Calculate working days and absences for each month (Mon-Fri), capped to today
            for r in rows:
                month = int(r['month'])

                # Count working days for the month using a generated date series
                cursor.execute(
                    """
                    SELECT COUNT(*) AS working_days
                    FROM (
                        SELECT 0 AS seq UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9 UNION
                        SELECT 10 UNION SELECT 11 UNION SELECT 12 UNION SELECT 13 UNION SELECT 14 UNION SELECT 15 UNION SELECT 16 UNION SELECT 17 UNION SELECT 18 UNION SELECT 19 UNION
                        SELECT 20 UNION SELECT 21 UNION SELECT 22 UNION SELECT 23 UNION SELECT 24 UNION SELECT 25 UNION SELECT 26 UNION SELECT 27 UNION SELECT 28 UNION SELECT 29 UNION SELECT 30
                    ) s
                    WHERE 
                        WEEKDAY(
                            DATE_ADD(
                                DATE_ADD(MAKEDATE(%s, 1), INTERVAL %s-1 MONTH), 
                                INTERVAL s.seq DAY
                            )
                        ) < 5
                        AND DATE_ADD(
                                DATE_ADD(MAKEDATE(%s, 1), INTERVAL %s-1 MONTH),
                                INTERVAL s.seq DAY
                            ) <= LEAST(
                                LAST_DAY(DATE_ADD(MAKEDATE(%s, 1), INTERVAL %s-1 MONTH)),
                                CURDATE()
                            )
                        AND DATE_ADD(
                                DATE_ADD(MAKEDATE(%s, 1), INTERVAL %s-1 MONTH),
                                INTERVAL s.seq DAY
                            ) >= DATE_ADD(MAKEDATE(%s, 1), INTERVAL %s-1 MONTH)
                    """,
                    (year, month, year, month, year, month, year, month, year, month)
                )
                wd_res = cursor.fetchone()
                working_days = (wd_res or {}).get('working_days', 0) or 0

                # Absences as expected (Mon-Fri working days) minus attended days
                attended_days = r['attended_days'] or 0
                absences = max(0, int(working_days) - int(attended_days))

                # Update row
                r['hours'] = r['hours'] or 0
                r['absences'] = absences
                r['worked_days'] = r['worked_days'] or 0
                r['expected_days'] = working_days
                r['overtime'] = r['overtime'] or 0

            return rows
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
                    e.created_at,
                    ROUND(COALESCE(SUM(TIMESTAMPDIFF(MINUTE, a.check_in, IFNULL(a.check_out, NOW()))/60.0), 0), 2) AS hours,
                    COUNT(CASE WHEN a.status IN ('Present', 'Late') THEN 1 END) AS worked_days,
                    COUNT(DISTINCT a.date) AS attended_days,
                    ROUND(COALESCE(SUM(CASE 
                        WHEN TIMESTAMPDIFF(MINUTE, a.check_in, IFNULL(a.check_out, NOW()))/60.0 > 8 
                        THEN TIMESTAMPDIFF(MINUTE, a.check_in, IFNULL(a.check_out, NOW()))/60.0 - 8 
                        ELSE 0 
                    END), 0), 2) AS overtime
                FROM employees e
                LEFT JOIN attendance_records a ON e.employee_id = a.employee_id 
                    AND YEAR(a.date) = %s AND MONTH(a.date) = %s
                WHERE e.is_active = TRUE
                GROUP BY e.employee_id, e.full_name, e.created_at
                ORDER BY e.full_name
                """,
                (year, month)
            )
            rows = cursor.fetchall() or []

            for r in rows:
                attended_days = int(r.get('attended_days', 0) or 0)
                created_at = r.get('created_at')

                # Compute working days for the month (Mon-Fri), starting from hire date if within month, and capped to today
                cursor.execute(
                    """
                    SELECT COUNT(*) AS working_days
                    FROM (
                        SELECT 0 AS seq UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9 UNION
                        SELECT 10 UNION SELECT 11 UNION SELECT 12 UNION SELECT 13 UNION SELECT 14 UNION SELECT 15 UNION SELECT 16 UNION SELECT 17 UNION SELECT 18 UNION SELECT 19 UNION
                        SELECT 20 UNION SELECT 21 UNION SELECT 22 UNION SELECT 23 UNION SELECT 24 UNION SELECT 25 UNION SELECT 26 UNION SELECT 27 UNION SELECT 28 UNION SELECT 29 UNION SELECT 30
                    ) s
                    WHERE 
                        WEEKDAY(
                            DATE_ADD(
                                DATE_ADD(MAKEDATE(%s, 1), INTERVAL %s-1 MONTH), 
                                INTERVAL s.seq DAY
                            )
                        ) < 5
                        AND DATE_ADD(
                                DATE_ADD(MAKEDATE(%s, 1), INTERVAL %s-1 MONTH),
                                INTERVAL s.seq DAY
                            ) <= LEAST(
                                LAST_DAY(DATE_ADD(MAKEDATE(%s, 1), INTERVAL %s-1 MONTH)),
                                CURDATE()
                            )
                        AND DATE_ADD(
                                DATE_ADD(MAKEDATE(%s, 1), INTERVAL %s-1 MONTH),
                                INTERVAL s.seq DAY
                            ) >= GREATEST(
                                DATE(%s),
                                DATE_ADD(MAKEDATE(%s, 1), INTERVAL %s-1 MONTH)
                            )
                    """,
                    (year, month, year, month, year, month, year, month, created_at, year, month)
                )
                wd_res = cursor.fetchone()
                working_days = (wd_res or {}).get('working_days', 0) or 0

                absences = max(0, int(working_days) - attended_days)

                r['hours'] = r['hours'] or 0
                r['absences'] = absences
                r['worked_days'] = r['worked_days'] or 0
                r['expected_days'] = working_days
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
            # Aggregate per employee for the given year
            cursor.execute(
                """
                SELECT 
                    e.employee_id,
                    e.full_name,
                    e.created_at,
                    ROUND(COALESCE(SUM(TIMESTAMPDIFF(MINUTE, a.check_in, IFNULL(a.check_out, NOW()))/60.0), 0), 2) AS hours,
                    COUNT(CASE WHEN a.status IN ('Present', 'Late') THEN 1 END) AS worked_days,
                    COUNT(DISTINCT a.date) AS attended_days,
                    ROUND(COALESCE(SUM(CASE 
                        WHEN TIMESTAMPDIFF(MINUTE, a.check_in, IFNULL(a.check_out, NOW()))/60.0 > 8 
                        THEN TIMESTAMPDIFF(MINUTE, a.check_in, IFNULL(a.check_out, NOW()))/60.0 - 8 
                        ELSE 0 
                    END), 0), 2) AS overtime
                FROM employees e
                LEFT JOIN attendance_records a ON e.employee_id = a.employee_id 
                    AND YEAR(a.date) = %s
                WHERE e.is_active = TRUE
                GROUP BY e.employee_id, e.full_name, e.created_at
                ORDER BY e.full_name
                """,
                (year,)
            )
            rows = cursor.fetchall() or []

            # Post-process expected working days and absences per employee in Python
            import datetime as _dt
            today = _dt.date.today()
            year_start = _dt.date(year, 1, 1)
            year_end = _dt.date(year, 12, 31)
            cap_end = min(year_end, today)

            def _count_weekdays(start: _dt.date, end: _dt.date) -> int:
                if start > end:
                    return 0
                d = start
                one = _dt.timedelta(days=1)
                cnt = 0
                while d <= end:
                    if d.weekday() < 5:
                        cnt += 1
                    d += one
                return cnt

            for r in rows:
                created_at = r.get('created_at')
                hire_date = created_at.date() if created_at else year_start
                effective_start = max(year_start, hire_date)
                expected_days = _count_weekdays(effective_start, cap_end)
                attended_days = int(r.get('attended_days', 0) or 0)
                absences = max(0, int(expected_days) - attended_days)

                r['hours'] = r.get('hours', 0) or 0
                r['worked_days'] = r.get('worked_days', 0) or 0
                r['expected_days'] = expected_days
                r['absences'] = absences
                r['overtime'] = r.get('overtime', 0) or 0
                r['year'] = year

            return rows
    finally:
        conn.close()


def get_employee_yearly_hours(employee_id: str):
    """Return a list of enhanced yearly data for the given employee across years.
    Each row includes year, hours, absences, worked_days, expected_days, and overtime.
    """
    conn = get_db_connection()
    if not conn:
        return []
    try:
        with conn.cursor() as cursor:
            # Fetch employee hire date
            cursor.execute(
                """
                SELECT created_at FROM employees 
                WHERE employee_id = %s AND is_active = TRUE
                """,
                (employee_id,)
            )
            emp = cursor.fetchone() or {}
            created_at = emp.get('created_at')

            # Aggregate by year for the employee
            cursor.execute(
                """
                SELECT 
                    YEAR(date) AS year,
                    ROUND(SUM(TIMESTAMPDIFF(MINUTE, check_in, IFNULL(check_out, NOW()))/60.0), 2) AS hours,
                    COUNT(CASE WHEN status IN ('Present', 'Late') THEN 1 END) AS worked_days,
                    COUNT(DISTINCT date) AS attended_days,
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

            # Compute expected days and absences per year
            import datetime as _dt
            today = _dt.date.today()

            def _count_weekdays(start: _dt.date, end: _dt.date) -> int:
                if start > end:
                    return 0
                d = start
                one = _dt.timedelta(days=1)
                cnt = 0
                while d <= end:
                    if d.weekday() < 5:
                        cnt += 1
                    d += one
                return cnt

            for r in rows:
                year = int(r.get('year'))
                year_start = _dt.date(year, 1, 1)
                year_end = _dt.date(year, 12, 31)
                cap_end = min(year_end, today)
                hire_date = created_at.date() if created_at else year_start
                effective_start = max(year_start, hire_date)
                expected_days = _count_weekdays(effective_start, cap_end)
                attended_days = int(r.get('attended_days', 0) or 0)
                absences = max(0, int(expected_days) - attended_days)

                r['hours'] = r.get('hours', 0) or 0
                r['worked_days'] = r.get('worked_days', 0) or 0
                r['expected_days'] = expected_days
                r['absences'] = absences
                r['overtime'] = r.get('overtime', 0) or 0

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
    """Get detailed monthly attendance records for an employee within a specific date range.
    Ensures a row per working weekday in the range. Missing records are emitted as Absent.
    Date range is [start_date, end_date), capped by employee hire date and today.
    """
    conn = get_db_connection()
    if conn:
        with conn.cursor() as cursor:
            # Verify employee active and get hire date
            cursor.execute(
                "SELECT full_name, created_at FROM employees WHERE employee_id = %s AND is_active = TRUE",
                (employee_id,)
            )
            res = cursor.fetchone()
            if not res:
                conn.close()
                return []
            created_at = res.get('created_at')

            from datetime import date as _date, timedelta as _td, datetime as _dt
            today = _date.today()
            cap_end_exclusive = min(end_date, today + _td(days=1))
            hire_date = created_at.date() if created_at else None
            effective_start = max(start_date, hire_date) if hire_date else start_date

            if effective_start >= cap_end_exclusive:
                conn.close()
                return []

            # Fetch all records in the effective range
            cursor.execute(
                """
                SELECT date, check_in, check_out, status
                FROM attendance_records
                WHERE employee_id = %s AND date >= %s AND date < %s
                """,
                (employee_id, effective_start, cap_end_exclusive)
            )
            rows = cursor.fetchall() or []
            by_date = {r['date']: r for r in rows}

            # Build a complete list of working days
            formatted_records = []
            cur = effective_start
            while cur < cap_end_exclusive:
                if cur.weekday() < 5:  # Mon-Fri
                    rec = by_date.get(cur)
                    if rec:
                        ci = rec.get('check_in')
                        co = rec.get('check_out')
                        status = rec.get('status') or 'Absent'
                        # Compute daily hours similar to prior logic
                        if ci and co:
                            diff_hours = round((co - ci).total_seconds() / 3600.0, 2)
                        elif ci and not co:
                            diff_hours = round((_dt.now() - ci).total_seconds() / 3600.0, 2)
                        else:
                            diff_hours = 0
                        formatted_records.append({
                            'date': cur.strftime('%Y-%m-%d'),
                            'check_in': ci.strftime('%H:%M') if ci else '--',
                            'check_out': co.strftime('%H:%M') if co else '--',
                            'status': status,
                            'daily_hours': diff_hours
                        })
                    else:
                        # No record for a working day: Absent
                        formatted_records.append({
                            'date': cur.strftime('%Y-%m-%d'),
                            'check_in': '--',
                            'check_out': '--',
                            'status': 'Absent',
                            'daily_hours': 0
                        })
                cur += _td(days=1)

        conn.close()
        # Ensure chronological order
        formatted_records.sort(key=lambda x: x['date'])
        return formatted_records
    return []


def add_employee(full_name, position, department, image_path=None, leave_credits=15, is_active=True):
    """Insert a new employee letting the DB assign AUTO_INCREMENT ID.
    Returns the new employee_id (int) on success, or None on failure.

    Note: image_path is not stored during insert because we need the new id to name the asset file.
    Call set_employee_image_path(new_id, path) after copying the file.
    """
    conn = get_db_connection()
    if not conn:
        return None
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO employees (full_name, position, department, leave_credits, is_active, created_at)
                VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                """,
                (full_name, position, department, leave_credits, is_active)
            )
            conn.commit()
            new_id = cursor.lastrowid
            try:
                return int(new_id) if new_id is not None else None
            except Exception:
                return None
    except Exception as e:
        print(f"[add_employee] Error adding employee: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()


def set_employee_image_path(employee_id: int, image_path: str) -> bool:
    """Update only the image_path for an employee."""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE employees SET image_path = %s WHERE employee_id = %s",
                (image_path, employee_id)
            )
            conn.commit()
            return True
    except Exception as e:
        print(f"[set_employee_image_path] Error updating image_path for {employee_id}: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
