from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField, FloatField, FieldList, FormField, DateTimeLocalField
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from clinic_app.models import Patient, Ticket, Visit, Prescription, DoctorSettings, Appointment


class VisitForm(FlaskForm):
    symptoms = TextAreaField("الأعراض", validators=[DataRequired(), Length(min=5, max=500)])
    diagnosis = TextAreaField("التشخيص", validators=[DataRequired(), Length(min=5, max=500)])
    treatment = TextAreaField("العلاج", validators=[DataRequired(), Length(min=5, max=500)])
    notes = TextAreaField("ملاحظات", validators=[Optional(), Length(max=500)])
    status = SelectField("الحالة", choices=[
        ("مستقر", "مستقر"),
        ("متابعة", "متابعة"),
        ("طارئ", "طارئ"),
        ("معلقة", "معلقة")
    ], validators=[DataRequired()])
    price = FloatField("سعر الزيارة", validators=[DataRequired(), NumberRange(min=0)])
    payment_status = SelectField("حالة الدفع", choices=[
        ("مدفوع", "مدفوع"),
        ("غير مدفوع", "غير مدفوع"),
        ("مدفوع جزئياً", "مدفوع جزئياً")
    ], validators=[DataRequired()])
    follow_up_date = DateTimeLocalField('موعد المتابعة', validators=[Optional()], format='%Y-%m-%dT%H:%M')
    follow_up_notes = TextAreaField("ملاحظات الموعد", validators=[Optional(), Length(max=500)])
    submit = SubmitField("حفظ الزيارة")


class MedicationEntryForm(FlaskForm):
    medication_id = SelectField('الدواء', coerce=int, validators=[DataRequired()])
    quantity = StringField('الكمية/المدة', validators=[Optional(), Length(max=50)])
    instructions = StringField('التعليمات', validators=[DataRequired(), Length(min=2, max=200)])


class PrescriptionForm(FlaskForm):
    predefined_prescription = SelectField('اختيار وصفة جاهزة', coerce=int, choices=[(0, 'اختر وصفة جاهزة')], validators=[Optional()])
    medications = FieldList(FormField(MedicationEntryForm), min_entries=1)
    submit = SubmitField('إنشاء وصفة طبية')


class DoctorSettingsForm(FlaskForm):
    default_visit_price = FloatField("سعر الزيارة الافتراضي", validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField("حفظ الإعدادات")


class MedicationForm(FlaskForm):
    name = StringField('اسم الدواء', validators=[DataRequired(), Length(min=2, max=100)])
    dosage = StringField('الجرعة', validators=[DataRequired(), Length(min=2, max=100)])
    submit = SubmitField('إضافة دواء')


class PredefinedPrescriptionForm(FlaskForm):
    name = StringField('اسم الوصفة الجاهزة', validators=[DataRequired(), Length(min=2, max=100)])
    submit = SubmitField('إضافة وصفة جاهزة')


class AppointmentForm(FlaskForm):
    appointment_date = DateTimeLocalField('تاريخ ووقت الموعد', validators=[DataRequired()], format='%Y-%m-%dT%H:%M')
    notes = TextAreaField('ملاحظات حول الموعد', validators=[Optional(), Length(max=500)])
    submit = SubmitField('حجز الموعد')
