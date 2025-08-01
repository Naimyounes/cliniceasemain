#!/usr/bin/env python3
"""
سكريبت لإنشاء قاعدة البيانات
"""

from clinic_app import create_app, db
from clinic_app.models import User, Patient, Ticket, Visit, Prescription, PrescriptionMedication, Medication, PredefinedPrescription, PredefinedPrescriptionMedication, DoctorSettings
from werkzeug.security import generate_password_hash

def create_database():
    """إنشاء قاعدة البيانات والجداول"""
    app = create_app()
    
    with app.app_context():
        # إنشاء جميع الجداول
        db.create_all()
        print("تم إنشاء جميع الجداول بنجاح!")
        
        # إنشاء مستخدمين افتراضيين إذا لم يكونوا موجودين
        if not User.query.first():
            # إنشاء مستخدم طبيب افتراضي
            doctor = User(
                username="doctor",
                password=generate_password_hash("doctor123"),
                role="doctor"
            )
            
            # إنشاء مستخدم سكرتير افتراضي
            secretary = User(
                username="secretary",
                password=generate_password_hash("secretary123"),
                role="secretary"
            )
            
            db.session.add(doctor)
            db.session.add(secretary)
            db.session.commit()
            print("تم إنشاء المستخدمين الافتراضيين!")
        
        # إضافة بعض الأدوية الافتراضية
        if not Medication.query.first():
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
            print("تم إضافة الأدوية الافتراضية!")
        
        print("تم إعداد قاعدة البيانات بنجاح!")

if __name__ == "__main__":
    create_database()