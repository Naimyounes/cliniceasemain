#!/usr/bin/env python3
"""
إنشاء بيانات تجريبية للاختبار
"""

import os
import sys
from datetime import datetime, timedelta

# إضافة المجلد الحالي إلى مسار Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from clinic_app import create_app, db
from clinic_app.models import *
from werkzeug.security import generate_password_hash

def create_test_data():
    """إنشاء بيانات تجريبية"""
    app = create_app()
    
    with app.app_context():
        # إنشاء مريض تجريبي
        if not Patient.query.first():
            patient = Patient(
                full_name="أحمد محمد علي",
                phone="01234567890",
                age=35,
                gender="ذكر",
                address="القاهرة، مصر",
                medical_history="لا يوجد تاريخ مرضي مهم"
            )
            db.session.add(patient)
            db.session.commit()
            print("تم إنشاء مريض تجريبي")
            
            # إنشاء تذكرة للمريض
            ticket = Ticket(
                patient_id=patient.id,
                number=1,
                status="waiting"
            )
            db.session.add(ticket)
            
            # إنشاء زيارة للمريض
            doctor = User.query.filter_by(role="doctor").first()
            if doctor:
                visit = Visit(
                    patient_id=patient.id,
                    doctor_id=doctor.id,
                    date=datetime.now(),
                    diagnosis="التهاب في الحلق",
                    notes="المريض يشكو من ألم في الحلق وصعوبة في البلع",
                    fee=100.0,
                    paid=False,
                    status="completed"
                )
                db.session.add(visit)
                db.session.commit()
                print("تم إنشاء زيارة تجريبية")
        
        # إنشاء إعدادات الطبيب
        doctor = User.query.filter_by(role="doctor").first()
        if doctor and not DoctorSettings.query.filter_by(user_id=doctor.id).first():
            doctor_settings = DoctorSettings(
                user_id=doctor.id,
                default_visit_price=100.0
            )
            db.session.add(doctor_settings)
            db.session.commit()
            print("تم إنشاء إعدادات الطبيب")
        
        print("تم إنشاء جميع البيانات التجريبية بنجاح!")

if __name__ == "__main__":
    create_test_data()