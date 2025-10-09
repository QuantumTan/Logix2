# src/database/attendance.py
from __future__ import annotations
from typing import Optional
from datetime import datetime, date, timedelta

from .db_config import get_db_connection


# --- Helper function for counting weekdays ---

def _count_weekdays(start: date, end: date) -> int:
    """Count weekdays (Mon-Fri) between start and end dates (inclusive)."""
    if start > end:
        return 0
    d = start
    cnt = 0
    one = timedelta(days=1)
    # Include both start and end dates
    while d <= end:
        if d.weekday() < 5:  # Monday=0, Friday=4
            cnt += 1
        d += one
    return cnt


# --- Attendance operations ---

def employee_check_in(employee_id: int) -> bool:
    """Handle employee check-in, compute status, and insert record if not already checked in."""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM employees WHERE employee_id = %s AND is_active = TRUE",
                (employee_id,)
            )
            if not cursor.fetchone():
                return False
            cursor.execute(
                "SELECT 1 FROM attendance_records WHERE employee_id = %s AND date = CURDATE()",
                (employee_id,)
            )
            if cursor.fetchone():
                return False
            check_in = datetime.now()
            start_time = check_in.replace(hour=8, minute=0, second=0, microsecond=0)
            late_threshold = start_time.replace(minute=15)
            status = 'Late' if check_in > late_threshold else 'Present'
            cursor.execute(
                """
                INSERT INTO attendance_records (employee_id, check_in, status, date)
                VALUES (%s, %s, %s, CURDATE())
                """,
                (employee_id, check_in, status)
            )
            conn.commit()
            return True
    finally:
        conn.close()


def employee_check_out(employee_id: int) -> bool:
    """Handle employee check-out if checked in and not yet checked out."""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT record_id FROM attendance_records
                WHERE employee_id = %s AND date = CURDATE() AND check_out IS NULL
                """,
                (employee_id,)
            )
            rec = cursor.fetchone()
            if not rec:
                return False
            check_out = datetime.now()
            cursor.execute(
                "UPDATE attendance_records SET check_out = %s WHERE record_id = %s",
                (check_out, rec['record_id'])
            )
            conn.commit()
            return True
    finally:
        conn.close()


# --- Aggregates and queries used by dashboards ---

def get_employee_details(employee_id: int, period: str = 'month') -> dict:
    """Get computed details for an ACTIVE employee."""
    conn = get_db_connection()
    if not conn:
        return {}
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT leave_credits, created_at
                FROM employees
                WHERE employee_id = %s AND is_active = TRUE
                """,
                (employee_id,)
            )
            res = cursor.fetchone()
            if not res:
                return {}
            leave_credits = res['leave_credits'] if res else 15
            employee_start_date = res.get('created_at')

            # Convert to date if it's a datetime
            if employee_start_date and hasattr(employee_start_date, 'date'):
                employee_start_date = employee_start_date.date()

            if not employee_start_date:
                cursor.execute(
                    """
                    SELECT MIN(date) as first_attendance
                    FROM attendance_records
                    WHERE employee_id = %s
                    """,
                    (employee_id,)
                )
                first_record = cursor.fetchone()
                employee_start_date = first_record['first_attendance'] if first_record and first_record['first_attendance'] else date.today()

            if period == 'month':
                # Calculate effective start date (1 month ago or employee start date, whichever is later)
                today = date.today()
                one_month_ago = today - timedelta(days=30)
                effective_start = max(one_month_ago, employee_start_date)

                # Use Python to count working days instead of complex SQL
                working_days = _count_weekdays(effective_start, today)

                where_period = "AND date >= %s"
                date_params = (employee_id, effective_start)
            else:
                where_period = ""
                date_params = (employee_id,)
                working_days = 30

            cursor.execute(
                f"""
                SELECT COUNT(DISTINCT date) as attended_days
                FROM attendance_records WHERE employee_id = %s {where_period}
                """,
                date_params
            )
            attended_days = cursor.fetchone()['attended_days'] or 0

            absences = max(0, working_days - attended_days) if period == 'month' else 0

            if period != 'month':
                cursor.execute(
                    f"""
                    SELECT COUNT(*) as absences FROM attendance_records
                    WHERE employee_id = %s AND status = 'Absent' {where_period}
                    """,
                    date_params
                )
                absences = cursor.fetchone()['absences']

            cursor.execute(
                f"""
                SELECT SUM(TIMESTAMPDIFF(MINUTE, check_in, IFNULL(check_out, NOW())) / 60.0) as hours
                FROM attendance_records WHERE employee_id = %s {where_period}
                """,
                date_params
            )
            hours = cursor.fetchone()['hours'] or 0

            cursor.execute(
                f"""
                SELECT COUNT(*) as total_days, SUM(CASE WHEN status IN ('Present', 'Late') THEN 1 ELSE 0 END) as present_days
                FROM attendance_records WHERE employee_id = %s {where_period}
                """,
                date_params
            )
            res = cursor.fetchone()
            total_days = res['total_days'] or 0
            present_days = res['present_days'] or 0

            if period == 'month':
                attendance_rate = (present_days / working_days * 100) if working_days > 0 else 0
            else:
                attendance_rate = (present_days / total_days * 100) if total_days > 0 else 0

            avg_hours = hours / present_days if present_days > 0 else 0

            if attendance_rate > 95:
                status = 'Excellent'
            elif attendance_rate > 85:
                status = 'Good'
            else:
                status = 'Needs Improvement'

            return {
                'absences': absences,
                'hours': round(hours),
                'leave_credits': leave_credits,
                'attendance_rate': round(attendance_rate),
                'avg_hours': round(avg_hours, 1),
                'status': status
            }
    finally:
        conn.close()


