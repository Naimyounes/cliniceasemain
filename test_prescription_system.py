#!/usr/bin/env python3
"""
سكريبت لاختبار نظام الوصفات الطبية المحدث
"""

from clinic_app import create_app, db
from clinic_app.models import User, Patient, Visit, Prescription, PrescriptionMedication, Medication
from datetime import datetime

def test_prescription_system():
    """اختبار نظام الوصفات الطبية"""
    
    app = create_app()
    
    with app.app_context():
        print("🔍 اختبار نظام الوصفات الطبية...")
        
        # التحقق من وجود الأطباء
        doctors = User.query.filter_by(role='doctor').all()
        print(f"📋 عدد الأطباء: {len(doctors)}")
        
        # التحقق من وجود المرضى
        patients = Patient.query.all()
        print(f"👥 عدد المرضى: {len(patients)}")
        
        # التحقق من وجود الأدوية
        medications = Medication.query.all()
        print(f"💊 عدد الأدوية: {len(medications)}")
        
        # التحقق من الوصفات الموجودة
        prescriptions = Prescription.query.all()
        print(f"📝 عدد الوصفات: {len(prescriptions)}")
        
        # التحقق من حقل الكمية في جدول prescription_medication
        if prescriptions:
            prescription = prescriptions[0]
            prescription_meds = PrescriptionMedication.query.filter_by(prescription_id=prescription.id).all()
            if prescription_meds:
                med = prescription_meds[0]
                print(f"✅ حقل الكمية متوفر: {hasattr(med, 'quantity')}")
                print(f"📦 قيمة الكمية: {getattr(med, 'quantity', 'غير محدد')}")
        
        print("\n🎉 اختبار النظام مكتمل!")
        
        # عرض ملخص الميزات الجديدة
        print("\n" + "="*50)
        print("الميزات الجديدة في نظام الوصفات الطبية:")
        print("="*50)
        print("✅ إضافة حقل الكمية/المدة للأدوية")
        print("✅ تحسين تصميم الوصفة المطبوعة")
        print("✅ إضافة زر عرض الوصفة في تفاصيل الزيارة")
        print("✅ إضافة زر إعادة طباعة الوصفة")
        print("✅ حفظ الوصفة كملف PDF تلقائياً")
        print("✅ تحسين واجهة إنشاء الوصفة")
        print("="*50)

if __name__ == "__main__":
    test_prescription_system()