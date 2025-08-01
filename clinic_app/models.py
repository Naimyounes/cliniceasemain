from flask_login import UserMixin
from datetime import datetime
from clinic_app import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    """نموذج المستخدم: للأطباء والسكرتارية"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # doctor, secretary

    # العلاقات
    visits = db.relationship("Visit", backref="doctor", lazy=True)
    settings = db.relationship("DoctorSettings", backref="user", uselist=False, lazy=True)

    def __repr__(self):
        return f"User('{self.username}', '{self.role}')"


class Patient(db.Model):
    """نموذج المريض: يخزن بيانات المريض الأساسية"""
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    birth_date = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(10), nullable=True)  # male, female, other
    blood_group = db.Column(db.String(5), nullable=True)  # A+, A-, B+, B-, AB+, AB-, O+, O-
    address = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # العلاقات
    tickets = db.relationship("Ticket", backref="patient", lazy=True)
    visits = db.relationship("Visit", backref="patient", lazy=True)

    def __repr__(self):
        return f"Patient('{self.full_name}', '{self.phone}')"


class Ticket(db.Model):
    """نموذج التذكرة: يمثل تذكرة انتظار للمريض"""
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False)
    number = db.Column(db.Integer, nullable=False)  # رقم تسلسلي للتذكرة في اليوم
    status = db.Column(db.String(20), nullable=False, default="waiting")  # waiting, called, done
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    
    # حقول نظام الأولوية
    ticket_type = db.Column(db.String(20), nullable=False, default="regular")  # regular, reservation
    appointment_id = db.Column(db.Integer, db.ForeignKey("appointment.id"), nullable=True)  # ربط بالموعد
    priority = db.Column(db.Integer, nullable=False, default=0)  # 0 = عادي، 1 = أولوية
    
    # العلاقات
    appointment = db.relationship("Appointment", backref="tickets", lazy=True)

    def __repr__(self):
        date_str = self.created_at.strftime('%Y-%m-%d') if self.created_at else 'No Date'
        ticket_display = f"{self.number}R" if self.ticket_type == "reservation" else str(self.number)
        return f"Ticket('{ticket_display}', '{self.status}', '{date_str}')"
    
    @property
    def display_number(self):
        """عرض رقم التذكرة مع الحرف R إذا كانت حجز"""
        return f"{self.number}R" if self.ticket_type == "reservation" else str(self.number)



class Visit(db.Model):
    """نموذج الزيارة: يمثل زيارة طبية"""
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    symptoms = db.Column(db.Text, nullable=True)
    diagnosis = db.Column(db.Text, nullable=True)
    treatment = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="مستقر")  # مستقر، متابعة، طارئ، معلقة
    price = db.Column(db.Float, nullable=True)  # سعر الزيارة
    payment_status = db.Column(db.String(20), default="غير مدفوع")  # مدفوع، غير مدفوع، مدفوع جزئياً

    # العلاقات
    prescription = db.relationship("Prescription", backref="visit", uselist=False, lazy=True)

    def __repr__(self):
        date_str = self.date.strftime('%Y-%m-%d') if self.date else 'No Date'
        return f"Visit('{self.patient_id}', '{date_str}')"


class Medication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    dosage = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f"Medication('{self.name}', '{self.dosage}')"

class PredefinedPrescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    medications = db.relationship('PredefinedPrescriptionMedication', backref='predefined_prescription', lazy=True)

    def __repr__(self):
        return f"PredefinedPrescription('{self.name}')"

class PredefinedPrescriptionMedication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    predefined_prescription_id = db.Column(db.Integer, db.ForeignKey('predefined_prescription.id'), nullable=False)
    medication_id = db.Column(db.Integer, db.ForeignKey('medication.id'), nullable=False)
    instructions = db.Column(db.String(200), nullable=True)
    medication = db.relationship('Medication', lazy=True)

    def __repr__(self):
        return f"PredefinedPrescriptionMedication('{self.predefined_prescription_id}', '{self.medication_id}')"

class Prescription(db.Model):
    """نموذج الوصفة الطبية"""
    id = db.Column(db.Integer, primary_key=True)
    visit_id = db.Column(db.Integer, db.ForeignKey("visit.id"), nullable=False, unique=True)
    pdf_file = db.Column(db.String(100), nullable=True)  # مسار الملف على السيرفر
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    prescription_medications = db.relationship('PrescriptionMedication', backref='prescription', lazy=True)

    def __repr__(self):
        date_str = self.created_at.strftime('%Y-%m-%d') if self.created_at else 'No Date'
        return f"Prescription('{self.visit_id}', '{date_str}')"

class PrescriptionMedication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescription.id'), nullable=False)
    medication_id = db.Column(db.Integer, db.ForeignKey('medication.id'), nullable=False)
    instructions = db.Column(db.String(200), nullable=True)
    quantity = db.Column(db.String(50), nullable=True)  # الكمية أو المدة
    medication = db.relationship('Medication', lazy=True)

    def __repr__(self):
        return f"PrescriptionMedication('{self.prescription_id}', '{self.medication_id}')"


class Appointment(db.Model):
    """نموذج الموعد الطبي"""
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    visit_id = db.Column(db.Integer, db.ForeignKey("visit.id"), nullable=True)  # الزيارة المرتبطة بالموعد
    appointment_date = db.Column(db.DateTime, nullable=False)  # تاريخ ووقت الموعد
    status = db.Column(db.String(20), nullable=False, default="مجدول")  # مجدول، مكتمل، ملغي، فائت
    notes = db.Column(db.Text, nullable=True)  # ملاحظات حول الموعد
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # العلاقات
    patient = db.relationship("Patient", backref="appointments", lazy=True)
    doctor = db.relationship("User", backref="doctor_appointments", lazy=True)
    visit = db.relationship("Visit", backref="follow_up_appointment", uselist=False, lazy=True)

    def __repr__(self):
        date_str = self.appointment_date.strftime('%Y-%m-%d %H:%M') if self.appointment_date else 'No Date'
        return f"Appointment('{self.patient_id}', '{date_str}', '{self.status}')"


class DoctorSettings(db.Model):
    """نموذج إعدادات الطبيب"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, unique=True)
    default_visit_price = db.Column(db.Float, nullable=False, default=100.0)  # السعر الافتراضي للزيارة
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"DoctorSettings('{self.user_id}', 'سعر الزيارة: {self.default_visit_price}')"
