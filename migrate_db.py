import sqlite3
import os

db_path = 'bus_tracking.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE student_profile ADD COLUMN parent_name VARCHAR(100)")
        conn.commit()
        print("Column 'parent_name' added successfully to 'student_profile'.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("Column 'parent_name' already exists.")
        else:
            print(f"Error: {e}")
    finally:
        conn.close()
else:
    print(f"Database {db_path} not found. It will be created with the new schema on first run.")
