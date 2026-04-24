import sqlite3

# Check customers database
print("=== CUSTOMERS DATABASE ===")
try:
    conn = sqlite3.connect('data/customers/customers.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
    tables = [row[0] for row in cursor.fetchall()]
    print(f"Tables: {tables}")

    for table in tables:
        cursor.execute(f'PRAGMA table_info({table})')
        columns = cursor.fetchall()
        print(f"\n{table} columns:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")

        cursor.execute(f'SELECT COUNT(*) FROM {table}')
        count = cursor.fetchone()[0]
        print(f"  Rows: {count}")

    conn.close()
except Exception as e:
    print(f"Error: {e}")

print("\n=== MEMORY DATABASE ===")
try:
    conn = sqlite3.connect('memory/memory.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
    tables = [row[0] for row in cursor.fetchall()]
    print(f"Tables: {tables}")

    for table in tables:
        cursor.execute(f'PRAGMA table_info({table})')
        columns = cursor.fetchall()
        print(f"\n{table} columns:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")

        cursor.execute(f'SELECT COUNT(*) FROM {table}')
        count = cursor.fetchone()[0]
        print(f"  Rows: {count}")

    conn.close()
except Exception as e:
    print(f"Error: {e}")

print("\n=== JARVIS CALENDAR DATABASE ===")
try:
    conn = sqlite3.connect('jarvis_calendar.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
    tables = [row[0] for row in cursor.fetchall()]
    print(f"Tables: {tables}")

    for table in tables:
        cursor.execute(f'PRAGMA table_info({table})')
        columns = cursor.fetchall()
        print(f"\n{table} columns:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")

        cursor.execute(f'SELECT COUNT(*) FROM {table}')
        count = cursor.fetchone()[0]
        print(f"  Rows: {count}")

    conn.close()
except Exception as e:
    print(f"Error: {e}")