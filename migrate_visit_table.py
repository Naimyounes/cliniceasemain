import sqlite3
import os
from clinic_app import create_app, db

def migrate_visit_table():
    """تحديث جدول الزيارات ليتطابق مع النموذج الحالي"""
    
    app = create_app()
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'clinic.db')
    
    if not os.path.exists(db_path):
        print("قاعدة البيانات غير موجودة. سيتم إنشاؤها عند تشغيل التطبيق.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # التحقق من الأعمدة الموجودة
        cursor.execute('PRAGMA table_info(visit)')
        existing_columns = [column[1] for column in cursor.fetchall()]
        print(f"الأعمدة الموجودة: {existing_columns}")
        
        # إضافة الأعمدة المفقودة
        columns_to_add = []
        
        if 'symptoms' not in existing_columns:
            columns_to_add.append('symptoms TEXT')
            
        if 'treatment' not in existing_columns:
            columns_to_add.append('treatment TEXT')
            
        if 'price' not in existing_columns:
            columns_to_add.append('price FLOAT')
            
        if 'payment_status' not in existing_columns:
            columns_to_add.append('payment_status VARCHAR(20) DEFAULT "غير مدفوع"')
        
        # إضافة الأعمدة الجديدة
        for column in columns_to_add:
            try:
                cursor.execute(f'ALTER TABLE visit ADD COLUMN {column}')
                print(f"تم إضافة العمود: {column}")
            except sqlite3.OperationalError as e:
                print(f"خطأ في إضافة العمود {column}: {e}")
        
        # تحديث البيانات الموجودة إذا كان هناك عمود fee بدلاً من price
        if 'fee' in existing_columns and 'price' in [col.split()[0] for col in columns_to_add]:
            cursor.execute('UPDATE visit SET price = fee WHERE price IS NULL')
            print("تم نسخ قيم fee إلى price")
        
        # تحديث البيانات الموجودة إذا كان هناك عمود paid بدلاً من payment_status
        if 'paid' in existing_columns and 'payment_status' in [col.split()[0] for col in columns_to_add]:
            cursor.execute('UPDATE visit SET payment_status = CASE WHEN paid = 1 THEN "مدفوع" ELSE "غير مدفوع" END WHERE payment_status IS NULL')
            print("تم تحويل قيم paid إلى payment_status")
        
        conn.commit()
        print("تم تحديث جدول الزيارات بنجاح!")
        
        # عرض الهيكل الجديد
        cursor.execute('PRAGMA table_info(visit)')
        new_columns = cursor.fetchall()
        print("\nالهيكل الجديد لجدول الزيارات:")
        for column in new_columns:
            print(f"  {column[1]} ({column[2]})")
            
    except Exception as e:
        print(f"خطأ في تحديث قاعدة البيانات: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_visit_table()