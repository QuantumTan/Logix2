# src/database/employees.py
from __future__ import annotations
from typing import Any, Optional
from .db_config import get_db_connection


def get_all_employees() -> list[dict]:
    """Fetch all ACTIVE employees from the database."""
    conn = get_db_connection()
    if not conn:
        return []
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM employees WHERE is_active = TRUE")
            return cursor.fetchall() or []
    finally:
        conn.close()


def get_employee_by_id(employee_id: int) -> Optional[dict]:
    """Fetch basic employee info by ID (only active)."""
    conn = get_db_connection()
    if not conn:
        return None
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM employees WHERE employee_id = %s AND is_active = TRUE",
                (employee_id,)
            )
            return cursor.fetchone()
    finally:
        conn.close()


def add_employee(full_name: str, position: str, department: str,
                 image_path: Optional[str] = None, leave_credits: int = 15,
                 is_active: bool = True) -> Optional[int]:
    """Insert a new employee letting the DB assign AUTO_INCREMENT ID and return new id.
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
                (full_name, position, department, leave_credits, True if is_active else False)
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
    except Exception:
        # Error updating image path
        conn.rollback()
        return False
    finally:
        conn.close()


def update_employee(employee_id: int, full_name: str, position: str,
                    department: str, image_path: Optional[str] = None,
                    leave_credits: Optional[int] = None) -> None:
    """Update an existing employee."""
    conn = get_db_connection()
    if not conn:
        return
    try:
        with conn.cursor() as cursor:
            set_clause = "full_name = %s, position = %s, department = %s"
            params: list[Any] = [full_name, position, department]
            if image_path is not None:
                set_clause += ", image_path = %s"
                params.append(image_path)
            if leave_credits is not None:
                set_clause += ", leave_credits = %s"
                params.append(leave_credits)
            params.append(employee_id)
            cursor.execute(f"UPDATE employees SET {set_clause} WHERE employee_id = %s", params)
            conn.commit()
    finally:
        conn.close()


def delete_employee(employee_id: int) -> None:
    """Soft delete an employee (mark as inactive instead of deleting)."""
    conn = get_db_connection()
    if not conn:
        return
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE employees SET is_active = FALSE WHERE employee_id = %s",
                (employee_id,)
            )
            conn.commit()
    finally:
        conn.close()


def search_employees(query: str, limit: int = 50) -> list[dict]:
    """Search active employees by name or id substring."""
    q = (query or "").strip()
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
                  AND (full_name LIKE %s OR CAST(employee_id AS CHAR) LIKE %s)
                ORDER BY full_name
                LIMIT %s
                """,
                (like, like, int(limit))
            )
            return cursor.fetchall() or []
    finally:
        conn.close()
