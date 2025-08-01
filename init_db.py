#!/usr/bin/env python3
"""
سكريبت بسيط لإنشاء قاعدة البيانات
"""

import os
import sys

# إضافة المجلد الحالي إلى مسار Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from clinic_app import create_app, db
from clinic_app.models import *
from werkzeug.security import generate_password_hash

def init_database():
    """إنشاء قاعدة البيانات"""
    print("إنشاء التطبيق...")
    app = create_app()
    
    with app.app_context():
        print("إنشاء الجداول...")
        db.create_all()
        
        # التحقق من إنشاء الجداول
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"تم إنشاء {len(tables)} جدول:")
        for table in tables:
            print(f"  - {table}")
        
        # إنشاء المستخدمين الافتراضيين
        if not User.query.first():
            print("إنشاء المستخدمين الافتراضيين...")
            
            doctor = User(
                username="doctor",
                password=generate_password_hash("doctor123"),
                role="doctor"
            )
            
            secretary = User(
                username="secretary", 
                password=generate_password_hash("secretary123"),
                role="secretary"
            )
            
            db.session.add(doctor)
            db.session.add(secretary)
            db.session.commit()
            print("تم إنشاء المستخدمين!")
        
        # إضافة أدوية افتراضية
        if not Medication.query.first():
            print("إضافة الأدوية الافتراضية...")
            medications = [
                Medication(name="باراسيتامول", dosage="500 مجم"),
                Medication(name="إيبوبروفين", dosage="400 مجم"),
                Medication(name="أموكسيسيلين", dosage="500 مجم"),
                Medication(name="أزيثروميسين", dosage="250 مجم"),
                Medication(name="أوميبرازول", dosage="20 مجم"),
            ]
            
            for med in medications:
                db.session.add(med)
            
            db.session.commit()
            print("تم إضافة الأدوية!")
        
        print("تم إعداد قاعدة البيانات بنجاح!")

if __name__ == "__main__":
    init_database()