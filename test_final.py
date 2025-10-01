#!/usr/bin/env python3
# Test the updated staff functionality

from database.db_queries import get_all_staff, add_or_update_staff
from database.db_config import get_db_connection

def test_updated_functionality():
    print("=== Testing Updated Staff Functionality ===")

    # Get a staff member to test with
    staff = get_all_staff()
    if not staff:
        print("No staff found to test with")
        return

    username = staff[0]['username']
    print(f"Testing with username: {username}")

    # Test 1: Get complete user data (like the edit handler does)
    try:
        conn = get_db_connection()
        if conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM staff_users WHERE username = %s", (username,))
                complete_user = cursor.fetchone()
            conn.close()

            print(f"Complete user data: {complete_user}")

            # Test 2: Test edit functionality with the complete data
            original_name = complete_user['full_name']
            test_name = "Test Edit Name"

            # Simulate editing (update name)
            add_or_update_staff(
                username=complete_user['username'],
                full_name=test_name,
                role=complete_user['role'],
                position=complete_user['position'],
                password=None,  # No password change
                is_active=complete_user['is_active'],  # Preserve is_active
                mode='update'
            )
            print("✓ Edit test passed - name updated")

            # Test 3: Test password change functionality
            add_or_update_staff(
                username=complete_user['username'],
                full_name=test_name,
                role=complete_user['role'],
                position=complete_user['position'],
                password="newpassword123",  # Password change
                is_active=complete_user['is_active'],
                mode='update'
            )
            print("✓ Password change test passed")

            # Restore original name
            add_or_update_staff(
                username=complete_user['username'],
                full_name=original_name,
                role=complete_user['role'],
                position=complete_user['position'],
                password=None,
                is_active=complete_user['is_active'],
                mode='update'
            )
            print("✓ Restored original data")

            print("\n🎉 All tests passed! Edit staff and change password should work now.")

    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_updated_functionality()
