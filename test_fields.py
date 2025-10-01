#!/usr/bin/env python3
# Test username and position field handling

from database.db_queries import get_all_staff
from database.db_config import get_db_connection

def test_username_position_fields():
    print("=== Testing Username and Position Field Handling ===")

    # Get staff data
    staff = get_all_staff()
    if not staff:
        print("No staff found to test with")
        return

    username = staff[0]['username']
    print(f"Testing with username: {username}")

    # Get complete user data (simulating what the edit handler does)
    try:
        conn = get_db_connection()
        if conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM staff_users WHERE username = %s", (username,))
                complete_user = cursor.fetchone()
            conn.close()

            print(f"\nComplete user data from database:")
            for key, value in complete_user.items():
                print(f"  {key}: {value}")

            # Test if all required fields are present
            required_fields = ['username', 'full_name', 'role', 'position', 'is_active']
            missing_fields = []

            for field in required_fields:
                if field not in complete_user or complete_user[field] is None:
                    missing_fields.append(field)

            if missing_fields:
                print(f"\n❌ Missing or null fields: {missing_fields}")
            else:
                print(f"\n✓ All required fields are present")

            # Test field values
            print(f"\nField validation:")
            print(f"  Username: '{complete_user['username']}' - {'✓ Valid' if complete_user['username'] else '❌ Empty'}")
            print(f"  Position: '{complete_user['position']}' - {'✓ Valid' if complete_user['position'] else '❌ Empty'}")
            print(f"  Full Name: '{complete_user['full_name']}' - {'✓ Valid' if complete_user['full_name'] else '❌ Empty'}")
            print(f"  Role: '{complete_user['role']}' - {'✓ Valid' if complete_user['role'] else '❌ Empty'}")

    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_username_position_fields()
