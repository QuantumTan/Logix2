#!/usr/bin/env python3
# Debug script to test the exact edit flow

from database.db_queries import get_all_staff
from database.db_config import get_db_connection

def test_edit_flow():
    print("=== Testing Edit Staff Flow ===")

    # Test the exact flow used in _make_edit_staff_handler
    staff = get_all_staff()
    if staff:
        username = staff[0]['username']
        print(f"Testing edit flow for username: {username}")

        try:
            conn = get_db_connection()
            if conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM staff_users WHERE username = %s", (username,))
                    complete_user = cursor.fetchone()
                conn.close()

                print(f"Complete user data: {complete_user}")
                print(f"Type: {type(complete_user)}")
                print(f"Keys: {list(complete_user.keys()) if complete_user else 'None'}")

                # Test what happens when we access fields
                if complete_user:
                    print(f"is_active value: {complete_user.get('is_active')}")
                    print(f"is_active type: {type(complete_user.get('is_active'))}")

        except Exception as e:
            print(f"Error in edit flow: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_edit_flow()
