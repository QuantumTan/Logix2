# db_setup.py
import pymysql

def create_database_and_tables():
    """Creates the 'logix' database and tables if they don't exist, and seeds initial data."""
    # Import hash_password from db_queries to avoid duplication
    from .db_queries import hash_password

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
                employee_id INT PRIMARY KEY AUTO_INCREMENT,
                full_name VARCHAR(100) NOT NULL,
                position VARCHAR(50) NOT NULL,
                department VARCHAR(50) NOT NULL,
                image_path VARCHAR(255),
                leave_credits INT DEFAULT 15,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_employee_id (employee_id),
                INDEX idx_is_active (is_active),
                INDEX idx_created_at (created_at)
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

        # Add created_at column to employees if it doesn't exist
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = 'logix' 
            AND TABLE_NAME = 'employees' 
            AND COLUMN_NAME = 'created_at'
        """)
        if cursor.fetchone()[0] == 0:
            cursor.execute("ALTER TABLE employees ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            cursor.execute("CREATE INDEX idx_created_at ON employees(created_at)")
            # Update existing employees with current timestamp if they don't have created_at
            cursor.execute("UPDATE employees SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")

        # Create attendance_records table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance_records (
                record_id INT AUTO_INCREMENT PRIMARY KEY,
                employee_id INT NOT NULL,
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

        # --- MIGRATION: convert employee_id from VARCHAR to INT if needed ---
        cursor.execute("""
            SELECT DATA_TYPE
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = 'logix'
              AND TABLE_NAME = 'employees'
              AND COLUMN_NAME = 'employee_id'
        """)
        dtype = cursor.fetchone()
        if dtype and dtype[0].lower() != 'int':
            try:
                # Temporarily disable FK checks
                cursor.execute("SET FOREIGN_KEY_CHECKS=0")

                # Find existing FK name on attendance_records.employee_id
                cursor.execute("""
                    SELECT CONSTRAINT_NAME
                    FROM information_schema.KEY_COLUMN_USAGE
                    WHERE TABLE_SCHEMA = 'logix'
                      AND TABLE_NAME = 'attendance_records'
                      AND COLUMN_NAME = 'employee_id'
                      AND REFERENCED_TABLE_NAME = 'employees'
                """)
                fk = cursor.fetchone()
                if fk and fk[0]:
                    cursor.execute(f"ALTER TABLE attendance_records DROP FOREIGN KEY `{fk[0]}`")

                # Normalize values by stripping leading '#' and casting to int
                cursor.execute("UPDATE employees SET employee_id = CAST(REPLACE(employee_id, '#', '') AS UNSIGNED)")
                cursor.execute("UPDATE attendance_records SET employee_id = CAST(REPLACE(employee_id, '#', '') AS UNSIGNED)")

                # Alter column types to INT
                cursor.execute("ALTER TABLE employees MODIFY employee_id INT NOT NULL")
                cursor.execute("ALTER TABLE attendance_records MODIFY employee_id INT NOT NULL")

                # Recreate FK with a stable name
                cursor.execute("""
                    ALTER TABLE attendance_records
                    ADD CONSTRAINT fk_attendance_employee
                    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
                    ON DELETE CASCADE
                """)
            finally:
                cursor.execute("SET FOREIGN_KEY_CHECKS=1")

        # Ensure employee_id is AUTO_INCREMENT and set next AUTO_INCREMENT value beyond current MAX(id)
        try:
            # Check if column is already AUTO_INCREMENT
            cursor.execute(
                """
                SELECT EXTRA FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = 'logix' AND TABLE_NAME = 'employees' AND COLUMN_NAME = 'employee_id'
                """
            )
            extra = cursor.fetchone()
            is_auto = False
            if extra:
                # Depending on cursor type, extra may be tuple or dict
                is_auto = ('auto_increment' in (extra[0].lower() if isinstance(extra, tuple) else str(extra.get('EXTRA','')).lower()))
            if not is_auto:
                cursor.execute("ALTER TABLE employees MODIFY employee_id INT NOT NULL AUTO_INCREMENT")

            # Set AUTO_INCREMENT to max(employee_id)+1 or 10000 if table empty
            cursor.execute("SELECT COALESCE(MAX(employee_id), 9999) + 1 FROM employees")
            next_id = cursor.fetchone()
            next_val = next_id[0] if isinstance(next_id, tuple) else list(next_id.values())[0]
            if next_val is None or int(next_val) < 10000:
                next_val = 10000
            cursor.execute(f"ALTER TABLE employees AUTO_INCREMENT = {int(next_val)}")
        except Exception as e:
            print(f"[db_setup] Warning: failed to enforce AUTO_INCREMENT on employees.employee_id: {e}")

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