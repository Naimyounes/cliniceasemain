#!/usr/bin/env python3
"""
سكريبت للتحقق من بنية قاعدة البيانات
"""

import sqlite3
import os

def check_database():
    """التحقق من بنية قاعدة البيانات"""
    db_path = 'instance/clinic.db'
    
    if not os.path.exists(db_path):
        print("قاعدة البيانات غير موجودة")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # الحصول على قائمة الجداول
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"الجداول الموجودة ({len(tables)}):")
        for table in tables:
            print(f"  - {table[0]}")
        
        if len(tables) == 0:
            print("لا توجد جداول في قاعدة البيانات")
        
        # التحقق من بنية جدول prescription
        if any('prescription' in table[0] for table in tables):
            print("\nبنية جدول prescription:")
            cursor.execute("PRAGMA table_info(prescription)")
            columns = cursor.fetchall()
            for col in columns:
                null_status = "NULL" if col[3] == 0 else "NOT NULL"
                print(f"  {col[1]} - {col[2]} - {null_status}")
        
        # التحقق من بنية جدول prescription_medication
        if any('prescription_medication' in table[0] for table in tables):
            print("\nبنية جدول prescription_medication:")
            cursor.execute("PRAGMA table_info(prescription_medication)")
            columns = cursor.fetchall()
            for col in columns:
                null_status = "NULL" if col[3] == 0 else "NOT NULL"
                print(f"  {col[1]} - {col[2]} - {null_status}")
        
    except Exception as e:
        print(f"خطأ: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_database()