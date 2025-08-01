#!/usr/bin/env python3
"""
سكريبت لتحديث قاعدة البيانات لإضافة حقل الكمية للأدوية في الوصفات الطبية
"""

import sqlite3
import os
from datetime import datetime

def update_database():
    """تحديث قاعدة البيانات لإضافة حقل الكمية"""
    
    # مسار قاعدة البيانات
    db_path = os.path.join('instance', 'clinic.db')
    
    if not os.path.exists(db_path):
        print("❌ ملف قاعدة البيانات غير موجود!")
        return False
    
    try:
        # الاتصال بقاعدة البيانات
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 بدء تحديث قاعدة البيانات...")
        
        # التحقق من وجود حقل الكمية
        cursor.execute("PRAGMA table_info(prescription_medication)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'quantity' not in columns:
            print("➕ إضافة حقل الكمية إلى جدول prescription_medication...")
            cursor.execute("""
                ALTER TABLE prescription_medication 
                ADD COLUMN quantity VARCHAR(50)
            """)
            print("✅ تم إضافة حقل الكمية بنجاح!")
        else:
            print("ℹ️  حقل الكمية موجود بالفعل")
        
        # حفظ التغييرات
        conn.commit()
        print("✅ تم تحديث قاعدة البيانات بنجاح!")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ خطأ في قاعدة البيانات: {e}")
        return False
        
    except Exception as e:
        print(f"❌ خطأ عام: {e}")
        return False
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("=" * 50)
    print("تحديث قاعدة البيانات - نظام الوصفات الطبية")
    print("=" * 50)
    
    success = update_database()
    
    if success:
        print("\n🎉 تم تحديث قاعدة البيانات بنجاح!")
        print("يمكنك الآن تشغيل التطبيق واستخدام حقل الكمية في الوصفات الطبية")
    else:
        print("\n❌ فشل في تحديث قاعدة البيانات!")
        print("يرجى التحقق من الأخطاء أعلاه")
    
    print("=" * 50)