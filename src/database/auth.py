# src/database/auth.py
from __future__ import annotations
from typing import Optional
from .db_config import get_db_connection
from .utils import hash_password


def authenticate_user(username: str, password: str, role: str) -> bool:
    """Authenticate ACTIVE staff/admin user only."""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM staff_users
                WHERE username = %s AND role = %s AND is_active = TRUE
                """,
                (username, role)
            )
            user = cursor.fetchone()
        if user and user.get("password_hash") == hash_password(password):
            return True
        return False
    finally:
        conn.close()


def add_or_update_staff(username: str, full_name: str, role: str, position: str,
                         password: Optional[str] = None, is_active: bool = True,
                         mode: str = "add") -> None:
    """Add or update staff user."""
    conn = get_db_connection()
    if not conn:
        return
    try:
        with conn.cursor() as cursor:
            is_active_val = 1 if is_active else 0
            if mode == "add":
                password_hash = hash_password(password or "")
                cursor.execute(
                    """
                    INSERT INTO staff_users (username, full_name, role, position, password_hash, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (username, full_name, role, position, password_hash, is_active_val)
                )
            else:
                if password:
                    password_hash = hash_password(password)
                    cursor.execute(
                        """
                        UPDATE staff_users
                        SET full_name     = %s,
                            role          = %s,
                            position      = %s,
                            password_hash = %s,
                            is_active     = %s
                        WHERE username = %s
                        """,
                        (full_name, role, position, password_hash, is_active_val, username)
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE staff_users
                        SET full_name = %s,
                            role      = %s,
                            position  = %s,
                            is_active = %s
                        WHERE username = %s
                        """,
                        (full_name, role, position, is_active_val, username)
                    )
            conn.commit()
    finally:
        conn.close()


def get_all_staff() -> list[dict]:
    conn = get_db_connection()
    if not conn:
        return []
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT username, full_name, role, position
                FROM staff_users
                WHERE role = 'Staff' AND is_active = TRUE
                """
            )
            return cursor.fetchall() or []
    finally:
        conn.close()


def delete_staff(username: str) -> None:
    conn = get_db_connection()
    if not conn:
        return
    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE staff_users SET is_active = FALSE WHERE username = %s", (username,))
            conn.commit()
    finally:
        conn.close()

