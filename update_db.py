
from clinic_app import create_app, db
from clinic_app.models import User, Patient, Ticket, Visit, Prescription, DoctorSettings
import os

# إنشاء التطبيق باستخدام تكوين التطوير
app = create_app()

with app.app_context():
    # حذف قاعدة البيانات القديمة إذا وجدت
    db_path = os.path.join(app.instance_path, 'clinic.db')
    if os.path.exists(db_path):
        os.remove(db_path)
        print("تم حذف قاعدة البيانات القديمة")

    # إنشاء جميع الجداول من جديد
    db.create_all()
    print("تم إنشاء قاعدة بيانات جديدة")

    # إنشاء حسابات المستخدمين الافتراضية
    doctor = User(username="doctor", password="$2b$12$dMD8u9fzcvCr19Au9rSAweMYKEPLMnG9DEWQTtF19QnXhm1J1vOyy", role="doctor")
    secretary = User(username="secretary", password="$2b$12$dMD8u9fzcvCr19Au9rSAweMYKEPLMnG9DEWQTtF19QnXhm1J1vOyy", role="secretary")

    db.session.add(doctor)
    db.session.add(secretary)
    db.session.commit()

    # إضافة إعدادات افتراضية للطبيب
    doctor_settings = DoctorSettings(user_id=doctor.id, default_visit_price=100.0)
    db.session.add(doctor_settings)
    db.session.commit()

    print("تم إنشاء حسابات المستخدمين الافتراضية:")
    print("- اسم المستخدم: doctor, كلمة المرور: 123456")
    print("- اسم المستخدم: secretary, كلمة المرور: 123456")
    print("\nالتطبيق جاهز للاستخدام الآن!")
