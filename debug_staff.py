#!/usr/bin/env python3
# Debug script to test staff functionality

from database.db_queries import get_all_staff, add_or_update_staff
from database.db_config import get_db_connection

def test_staff_functions():
    print("=== Testing Staff Functions ===")

    # Test 1: Get all staff
    print("\n1. Testing get_all_staff():")
    try:
        staff = get_all_staff()
        print(f"Found {len(staff)} staff members")
        if staff:
            print("Sample staff member:", staff[0])
            print("Keys:", list(staff[0].keys()) if hasattr(staff[0], 'keys') else 'Not a dict')
        else:
            print("No staff found")
    except Exception as e:
        print(f"Error in get_all_staff: {e}")

    # Test 2: Check database structure
    print("\n2. Testing database connection and table structure:")
    try:
        conn = get_db_connection()
        if conn:
            with conn.cursor() as cursor:
                cursor.execute("DESCRIBE staff_users")
                columns = cursor.fetchall()
                print("staff_users table structure:")
                for col in columns:
                    print(f"  {col}")

                # Check actual data
                cursor.execute("SELECT * FROM staff_users LIMIT 1")
                sample = cursor.fetchone()
                print(f"\nSample record: {sample}")
                print(f"Sample type: {type(sample)}")
            conn.close()
        else:
            print("Failed to connect to database")
    except Exception as e:
        print(f"Error checking database: {e}")

    # Test 3: Test update functionality
    print("\n3. Testing update functionality:")
    try:
        if staff:
            test_user = staff[0]
            username = test_user['username'] if isinstance(test_user, dict) else test_user[1]
            print(f"Testing update for user: {username}")

            # Try a simple update (without password change)
            add_or_update_staff(
                username=username,
                full_name="Test Update Name",
                role="Staff",
                position="Test Position",
                password=None,
                is_active=True,
                mode='update'
            )
            print("Update test completed successfully")
        else:
            print("No staff to test update with")
    except Exception as e:
        print(f"Error in update test: {e}")

if __name__ == "__main__":
    test_staff_functions()
