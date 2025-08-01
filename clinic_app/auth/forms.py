from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo


class LoginForm(FlaskForm):
    """نموذج تسجيل الدخول"""
    username = StringField("اسم المستخدم", validators=[DataRequired()])
    password = PasswordField("كلمة المرور", validators=[DataRequired()])
    submit = SubmitField("تسجيل الدخول")


class ChangePasswordForm(FlaskForm):
    """نموذج تغيير كلمة المرور"""
    current_password = PasswordField("كلمة المرور الحالية", validators=[DataRequired()])
    new_password = PasswordField("كلمة المرور الجديدة", validators=[
        DataRequired(), 
        Length(min=6, message="كلمة المرور يجب أن تكون 6 أحرف على الأقل")
    ])
    confirm_password = PasswordField("تأكيد كلمة المرور الجديدة", validators=[
        DataRequired(),
        EqualTo('new_password', message="كلمات المرور غير متطابقة")
    ])
    submit = SubmitField("تغيير كلمة المرور")
