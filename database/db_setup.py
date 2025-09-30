# db_setup.py
import pymysql
import hashlib

def hash_password(password):
    """Hashes the password using SHA-256."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def create_database_and_tables():
    """Creates the 'logix' database and tables if they don't exist, and seeds initial data."""
    try:
        # Connect to MySQL server (without specifying database)
        connection = pymysql.connect(
            host='127.0.0.1',
            port=3306,
            user='root',
            password=''
        )
        cursor = connection.cursor()

        # Create database if not exists
        cursor.execute("CREATE DATABASE IF NOT EXISTS logix CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        connection.select_db('logix')

        # Create employees table with leave_credits and is_active columns
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                employee_id VARCHAR(10) PRIMARY KEY,
                full_name VARCHAR(100) NOT NULL,
                position VARCHAR(50) NOT NULL,
                department VARCHAR(50) NOT NULL,
                image_path VARCHAR(255),
                leave_credits INT DEFAULT 15,
                is_active BOOLEAN DEFAULT TRUE,
                INDEX idx_employee_id (employee_id),
                INDEX idx_is_active (is_active)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        # Add leave_credits column if it doesn't exist
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = 'logix' 
            AND TABLE_NAME = 'employees' 
            AND COLUMN_NAME = 'leave_credits'
        """)
        if cursor.fetchone()[0] == 0:
            cursor.execute("ALTER TABLE employees ADD COLUMN leave_credits INT DEFAULT 15")

        # Add is_active column to employees if it doesn't exist
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = 'logix' 
            AND TABLE_NAME = 'employees' 
            AND COLUMN_NAME = 'is_active'
        """)
        if cursor.fetchone()[0] == 0:
            cursor.execute("ALTER TABLE employees ADD COLUMN is_active BOOLEAN DEFAULT TRUE")
            cursor.execute("CREATE INDEX idx_is_active ON employees(is_active)")

        # Create attendance_records table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance_records (
                record_id INT AUTO_INCREMENT PRIMARY KEY,
                employee_id VARCHAR(10) NOT NULL,
                check_in DATETIME,
                check_out DATETIME,
                status ENUM('Present', 'Late', 'Absent') NOT NULL DEFAULT 'Absent',
                date DATE NOT NULL,
                FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE CASCADE,
                INDEX idx_date (date),
                INDEX idx_employee_date (employee_id, date)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        # Create staff_users table with is_active
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS staff_users (
                username VARCHAR(50) PRIMARY KEY,
                full_name VARCHAR(100) NOT NULL,
                role ENUM('Admin', 'Staff') NOT NULL,
                position VARCHAR(50) NOT NULL,
                password_hash VARCHAR(64) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                INDEX idx_username (username),
                INDEX idx_is_active (is_active)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        # Add is_active column to staff_users if it doesn't exist
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = 'logix' 
            AND TABLE_NAME = 'staff_users' 
            AND COLUMN_NAME = 'is_active'
        """)
        if cursor.fetchone()[0] == 0:
            cursor.execute("ALTER TABLE staff_users ADD COLUMN is_active BOOLEAN DEFAULT TRUE")
            cursor.execute("CREATE INDEX idx_staff_is_active ON staff_users(is_active)")

        # Insert initial staff_users with hashed passwords
        staff_users = [
            (
                'admin',
                'Administrator',
                'Admin',
                'Administrator',
                hash_password('admin123')
            )
        ]
        for user in staff_users:
            cursor.execute("""
                INSERT IGNORE INTO staff_users (username, full_name, role, position, password_hash)
                VALUES (%s, %s, %s, %s, %s)
            """, user)

        # Update any existing records to be active (in case is_active was just added)
        cursor.execute("UPDATE employees SET is_active = TRUE WHERE is_active IS NULL")
        cursor.execute("UPDATE staff_users SET is_active = TRUE WHERE is_active IS NULL")

        connection.commit()
        print("Database setup completed successfully.")
        print("- is_active columns added/verified for employees and staff_users")
        print("- All existing records set to active")

    except pymysql.Error as e:
        print(f"Error during database setup: {e}")
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    create_database_and_tables()