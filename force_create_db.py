#!/usr/bin/env python3
"""
إنشاء قاعدة البيانات بالقوة
"""

import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash

# إعداد التطبيق
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/clinic.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# تعريف النماذج
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="secretary")

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    address = db.Column(db.Text, nullable=True)
    medical_history = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False)
    number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="waiting")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    patient = db.relationship("Patient", backref=db.backref("tickets", lazy=True))

class Visit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    diagnosis = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    fee = db.Column(db.Float, nullable=True, default=0.0)
    paid = db.Column(db.Boolean, nullable=False, default=False)
    status = db.Column(db.String(20), nullable=True)
    patient = db.relationship("Patient", backref=db.backref("visits", lazy=True))
    doctor = db.relationship("User", backref=db.backref("visits", lazy=True))

class Medication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    dosage = db.Column(db.String(100), nullable=True)

class PredefinedPrescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class PredefinedPrescriptionMedication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    predefined_prescription_id = db.Column(db.Integer, db.ForeignKey('predefined_prescription.id'), nullable=False)
    medication_id = db.Column(db.Integer, db.ForeignKey('medication.id'), nullable=False)
    instructions = db.Column(db.String(200), nullable=True)

class Prescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    visit_id = db.Column(db.Integer, db.ForeignKey("visit.id"), nullable=False, unique=True)
    pdf_file = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class PrescriptionMedication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescription.id'), nullable=False)
    medication_id = db.Column(db.Integer, db.ForeignKey('medication.id'), nullable=False)
    instructions = db.Column(db.String(200), nullable=True)

class DoctorSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, unique=True)
    clinic_name = db.Column(db.String(100), nullable=True)
    doctor_name = db.Column(db.String(100), nullable=True)
    specialization = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)
    visit_fee = db.Column(db.Float, nullable=True, default=50.0)

def create_database():
    with app.app_context():
        # إنشاء المجلد إذا لم يكن موجوداً
        os.makedirs('instance', exist_ok=True)
        
        # إنشاء الجداول
        db.create_all()
        print("تم إنشاء جميع الجداول!")
        
        # إنشاء المستخدمين
        if not User.query.first():
            doctor = User(
                username="doctor",
                password=generate_password_hash("doctor123"),
                role="doctor"
            )
            
            secretary = User(
                username="secretary",
                password=generate_password_hash("secretary123"),
                role="secretary"
            )
            
            db.session.add(doctor)
            db.session.add(secretary)
            db.session.commit()
            print("تم إنشاء المستخدمين!")
        
        # إضافة الأدوية
        if not Medication.query.first():
            medications = [
                Medication(name="باراسيتامول", dosage="500 مجم"),
                Medication(name="إيبوبروفين", dosage="400 مجم"),
                Medication(name="أموكسيسيلين", dosage="500 مجم"),
            ]
            
            for med in medications:
                db.session.add(med)
            
            db.session.commit()
            print("تم إضافة الأدوية!")
        
        print("تم إعداد قاعدة البيانات بنجاح!")

if __name__ == "__main__":
    create_database()