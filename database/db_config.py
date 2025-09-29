# db_config.py
import pymysql

def get_db_connection():
    """
    Establishes and returns a connection to the MySQL database using XAMPP defaults.
    """
    try:
        connection = pymysql.connect(
            host='127.0.0.1',
            port=3306,
            user='root',
            password='',
            database='logix',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except pymysql.Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None