#!/usr/bin/env python3
"""
تنظيف ملفات PDF المكررة والاحتفاظ بأحدث ملف لكل وصفة
"""

import os
import re
from datetime import datetime
from clinic_app import create_app, db
from clinic_app.models import Prescription

def cleanup_duplicate_pdfs():
    """تنظيف ملفات PDF المكررة"""
    
    app = create_app()
    
    with app.app_context():
        print("🧹 بدء تنظيف ملفات PDF المكررة...")
        
        # مسار مجلد الوصفات
        prescriptions_dir = os.path.join(app.root_path, "static", "prescriptions")
        
        if not os.path.exists(prescriptions_dir):
            print("❌ مجلد الوصفات غير موجود")
            return
        
        # الحصول على جميع ملفات PDF
        pdf_files = [f for f in os.listdir(prescriptions_dir) if f.endswith('.pdf')]
        print(f"📁 عدد ملفات PDF الموجودة: {len(pdf_files)}")
        
        # تجميع الملفات حسب الوصفة
        prescription_files = {}
        pattern = r'prescription_(\d+)_(\d+)_(\d+_\d+)\.pdf'
        
        for filename in pdf_files:
            match = re.match(pattern, filename)
            if match:
                patient_id, visit_id, timestamp = match.groups()
                key = f"{patient_id}_{visit_id}"
                
                if key not in prescription_files:
                    prescription_files[key] = []
                
                prescription_files[key].append({
                    'filename': filename,
                    'timestamp': timestamp,
                    'full_path': os.path.join(prescriptions_dir, filename)
                })
        
        deleted_count = 0
        kept_count = 0
        
        # معالجة كل مجموعة من الملفات
        for key, files in prescription_files.items():
            if len(files) > 1:
                # ترتيب الملفات حسب التاريخ (الأحدث أولاً)
                files.sort(key=lambda x: x['timestamp'], reverse=True)
                
                # الاحتفاظ بأحدث ملف
                latest_file = files[0]
                kept_count += 1
                print(f"✅ الاحتفاظ بـ: {latest_file['filename']}")
                
                # حذف الملفات القديمة
                for old_file in files[1:]:
                    try:
                        os.remove(old_file['full_path'])
                        deleted_count += 1
                        print(f"🗑️  حذف: {old_file['filename']}")
                    except Exception as e:
                        print(f"❌ خطأ في حذف {old_file['filename']}: {e}")
                
                # تحديث قاعدة البيانات
                patient_id, visit_id = key.split('_')
                prescription = Prescription.query.join(Prescription.visit).filter(
                    Prescription.visit.has(patient_id=int(patient_id), id=int(visit_id))
                ).first()
                
                if prescription:
                    new_path = f"static/prescriptions/{latest_file['filename']}"
                    prescription.pdf_file = new_path
                    print(f"📝 تحديث قاعدة البيانات للوصفة {prescription.id}")
            else:
                kept_count += 1
                print(f"ℹ️  ملف واحد فقط: {files[0]['filename']}")
        
        # حفظ التغييرات في قاعدة البيانات
        try:
            db.session.commit()
            print("✅ تم حفظ التغييرات في قاعدة البيانات")
        except Exception as e:
            print(f"❌ خطأ في حفظ قاعدة البيانات: {e}")
            db.session.rollback()
        
        print(f"\n📊 ملخص التنظيف:")
        print(f"🗑️  ملفات محذوفة: {deleted_count}")
        print(f"✅ ملفات محتفظ بها: {kept_count}")
        print(f"📁 إجمالي ملفات PDF الآن: {len(os.listdir(prescriptions_dir))}")
        
        print("\n🎉 تم تنظيف ملفات PDF بنجاح!")

if __name__ == "__main__":
    cleanup_duplicate_pdfs()