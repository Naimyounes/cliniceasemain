from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
import os
from datetime import datetime

# تهيئة المكتبات
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)

    # إعدادات التطبيق
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "default_secret_key_for_development")
    # إنشاء مجلد instance إذا لم يكن موجوداً
    instance_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance')
    os.makedirs(instance_path, exist_ok=True)
    
    db_path = os.path.join(instance_path, 'clinic.db')
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", f"sqlite:///{db_path}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # تهيئة المكتبات مع التطبيق
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"
    login_manager.login_message = "يرجى تسجيل الدخول للوصول إلى هذه الصفحة"

    # تضمين النماذج والوحدات
    from clinic_app.models import User, Patient, Ticket, Visit, Prescription

    # تضمين المسارات
    from clinic_app.auth.routes import auth
    from clinic_app.doctor.routes import doctor
    from clinic_app.secretary.routes import secretary
    from clinic_app.main.routes import main

    # تسجيل المسارات
    app.register_blueprint(auth)
    app.register_blueprint(doctor)
    app.register_blueprint(secretary)
    app.register_blueprint(main)

    # إنشاء قاعدة البيانات
    with app.app_context():
        db.create_all()
        # إنشاء مستخدمين افتراضيين إذا كانت قاعدة البيانات فارغة
        if not User.query.first():
            create_default_users()

    @app.context_processor
    def utility_processor():
        def get_current_year():
            return datetime.now().year
        
        def format_date(date, format_str='%Y-%m-%d'):
            """تنسيق التاريخ"""
            if date:
                return date.strftime(format_str)
            return ''
        
        def format_datetime(datetime_obj, format_str='%Y-%m-%d %H:%M'):
            """تنسيق التاريخ والوقت"""
            if datetime_obj:
                return datetime_obj.strftime(format_str)
            return ''
        
        def get_current_date():
            """الحصول على التاريخ الحالي"""
            return datetime.now().date()
        
        def get_current_datetime():
            """الحصول على التاريخ والوقت الحالي"""
            return datetime.now()
        
        def get_arabic_date():
            """الحصول على التاريخ بالعربية"""
            now = datetime.now()
            days = ['الأحد', 'الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت']
            months = ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
                     'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر']
            
            day_name = days[now.weekday()]
            month_name = months[now.month - 1]
            
            return f"{day_name}، {now.day} {month_name} {now.year}"
        
        def get_secretary_notifications():
            """الحصول على إشعارات السكرتيرة"""
            from flask_login import current_user
            if not current_user.is_authenticated or current_user.role != 'secretary':
                return {'today_not_contacted': [], 'tomorrow_not_contacted': []}
            
            from clinic_app.models import Appointment
            from datetime import timedelta
            
            today = datetime.now().date()
            tomorrow = today + timedelta(days=1)
            
            # مواعيد اليوم
            today_appointments = Appointment.query.filter(
                db.func.date(Appointment.appointment_date) == today,
                Appointment.status == "مجدول"
            ).all()
            
            # مواعيد الغد
            tomorrow_appointments = Appointment.query.filter(
                db.func.date(Appointment.appointment_date) == tomorrow,
                Appointment.status == "مجدول"
            ).all()
            
            # حساب المواعيد التي لم يتم الاتصال بها
            today_not_contacted = [apt for apt in today_appointments if not apt.notes or 'تم الاتصال' not in apt.notes]
            tomorrow_not_contacted = [apt for apt in tomorrow_appointments if not apt.notes or 'تم الاتصال' not in apt.notes]
            
            return {
                'today_not_contacted': today_not_contacted,
                'tomorrow_not_contacted': tomorrow_not_contacted
            }

        return dict(
            get_current_year=get_current_year,
            format_date=format_date,
            format_datetime=format_datetime,
            get_current_date=get_current_date,
            get_current_datetime=get_current_datetime,
            get_arabic_date=get_arabic_date,
            get_secretary_notifications=get_secretary_notifications
        )

    return app


def create_default_users():
    """إنشاء مستخدمين افتراضيين عند بدء التطبيق لأول مرة"""
    from clinic_app.models import User
    from werkzeug.security import generate_password_hash

    # إنشاء مستخدم طبيب افتراضي
    doctor = User(
        username="doctor",
        password=generate_password_hash("doctor123"),
        role="doctor"
    )

    # إنشاء مستخدم سكرتير افتراضي
    secretary = User(
        username="secretary",
        password=generate_password_hash("secretary123"),
        role="secretary"
    )

    db.session.add(doctor)
    db.session.add(secretary)
    db.session.commit()
