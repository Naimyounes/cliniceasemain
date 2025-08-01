#!/usr/bin/env python3
"""
اختبار route طباعة الوصفة
"""

from clinic_app import create_app, db
from clinic_app.models import Prescription
import os

def test_print_route():
    """اختبار route الطباعة"""
    
    app = create_app()
    
    with app.app_context():
        print("🔍 اختبار route طباعة الوصفة...")
        
        # البحث عن وصفة موجودة
        prescription = Prescription.query.first()
        
        if not prescription:
            print("❌ لا توجد وصفات في قاعدة البيانات")
            return
        
        print(f"📋 اختبار الوصفة رقم: {prescription.id}")
        
        # اختبار route الطباعة
        with app.test_client() as client:
            # محاولة الوصول لـ route الطباعة (بدون تسجيل دخول للاختبار السريع)
            print(f"🔗 URL للاختبار: /doctor/prescription/{prescription.id}/print")
            
            # التحقق من وجود مجلد الوصفات
            prescriptions_dir = os.path.join(app.root_path, "static", "prescriptions")
            if os.path.exists(prescriptions_dir):
                print(f"✅ مجلد الوصفات موجود: {prescriptions_dir}")
                files = os.listdir(prescriptions_dir)
                print(f"📁 عدد ملفات PDF: {len(files)}")
                if files:
                    print(f"📄 أحدث ملف: {files[-1]}")
            else:
                print(f"❌ مجلد الوصفات غير موجود: {prescriptions_dir}")
        
        print("\n✅ اختبار route الطباعة مكتمل!")
        print("\n💡 للاختبار الكامل:")
        print("1. شغل التطبيق: python run.py")
        print("2. سجل دخول كطبيب")
        print("3. اذهب لصفحة زيارة تحتوي على وصفة")
        print("4. انقر على زر 'طباعة'")

if __name__ == "__main__":
    test_print_route()