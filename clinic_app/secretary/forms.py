from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SubmitField, SelectField, DateTimeLocalField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional
from datetime import date


class PatientForm(FlaskForm):
    """نموذج تسجيل مريض جديد أو تحديث بيانات مريض"""
    full_name = StringField("الاسم الكامل", validators=[DataRequired(), Length(min=3, max=100)])
    phone = StringField("رقم الهاتف", validators=[DataRequired(), Length(min=8, max=20)])
    birth_date = DateField("تاريخ الميلاد", format='%Y-%m-%d', validators=[Optional()], default=date.today)
    gender = SelectField(
        "الجنس", 
        choices=[
            ("", "اختر الجنس"),
            ("male", "ذكر"),
            ("female", "أنثى"),
            ("other", "غير محدد")
        ],
        validators=[Optional()]
    )
    blood_group = SelectField(
        "زمرة الدم",
        choices=[
            ("", "اختر زمرة الدم"),
            ("A+", "A+"),
            ("A-", "A-"),
            ("B+", "B+"),
            ("B-", "B-"),
            ("AB+", "AB+"),
            ("AB-", "AB-"),
            ("O+", "O+"),
            ("O-", "O-")
        ],
        validators=[Optional()]
    )
    address = StringField("العنوان", validators=[Optional(), Length(max=200)])
    submit = SubmitField("حفظ")


class SecretaryAppointmentForm(FlaskForm):
    """نموذج حجز موعد من قبل السكرتيرة"""
    patient_id = SelectField('المريض', coerce=int, validators=[DataRequired()])
    doctor_id = SelectField('الطبيب', coerce=int, validators=[DataRequired()])
    appointment_date = DateTimeLocalField('تاريخ ووقت الموعد', validators=[DataRequired()], format='%Y-%m-%dT%H:%M')
    notes = TextAreaField('ملاحظات حول الموعد', validators=[Optional(), Length(max=500)])
    submit = SubmitField('حجز الموعد')


class PaymentUpdateForm(FlaskForm):
    """نموذج تحديث حالة الدفع"""
    payment_status = SelectField("حالة الدفع", choices=[
        ("مدفوع", "مدفوع"),
        ("غير مدفوع", "غير مدفوع"),
        ("مدفوع جزئياً", "مدفوع جزئياً")
    ], validators=[DataRequired()])
    submit = SubmitField("تحديث حالة الدفع")
