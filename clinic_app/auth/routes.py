from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from clinic_app.auth.forms import LoginForm, ChangePasswordForm
from clinic_app.models import User
from clinic_app import db

# إنشاء بلوبرينت للمصادقة
auth = Blueprint("auth", __name__)


@auth.route("/login", methods=["GET", "POST"])
def login():
    """صفحة تسجيل الدخول"""
    if current_user.is_authenticated:
        if current_user.role == "doctor":
            return redirect(url_for("doctor.dashboard"))
        else:
            return redirect(url_for("secretary.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            next_page = request.args.get("next")

            flash(f"مرحبًا بعودتك {user.username}!", "success")

            if user.role == "doctor":
                return redirect(next_page or url_for("doctor.dashboard"))
            else:
                return redirect(next_page or url_for("secretary.dashboard"))
        else:
            flash("فشل تسجيل الدخول. يرجى التحقق من اسم المستخدم وكلمة المرور", "danger")

    return render_template("auth/login.html", title="تسجيل الدخول", form=form)


@auth.route("/logout")
@login_required
def logout():
    """تسجيل الخروج"""
    logout_user()
    flash("تم تسجيل خروجك بنجاح", "info")
    return redirect(url_for("auth.login"))


@auth.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    """تغيير كلمة المرور"""
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        # التحقق من كلمة المرور الحالية
        if not check_password_hash(current_user.password, form.current_password.data):
            flash("كلمة المرور الحالية غير صحيحة", "danger")
            return render_template("auth/change_password.html", title="تغيير كلمة المرور", form=form)
        
        # تحديث كلمة المرور
        current_user.password = generate_password_hash(form.new_password.data)
        db.session.commit()
        
        flash("تم تغيير كلمة المرور بنجاح", "success")
        
        # إعادة توجيه حسب نوع المستخدم
        if current_user.role == "doctor":
            return redirect(url_for("doctor.dashboard"))
        else:
            return redirect(url_for("secretary.dashboard"))
    
    return render_template("auth/change_password.html", title="تغيير كلمة المرور", form=form)
