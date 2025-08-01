#!/usr/bin/env python3
"""
إضافة أدوية تجريبية لاختبار النظام
"""

from clinic_app import create_app, db
from clinic_app.models import Medication

def add_sample_medications():
    """إضافة أدوية تجريبية"""
    
    app = create_app()
    
    with app.app_context():
        print("💊 إضافة أدوية تجريبية...")
        
        # قائمة الأدوية التجريبية
        sample_medications = [
            {"name": "Paracetamol", "dosage": "500mg"},
            {"name": "Amoxicillin", "dosage": "250mg"},
            {"name": "Ibuprofen", "dosage": "400mg"},
            {"name": "Omeprazole", "dosage": "20mg"},
            {"name": "Metformin", "dosage": "500mg"},
            {"name": "Aspirin", "dosage": "100mg"},
            {"name": "Cetirizine", "dosage": "10mg"},
            {"name": "Simvastatin", "dosage": "20mg"},
            {"name": "Lisinopril", "dosage": "10mg"},
            {"name": "Levothyroxine", "dosage": "50mcg"}
        ]
        
        added_count = 0
        
        for med_data in sample_medications:
            # التحقق من عدم وجود الدواء مسبقاً
            existing = Medication.query.filter_by(name=med_data["name"]).first()
            
            if not existing:
                medication = Medication(
                    name=med_data["name"],
                    dosage=med_data["dosage"]
                )
                db.session.add(medication)
                added_count += 1
                print(f"✅ تم إضافة: {med_data['name']} - {med_data['dosage']}")
            else:
                print(f"ℹ️  موجود مسبقاً: {med_data['name']}")
        
        if added_count > 0:
            db.session.commit()
            print(f"\n🎉 تم إضافة {added_count} دواء جديد!")
        else:
            print("\nℹ️  جميع الأدوية موجودة مسبقاً")
        
        # عرض إجمالي الأدوية
        total_medications = Medication.query.count()
        print(f"📊 إجمالي الأدوية في النظام: {total_medications}")

if __name__ == "__main__":
    add_sample_medications()