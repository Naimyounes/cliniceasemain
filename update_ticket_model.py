#!/usr/bin/env python3
"""
تحديث نموذج التذكرة لإضافة نظام الأولوية
"""

from clinic_app import create_app, db
from clinic_app.models import Ticket

def update_ticket_model():
    """تحديث نموذج التذكرة بإضافة الحقول الجديدة"""
    app = create_app()
    
    with app.app_context():
        try:
            # إعادة إنشاء الجداول مع الحقول الجديدة
            db.drop_all()
            db.create_all()
            print("✅ تم إعادة إنشاء قاعدة البيانات مع الحقول الجديدة")
            print("🎉 تم تحديث نموذج التذكرة بنجاح!")
            
        except Exception as e:
            print(f"❌ خطأ في تحديث قاعدة البيانات: {e}")
            db.session.rollback()

if __name__ == "__main__":
    update_ticket_model()