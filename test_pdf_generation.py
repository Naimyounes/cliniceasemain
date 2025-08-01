#!/usr/bin/env python3
"""
اختبار إنشاء PDF للوصفة الطبية
"""

from clinic_app import create_app, db
from clinic_app.models import User, Patient, Visit, Prescription, PrescriptionMedication, Medication
from clinic_app.doctor.utils import generate_prescription_pdf
from datetime import datetime

def test_pdf_generation():
    """اختبار إنشاء PDF للوصفة"""
    
    app = create_app()
    
    with app.app_context():
        print("🔍 اختبار إنشاء PDF للوصفة الطبية...")
        
        # البحث عن وصفة موجودة
        prescription = Prescription.query.first()
        
        if not prescription:
            print("❌ لا توجد وصفات في قاعدة البيانات")
            return
        
        visit = prescription.visit
        print(f"📋 اختبار الوصفة رقم: {prescription.id}")
        print(f"👤 المريض: {visit.patient.full_name}")
        print(f"👨‍⚕️ الطبيب: {visit.doctor.username}")
        
        try:
            # إنشاء PDF
            pdf_path = generate_prescription_pdf(prescription, visit)
            print(f"✅ تم إنشاء PDF بنجاح: {pdf_path}")
            
            # التحقق من وجود الملف
            import os
            full_path = os.path.join(app.root_path, pdf_path)
            if os.path.exists(full_path):
                file_size = os.path.getsize(full_path)
                print(f"📄 حجم الملف: {file_size} بايت")
                print(f"📁 مسار الملف: {full_path}")
            else:
                print("❌ الملف غير موجود")
                
        except Exception as e:
            print(f"❌ خطأ في إنشاء PDF: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_pdf_generation()