def get_department_attendance(period: str = 'daily') -> list[dict]:
    conn = get_db_connection()
    if not conn:
        return []
    try:
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
            cursor.execute(
                f"""
                SELECT e.department,
                       COUNT(e.employee_id) as total_employees,
                       SUM(CASE WHEN a.status IN ('Present', 'Late') THEN 1 ELSE 0 END) as present,
                       SUM(CASE WHEN a.status = 'Late' THEN 1 ELSE 0 END) as late,
                       SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) as absent
                FROM employees e
                LEFT JOIN attendance_records a ON e.employee_id = a.employee_id {where}
                WHERE e.is_active = TRUE
                GROUP BY e.department
                """
            )
            data = cursor.fetchall() or []
            for d in data:
                d['present'] = d.get('present') or 0
                d['late'] = d.get('late') or 0
                d['absent'] = d.get('absent') or 0
            return data
    finally:
        conn.close()


def get_today_attendance() -> list[dict]:
    conn = get_db_connection()
    if not conn:
        return []
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT e.employee_id, e.full_name, a.check_in, a.check_out, a.status
                FROM employees e
                LEFT JOIN attendance_records a
                  ON e.employee_id = a.employee_id AND a.date = CURDATE()
                WHERE e.is_active = TRUE
                """
            )
            attendance = cursor.fetchall() or []
            for row in attendance:
                if row['check_in'] is None:
                    row['status'] = 'Absent'
                    row['check_in'] = '--'
                    row['check_out'] = '--'
                else:
                    row['check_in'] = row['check_in'].strftime('%H:%M') if row['check_in'] else '--'
                    row['check_out'] = row['check_out'].strftime('%H:%M') if row['check_out'] else '--'
            return attendance
    finally:
        conn.close()


def get_today_stats(for_date: Optional[date] = None) -> dict:
    if for_date is None:
        for_date = date.today()
    conn = get_db_connection()
    if not conn:
        return {'present': 0, 'late': 0, 'absent': 0}
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as total FROM employees WHERE is_active = TRUE")
            total_active = (cursor.fetchone() or {}).get('total', 0)
            cursor.execute(
                """
                SELECT COALESCE(SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END), 0) as present,
                       COALESCE(SUM(CASE WHEN a.status = 'Late' THEN 1 ELSE 0 END), 0)    as late
                FROM attendance_records a
                INNER JOIN employees e ON a.employee_id = e.employee_id
                WHERE a.date = %s AND e.is_active = TRUE
                """,
                (for_date,)
            )
            stats = cursor.fetchone() or {}
            present = stats.get('present', 0) or 0
            late = stats.get('late', 0) or 0
            absent = int(total_active) - (int(present) + int(late))
            return {'present': present, 'late': late, 'absent': absent}
    finally:
        conn.close()


# --- Hours/absences aggregates ---

def get_employee_monthly_hours(employee_id: str, year: int) -> list[dict]:
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
                    COUNT(DISTINCT CASE WHEN status IN ('Present', 'Late') THEN date END) AS worked_days,
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
            for r in rows:
                month = int(r['month'])
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
                attended_days = r['attended_days'] or 0
                absences = max(0, int(working_days) - int(attended_days))
                r['hours'] = r['hours'] or 0
                r['absences'] = absences
                r['worked_days'] = r['worked_days'] or 0
                r['expected_days'] = working_days
                r['overtime'] = r['overtime'] or 0
            return rows
    finally:
        conn.close()


def get_all_employees_hours_for_month(year: int, month: int) -> list[dict]:
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
                    COUNT(DISTINCT CASE WHEN a.status IN ('Present', 'Late') THEN a.date END) AS worked_days,
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


def get_all_employees_hours_for_year(year: int) -> list[dict]:
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
                    COUNT(DISTINCT CASE WHEN a.status IN ('Present', 'Late') THEN a.date END) AS worked_days,
                    COUNT(DISTINCT a.date) AS attended_days,
                    ROUND(COALESCE(SUM(CASE 
                        WHEN TIMESTAMPDIFF(MINUTE, a.check_in, IFNULL(a.check_out, NOW()))/60.0 > 8 
                        THEN TIMESTAMPDIFF(MINUTE, a.check_in, IFNULL(a.check_out, NOW()))/60.0 - 8 
                        ELSE 0 
                    END), 0), 2) AS overtime
                FROM employees e
                LEFT JOIN attendance_records a ON e.employee_id = a.employee_id AND YEAR(a.date) = %s
                WHERE e.is_active = TRUE
                GROUP BY e.employee_id, e.full_name, e.created_at
                ORDER BY e.full_name
                """,
                (year,)
            )
            rows = cursor.fetchall() or []
            import datetime as _dt
            today = _dt.date.today()
            year_start = _dt.date(year, 1, 1)
            year_end = _dt.date(year, 12, 31)
            cap_end = min(year_end, today)

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


def get_employee_yearly_hours(employee_id: str) -> list[dict]:
    conn = get_db_connection()
    if not conn:
        return []
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT created_at FROM employees WHERE employee_id = %s AND is_active = TRUE",
                (employee_id,)
            )
            emp = cursor.fetchone() or {}
            created_at = emp.get('created_at')
            cursor.execute(
                """
                SELECT YEAR(date) AS year,
                       ROUND(SUM(TIMESTAMPDIFF(MINUTE, check_in, IFNULL(check_out, NOW()))/60.0), 2) AS hours,
                       COUNT(DISTINCT CASE WHEN status IN ('Present', 'Late') THEN date END) AS worked_days,
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
            import datetime as _dt
            today = _dt.date.today()

            for r in rows:
                y = int(r.get('year'))
                year_start = _dt.date(y, 1, 1)
                year_end = _dt.date(y, 12, 31)
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

