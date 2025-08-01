#!/usr/bin/env python3
"""
إصلاح نهائي لقاعدة البيانات
"""

import sqlite3
import os
from datetime import datetime

def fix_database_final():
    """إصلاح نهائي لقاعدة البيانات"""
    
    # حذف قاعدة البيانات القديمة
    db_path = 'instance/clinic.db'
    if os.path.exists(db_path):
        os.remove(db_path)
        print("تم حذف قاعدة البيانات القديمة")
    
    # إنشاء مجلد instance إذا لم يكن موجوداً
    os.makedirs('instance', exist_ok=True)
    
    # إنشاء قاعدة بيانات جديدة
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # إنشاء جدول المستخدمين
        cursor.execute('''
            CREATE TABLE user (
                id INTEGER PRIMARY KEY,
                username VARCHAR(20) UNIQUE NOT NULL,
                password VARCHAR(60) NOT NULL,
                role VARCHAR(20) NOT NULL DEFAULT 'secretary'
            )
        ''')
        
        # إنشاء جدول المرضى
        cursor.execute('''
            CREATE TABLE patient (
                id INTEGER PRIMARY KEY,
                full_name VARCHAR(100) NOT NULL,
                phone VARCHAR(20),
                age INTEGER,
                gender VARCHAR(10),
                address TEXT,
                medical_history TEXT,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # إنشاء جدول التذاكر
        cursor.execute('''
            CREATE TABLE ticket (
                id INTEGER PRIMARY KEY,
                patient_id INTEGER NOT NULL,
                number INTEGER NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'waiting',
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patient (id)
            )
        ''')
        
        # إنشاء جدول الزيارات
        cursor.execute('''
            CREATE TABLE visit (
                id INTEGER PRIMARY KEY,
                patient_id INTEGER NOT NULL,
                doctor_id INTEGER NOT NULL,
                date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                diagnosis TEXT,
                notes TEXT,
                fee FLOAT DEFAULT 0.0,
                paid BOOLEAN NOT NULL DEFAULT 0,
                status VARCHAR(20),
                FOREIGN KEY (patient_id) REFERENCES patient (id),
                FOREIGN KEY (doctor_id) REFERENCES user (id)
            )
        ''')
        
        # إنشاء جدول الأدوية
        cursor.execute('''
            CREATE TABLE medication (
                id INTEGER PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                dosage VARCHAR(100)
            )
        ''')
        
        # إنشاء جدول الوصفات المحددة مسبقاً
        cursor.execute('''
            CREATE TABLE predefined_prescription (
                id INTEGER PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL
            )
        ''')
        
        # إنشاء جدول أدوية الوصفات المحددة مسبقاً
        cursor.execute('''
            CREATE TABLE predefined_prescription_medication (
                id INTEGER PRIMARY KEY,
                predefined_prescription_id INTEGER NOT NULL,
                medication_id INTEGER NOT NULL,
                instructions VARCHAR(200),
                FOREIGN KEY (predefined_prescription_id) REFERENCES predefined_prescription (id),
                FOREIGN KEY (medication_id) REFERENCES medication (id)
            )
        ''')
        
        # إنشاء جدول الوصفات (بدون عمود medications)
        cursor.execute('''
            CREATE TABLE prescription (
                id INTEGER PRIMARY KEY,
                visit_id INTEGER NOT NULL UNIQUE,
                pdf_file VARCHAR(100),
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (visit_id) REFERENCES visit (id)
            )
        ''')
        
        # إنشاء جدول أدوية الوصفات
        cursor.execute('''
            CREATE TABLE prescription_medication (
                id INTEGER PRIMARY KEY,
                prescription_id INTEGER NOT NULL,
                medication_id INTEGER NOT NULL,
                instructions VARCHAR(200),
                FOREIGN KEY (prescription_id) REFERENCES prescription (id),
                FOREIGN KEY (medication_id) REFERENCES medication (id)
            )
        ''')
        
        # إنشاء جدول إعدادات الطبيب
        cursor.execute('''
            CREATE TABLE doctor_settings (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL UNIQUE,
                default_visit_price FLOAT NOT NULL DEFAULT 100.0,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user (id)
            )
        ''')
        
        print("تم إنشاء جميع الجداول بنجاح!")
        
        # إدراج المستخدمين الافتراضيين
        from werkzeug.security import generate_password_hash
        
        doctor_password = generate_password_hash("doctor123")
        secretary_password = generate_password_hash("secretary123")
        
        cursor.execute('''
            INSERT INTO user (username, password, role) VALUES (?, ?, ?)
        ''', ("doctor", doctor_password, "doctor"))
        
        cursor.execute('''
            INSERT INTO user (username, password, role) VALUES (?, ?, ?)
        ''', ("secretary", secretary_password, "secretary"))
        
        print("تم إنشاء المستخدمين الافتراضيين!")
        
        # إدراج الأدوية الافتراضية
        medications = [
            ("باراسيتامول", "500 مجم"),
            ("إيبوبروفين", "400 مجم"),
            ("أموكسيسيلين", "500 مجم"),
            ("أزيثروميسين", "250 مجم"),
            ("أوميبرازول", "20 مجم"),
        ]
        
        for name, dosage in medications:
            cursor.execute('''
                INSERT INTO medication (name, dosage) VALUES (?, ?)
            ''', (name, dosage))
        
        print("تم إضافة الأدوية الافتراضية!")
        
        # إنشاء مريض تجريبي
        cursor.execute('''
            INSERT INTO patient (full_name, phone, age, gender, address, medical_history) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ("أحمد محمد علي", "01234567890", 35, "ذكر", "القاهرة، مصر", "لا يوجد تاريخ مرضي مهم"))
        
        patient_id = cursor.lastrowid
        
        # إنشاء زيارة تجريبية
        cursor.execute('''
            INSERT INTO visit (patient_id, doctor_id, diagnosis, notes, fee, paid, status) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (patient_id, 1, "التهاب في الحلق", "المريض يشكو من ألم في الحلق وصعوبة في البلع", 100.0, 0, "completed"))
        
        print("تم إنشاء بيانات تجريبية!")
        
        # حفظ التغييرات
        conn.commit()
        print("تم حفظ جميع البيانات بنجاح!")
        
        # التحقق من بنية جدول prescription
        cursor.execute("PRAGMA table_info(prescription)")
        columns = cursor.fetchall()
        print("\nبنية جدول prescription:")
        for col in columns:
            null_status = "NULL" if col[3] == 0 else "NOT NULL"
            print(f"  {col[1]} - {col[2]} - {null_status}")
        
    except Exception as e:
        print(f"خطأ: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_database_final()