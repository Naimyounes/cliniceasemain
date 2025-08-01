from clinic_app import create_app, db
from clinic_app.models import User
from werkzeug.security import generate_password_hash

# إنشاء تطبيق Flask
app = create_app()

# دالة لإنشاء مستخدمين افتراضيين
def create_default_users():
    with app.app_context():
        # التحقق من وجود مستخدمين في قاعدة البيانات
        if User.query.count() == 0:
            # إنشاء مستخدم طبيب
            doctor = User(
                username="doctor",
                password=generate_password_hash("doctor123"),
                role="doctor"
            )

            # إنشاء مستخدم سكرتير
            secretary = User(
                username="secretary",
                password=generate_password_hash("secretary123"),
                role="secretary"
            )

            # إضافة المستخدمين لقاعدة البيانات
            db.session.add(doctor)
            db.session.add(secretary)
            db.session.commit()

            print("تم إنشاء المستخدمين الافتراضيين بنجاح")
        else:
            print("يوجد مستخدمين بالفعل في قاعدة البيانات")

# تشغيل البرنامج
if __name__ == "__main__":
    create_default_users()
    print("تم تهيئة المستخدمين، يمكنك الآن تشغيل التطبيق باستخدام run.py")
    print("بيانات تسجيل الدخول:")
    print("طبيب: اسم المستخدم: doctor، كلمة المرور: doctor123")
    print("سكرتير: اسم المستخدم: secretary، كلمة المرور: secretary123")

