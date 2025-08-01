import sqlite3

conn = sqlite3.connect('instance/clinic.db')
cursor = conn.cursor()

# التحقق من الجداول
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f"الجداول ({len(tables)}):")
for table in tables:
    print(f"  - {table[0]}")

# التحقق من بنية جدول prescription
print("\nبنية جدول prescription:")
cursor.execute("PRAGMA table_info(prescription)")
columns = cursor.fetchall()
for col in columns:
    null_status = 'NULL' if col[3] == 0 else 'NOT NULL'
    print(f"  {col[1]} - {col[2]} - {null_status}")

conn.close()