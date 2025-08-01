#!/usr/bin/env python3
"""
سكريبت لإصلاح جدول الوصفات الطبية
"""

import sqlite3
import os

def fix_prescription_table():
    """إصلاح جدول الوصفات الطبية"""
    db_path = 'instance/clinic.db'
    
    if not os.path.exists(db_path):
        print("قاعدة البيانات غير موجودة")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # التحقق من بنية الجدول الحالية
        cursor.execute("PRAGMA table_info(prescription)")
        columns = cursor.fetchall()
        print("أعمدة جدول prescription الحالية:")
        for col in columns:
            print(f"  {col[1]} - {col[2]} - NULL: {not col[3]}")
        
        # التحقق من وجود عمود medications
        has_medications_column = any(col[1] == 'medications' for col in columns)
        
        if has_medications_column:
            print("\nإزالة عمود medications...")
            
            # إنشاء جدول جديد بدون عمود medications
            cursor.execute("""
                CREATE TABLE prescription_new (
                    id INTEGER PRIMARY KEY,
                    visit_id INTEGER NOT NULL UNIQUE,
                    pdf_file VARCHAR(100),
                    created_at DATETIME NOT NULL,
                    FOREIGN KEY (visit_id) REFERENCES visit (id)
                )
            """)
            
            # نسخ البيانات من الجدول القديم (بدون عمود medications)
            cursor.execute("""
                INSERT INTO prescription_new (id, visit_id, pdf_file, created_at)
                SELECT id, visit_id, pdf_file, created_at FROM prescription
            """)
            
            # حذف الجدول القديم
            cursor.execute("DROP TABLE prescription")
            
            # إعادة تسمية الجدول الجديد
            cursor.execute("ALTER TABLE prescription_new RENAME TO prescription")
            
            print("تم إصلاح جدول prescription بنجاح!")
        else:
            print("جدول prescription لا يحتوي على عمود medications")
        
        # التحقق من النتيجة النهائية
        cursor.execute("PRAGMA table_info(prescription)")
        columns = cursor.fetchall()
        print("\nبنية الجدول بعد الإصلاح:")
        for col in columns:
            print(f"  {col[1]} - {col[2]} - NULL: {not col[3]}")
        
        conn.commit()
        print("\nتم حفظ التغييرات بنجاح!")
        
    except Exception as e:
        print(f"خطأ: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_prescription_table()