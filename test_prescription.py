#!/usr/bin/env python3
"""
اختبار إنشاء الوصفات
"""

import os
import sys

# إضافة المجلد الحالي إلى مسار Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from clinic_app import create_app, db
from clinic_app.models import *

def test_prescription():
    """اختبار إنشاء وصفة طبية"""
    app = create_app()
    
    with app.app_context():
        # البحث عن زيارة موجودة
        visit = Visit.query.first()
        if not visit:
            print("لا توجد زيارات في قاعدة البيانات")
            return
        
        print(f"اختبار إنشاء وصفة للزيارة رقم: {visit.id}")
        print(f"المريض: {visit.patient.full_name}")
        print(f"الطبيب: {visit.doctor.username}")
        
        try:
            # إنشاء الوصفة
            prescription = Prescription(visit_id=visit.id)
            db.session.add(prescription)
            db.session.flush()
            
            print(f"تم إنشاء الوصفة رقم: {prescription.id}")
            
            # إضافة دواء للوصفة
            medication = Medication.query.first()
            if medication:
                prescription_medication = PrescriptionMedication(
                    prescription_id=prescription.id,
                    medication_id=medication.id,
                    instructions="حبة واحدة كل 8 ساعات لمدة 5 أيام"
                )
                db.session.add(prescription_medication)
                print(f"تم إضافة الدواء: {medication.name}")
            
            db.session.commit()
            print("✅ تم إنشاء الوصفة بنجاح!")
            
            # التحقق من الوصفة
            saved_prescription = Prescription.query.get(prescription.id)
            print(f"الوصفة المحفوظة: ID={saved_prescription.id}, Visit={saved_prescription.visit_id}")
            print(f"عدد الأدوية: {len(saved_prescription.prescription_medications)}")
            
        except Exception as e:
            print(f"❌ خطأ في إنشاء الوصفة: {e}")
            db.session.rollback()

if __name__ == "__main__":
    test_prescription()