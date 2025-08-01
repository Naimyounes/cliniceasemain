from flask import Blueprint, render_template, url_for, flash, redirect, request, abort, current_app, jsonify, send_file
from flask_login import login_required, current_user
from clinic_app import db
from clinic_app.models import User, Patient, Ticket, Visit, Prescription, DoctorSettings, Medication, PrescriptionMedication, PredefinedPrescription, PredefinedPrescriptionMedication, Appointment
from clinic_app.doctor.forms import VisitForm, PrescriptionForm, DoctorSettingsForm, MedicationForm, PredefinedPrescriptionForm, AppointmentForm
from clinic_app.doctor.utils import generate_prescription_pdf
from datetime import datetime
import os
import calendar
from functools import wraps

# إنشاء بلوبرينت للطبيب
doctor = Blueprint("doctor", __name__)


def doctor_required(f):
    """تأكد أن المستخدم هو طبيب"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role != "doctor":
            flash("غير مسموح لك بالوصول إلى هذه الصفحة", "danger")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function


@doctor.route("/dashboard/doctor")
@login_required
@doctor_required
def dashboard():
    """لوحة تحكم الطبيب"""
    # الحصول على قائمة الانتظار الحالية مرتبة حسب الأولوية
    today = datetime.now().date()
    waiting_tickets = Ticket.query.filter(
        db.func.date(Ticket.created_at) == today,
        Ticket.status == "waiting"
    ).order_by(
        Ticket.priority.desc(),  # الأولوية أولاً
        Ticket.number.asc()      # ثم الرقم
    ).all()

    # الحصول على المريض الحالي - الذي لديه تذكرة بحالة called
    current_ticket = Ticket.query.filter(
        db.func.date(Ticket.created_at) == today,
        Ticket.status == "called"
    ).first()
    current_patient = None

    if current_ticket:
        current_patient = Patient.query.get(current_ticket.patient_id)

    # حساب الإحصائيات اليومية
    today = datetime.now().date()
    
    # زيارات اليوم
    daily_visits = Visit.query.filter(
        Visit.doctor_id == current_user.id,
        db.func.date(Visit.date) == today
    ).all()
    
    # إيرادات اليوم
    daily_revenue = sum(visit.price or 0 for visit in daily_visits if visit.payment_status == "مدفوع")
    
    # المرضى الجدد اليوم
    new_patients_today = Patient.query.filter(
        db.func.date(Patient.created_at) == today
    ).count()
    
    # مواعيد اليوم
    today_appointments = Appointment.query.filter(
        Appointment.doctor_id == current_user.id,
        db.func.date(Appointment.appointment_date) == today
    ).all()
    
    # المواعيد القادمة (من الغد فما بعد)
    upcoming_appointments = Appointment.query.filter(
        Appointment.doctor_id == current_user.id,
        Appointment.appointment_date > datetime.now(),
        Appointment.status == "مجدول"
    ).count()
    
    daily_stats = {
        'visits_count': len(daily_visits),
        'revenue': daily_revenue,
        'new_patients': new_patients_today,
        'today_appointments': len(today_appointments),
        'upcoming_appointments': upcoming_appointments
    }

    return render_template(
        "doctor/dashboard.html",
        title="لوحة تحكم الطبيب",
        waiting_tickets=waiting_tickets,
        current_ticket=current_ticket,
        current_patient=current_patient,
        daily_stats=daily_stats
    )


@doctor.route("/doctor/next-patient")
@login_required
@doctor_required
def next_patient():
    """استدعاء المريض التالي"""
    # التأكد من إنهاء الحالة الحالية إذا كانت موجودة
    current_ticket = Ticket.query.filter_by(status="called").first()
    if current_ticket:
        # تغيير حالة التذكرة الحالية إلى مكتمل
        current_ticket.status = "done"
        db.session.commit()

    # الحصول على المريض التالي في قائمة الانتظار
    next_ticket = Ticket.query.filter_by(status="waiting").order_by(Ticket.number).first()

    if next_ticket:
        next_ticket.status = "called"
        db.session.commit()
        flash(f"تم استدعاء المريض: {next_ticket.patient.full_name}", "success")
    else:
        flash("لا يوجد مرضى في قائمة الانتظار", "info")

    return redirect(url_for("doctor.dashboard"))


@doctor.route("/doctor/patient/<int:patient_id>", methods=["GET", "POST"])
@login_required
@doctor_required
def patient_visit(patient_id):
    """إنشاء زيارة جديدة للمريض"""
    patient = Patient.query.get_or_404(patient_id)
    
    # الحصول على سعر الزيارة الافتراضي من إعدادات الطبيب
    settings = DoctorSettings.query.filter_by(user_id=current_user.id).first()
    default_price = 100.0
    if settings:
        default_price = settings.default_visit_price
    
    form = VisitForm()
    if request.method == "GET":
        form.price.data = default_price

    if form.validate_on_submit():
        # إنشاء زيارة جديدة
        visit = Visit(
            patient_id=patient.id,
            doctor_id=current_user.id,
            symptoms=form.symptoms.data,
            diagnosis=form.diagnosis.data,
            treatment=form.treatment.data,
            notes=form.notes.data,
            status=form.status.data,
            price=form.price.data,
            payment_status=form.payment_status.data
        )

        db.session.add(visit)
        db.session.commit()

        # إنشاء موعد تلقائياً إذا كانت الحالة "متابعة" وتم تحديد تاريخ الموعد
        if form.status.data == "متابعة" and form.follow_up_date.data:
            appointment = Appointment(
                patient_id=patient.id,
                doctor_id=current_user.id,
                visit_id=visit.id,
                appointment_date=form.follow_up_date.data,
                notes=form.follow_up_notes.data or "موعد متابعة تلقائي",
                status="مجدول"
            )
            db.session.add(appointment)
            db.session.commit()
            
            flash(f"تم حفظ معلومات الزيارة وحجز موعد المتابعة بتاريخ {appointment.appointment_date.strftime('%Y-%m-%d %H:%M')}", "success")
        else:
            flash("تم حفظ معلومات الزيارة بنجاح", "success")
            
        return redirect(url_for("doctor.create_prescription", visit_id=visit.id))

    # الحصول على تاريخ الزيارات السابقة للمريض
    previous_visits = Visit.query.filter_by(patient_id=patient.id).order_by(Visit.date.desc()).all()

    return render_template(
        "doctor/patient_visit.html",
        title=f"زيارة المريض - {patient.full_name}",
        patient=patient,
        form=form,
        previous_visits=previous_visits
    )


@doctor.route("/doctor/medications", methods=["GET", "POST"])
@login_required
def medications():
    form = MedicationForm()
    if form.validate_on_submit():
        medication = Medication(name=form.name.data, dosage=form.dosage.data)
        db.session.add(medication)
        db.session.commit()
        flash('تم إضافة الدواء بنجاح!', 'success')
        return redirect(url_for('doctor.medications'))
    medications = Medication.query.all()
    return render_template('doctor/medications.html', title='إدارة الأدوية', form=form, medications=medications)


@doctor.route("/doctor/medication/<int:medication_id>/delete", methods=["POST"])
@login_required
def delete_medication(medication_id):
    medication = Medication.query.get_or_404(medication_id)
    db.session.delete(medication)
    db.session.commit()
    flash('تم حذف الدواء بنجاح!', 'success')
    return redirect(url_for('doctor.medications'))


@doctor.route("/doctor/predefined_prescriptions", methods=["GET", "POST"])
@login_required
def predefined_prescriptions():
    form = PredefinedPrescriptionForm()
    if form.validate_on_submit():
        predefined_prescription = PredefinedPrescription(name=form.name.data)
        db.session.add(predefined_prescription)
        db.session.commit()
        flash('تم إضافة الوصفة المحددة مسبقًا بنجاح!', 'success')
        return redirect(url_for('doctor.predefined_prescriptions'))
    predefined_prescriptions = PredefinedPrescription.query.all()
    return render_template('doctor/predefined_prescriptions.html', title='الوصفات المحددة مسبقًا', form=form, predefined_prescriptions=predefined_prescriptions)


@doctor.route("/doctor/predefined_prescription/<int:predefined_prescription_id>/delete", methods=["POST"])
@login_required
def delete_predefined_prescription(predefined_prescription_id):
    predefined_prescription = PredefinedPrescription.query.get_or_404(predefined_prescription_id)
    db.session.delete(predefined_prescription)
    db.session.commit()
    flash('تم حذف الوصفة المحددة مسبقًا بنجاح!', 'success')
    return redirect(url_for('doctor.predefined_prescriptions'))


@doctor.route("/doctor/predefined_prescription/<int:predefined_prescription_id>/add_medication", methods=["POST"])
@login_required
def add_medication_to_predefined(predefined_prescription_id):
    predefined_prescription = PredefinedPrescription.query.get_or_404(predefined_prescription_id)
    medication_id = request.form.get('medication_id')
    instructions = request.form.get('instructions')
    if medication_id:
        predefined_prescription_medication = PredefinedPrescriptionMedication(
            predefined_prescription_id=predefined_prescription.id,
            medication_id=medication_id,
            instructions=instructions
        )
        db.session.add(predefined_prescription_medication)
        db.session.commit()
        flash('تم إضافة الدواء إلى الوصفة المحددة مسبقًا بنجاح!', 'success')
    return redirect(url_for('doctor.predefined_prescriptions'))


@doctor.route("/doctor/predefined_prescription/<int:predefined_prescription_id>/remove_medication/<int:medication_id>", methods=["POST"])
@login_required
def remove_medication_from_predefined(predefined_prescription_id, medication_id):
    predefined_prescription_medication = PredefinedPrescriptionMedication.query.filter_by(
        predefined_prescription_id=predefined_prescription_id,
        medication_id=medication_id
    ).first_or_404()
    db.session.delete(predefined_prescription_medication)
    db.session.commit()
    flash('تم حذف الدواء من الوصفة المحددة مسبقًا بنجاح!', 'success')
    return redirect(url_for('doctor.predefined_prescriptions'))


@doctor.route("/doctor/prescription/<int:visit_id>", methods=["GET", "POST"])
@login_required
@doctor_required
def create_prescription(visit_id):
    """إنشاء وصفة طبية لزيارة"""
    visit = Visit.query.get_or_404(visit_id)

    # التأكد من أن الزيارة تنتمي إلى المريض الصحيح
    if visit.doctor_id != current_user.id:
        flash("غير مسموح لك بالوصول إلى هذه الزيارة", "danger")
        return redirect(url_for("doctor.dashboard"))

    form = PrescriptionForm()
    form.predefined_prescription.choices = [(0, 'اختر وصفة جاهزة')] + [(p.id, p.name) for p in PredefinedPrescription.query.all()]
    
    # Populate medication choices for each entry in the FieldList
    medication_choices = [(m.id, f"{m.name} ({m.dosage})") for m in Medication.query.all()]
    for entry in form.medications.entries:
        entry.form.medication_id.choices = medication_choices

    if request.method == 'POST':
        # التحقق من وجود أدوية في الطلب
        medications_data = []
        for key, value in request.form.items():
            if key.startswith('medications-') and key.endswith('-medication_id') and value:
                index = key.split('-')[1]
                instructions_key = f'medications-{index}-instructions'
                quantity_key = f'medications-{index}-quantity'
                instructions = request.form.get(instructions_key, '')
                quantity = request.form.get(quantity_key, '')
                if instructions:
                    medications_data.append({
                        'medication_id': int(value),
                        'instructions': instructions,
                        'quantity': quantity
                    })
        
        if not medications_data:
            flash("يجب إضافة دواء واحد على الأقل للوصفة", "danger")
        else:
            try:
                # إنشاء الوصفة
                prescription = Prescription(visit_id=visit.id)
                db.session.add(prescription)
                db.session.flush()  # للحصول على ID الوصفة
                
                # إضافة الأدوية
                for med_data in medications_data:
                    prescription_medication = PrescriptionMedication(
                        prescription_id=prescription.id,
                        medication_id=med_data['medication_id'],
                        instructions=med_data['instructions'],
                        quantity=med_data['quantity']
                    )
                    db.session.add(prescription_medication)
                
                db.session.commit()
                
                # تحديث حالة التذكرة
                ticket = Ticket.query.filter_by(patient_id=visit.patient_id, status="called").first()
                if ticket:
                    ticket.status = "done"
                    db.session.commit()
                
                # إنشاء ملف PDF للوصفة
                try:
                    pdf_path = generate_prescription_pdf(prescription, visit)
                    prescription.pdf_file = pdf_path
                    db.session.commit()
                except Exception as pdf_error:
                    print(f"خطأ في إنشاء PDF: {pdf_error}")
                
                flash("تم إنشاء الوصفة الطبية بنجاح!", "success")
                
                # إعادة توجيه لصفحة عرض الزيارة
                return redirect(url_for("doctor.view_visit", visit_id=visit.id))
                
            except Exception as e:
                db.session.rollback()
                flash(f"حدث خطأ في إنشاء الوصفة: {str(e)}", "danger")

    medications = Medication.query.all()
    return render_template("doctor/create_prescription.html", title="إنشاء وصفة طبية", form=form, visit=visit, medications=medications)


@doctor.route("/doctor/prescription/<int:prescription_id>/view")
@login_required
@doctor_required
def view_prescription(prescription_id):
    """عرض تفاصيل الوصفة الطبية"""
    prescription = Prescription.query.get_or_404(prescription_id)
    visit = prescription.visit
    
    # التأكد من أن الوصفة تنتمي للطبيب الحالي
    if visit.doctor_id != current_user.id:
        flash("غير مسموح لك بالوصول إلى هذه الوصفة", "danger")
        return redirect(url_for("doctor.dashboard"))
    
    return render_template("doctor/view_prescription.html", 
                         title="تفاصيل الوصفة الطبية",
                         prescription=prescription,
                         visit=visit)


@doctor.route("/doctor/prescription/<int:prescription_id>/print")
@login_required
@doctor_required
def print_prescription(prescription_id):
    """طباعة الوصفة الطبية"""
    prescription = Prescription.query.get_or_404(prescription_id)
    visit = prescription.visit
    
    # التأكد من أن الوصفة تنتمي للطبيب الحالي
    if visit.doctor_id != current_user.id:
        flash("غير مسموح لك بالوصول إلى هذه الوصفة", "danger")
        return redirect(url_for("doctor.dashboard"))
    
    try:
        # التحقق من وجود ملف PDF موجود مسبقاً
        if prescription.pdf_file:
            existing_path = os.path.join(current_app.root_path, prescription.pdf_file)
            if os.path.exists(existing_path):
                # استخدام الملف الموجود
                return send_file(existing_path, 
                               as_attachment=False, 
                               download_name=f"prescription_{prescription.id}.pdf",
                               mimetype='application/pdf')
        
        # إنشاء ملف PDF جديد فقط إذا لم يكن موجوداً
        pdf_path = generate_prescription_pdf(prescription, visit)
        
        # تحديث مسار الملف في قاعدة البيانات
        prescription.pdf_file = pdf_path
        db.session.commit()
        
        # إنشاء المسار الكامل للملف
        full_path = os.path.join(current_app.root_path, pdf_path)
        
        # التحقق من وجود الملف
        if os.path.exists(full_path):
            return send_file(full_path, 
                           as_attachment=False, 
                           download_name=f"prescription_{prescription.id}.pdf",
                           mimetype='application/pdf')
        else:
            flash("لم يتم العثور على ملف الوصفة", "danger")
            return redirect(url_for("doctor.view_visit", visit_id=visit.id))
        
    except Exception as e:
        flash(f"حدث خطأ في إنشاء الوصفة: {str(e)}", "danger")
        return redirect(url_for("doctor.view_visit", visit_id=visit.id))


@doctor.route("/doctor/prescription/<int:prescription_id>/view_pdf")
@login_required
@doctor_required
def view_prescription_pdf(prescription_id):
    """عرض الوصفة الطبية كـ PDF في المتصفح"""
    prescription = Prescription.query.get_or_404(prescription_id)
    visit = prescription.visit
    
    # التأكد من أن الوصفة تنتمي للطبيب الحالي
    if visit.doctor_id != current_user.id:
        flash("غير مسموح لك بالوصول إلى هذه الوصفة", "danger")
        return redirect(url_for("doctor.dashboard"))
    
    try:
        # التحقق من وجود ملف PDF موجود مسبقاً
        if prescription.pdf_file:
            existing_path = os.path.join(current_app.root_path, prescription.pdf_file)
            if os.path.exists(existing_path):
                # استخدام الملف الموجود
                return send_file(existing_path, mimetype='application/pdf')
        
        # إنشاء ملف PDF جديد فقط إذا لم يكن موجوداً
        pdf_path = generate_prescription_pdf(prescription, visit)
        prescription.pdf_file = pdf_path
        db.session.commit()
        
        full_path = os.path.join(current_app.root_path, pdf_path)
        
        if os.path.exists(full_path):
            return send_file(full_path, mimetype='application/pdf')
        else:
            flash("لم يتم العثور على ملف الوصفة", "danger")
            return redirect(url_for("doctor.view_visit", visit_id=visit.id))
            
    except Exception as e:
        flash(f"حدث خطأ في عرض الوصفة: {str(e)}", "danger")
        return redirect(url_for("doctor.view_visit", visit_id=visit.id))


@doctor.route("/doctor/prescription/<int:prescription_id>/regenerate_pdf")
@login_required
@doctor_required
def regenerate_prescription_pdf(prescription_id):
    """إعادة إنشاء PDF للوصفة الطبية"""
    prescription = Prescription.query.get_or_404(prescription_id)
    visit = prescription.visit
    
    # التأكد من أن الوصفة تنتمي للطبيب الحالي
    if visit.doctor_id != current_user.id:
        flash("غير مسموح لك بالوصول إلى هذه الوصفة", "danger")
        return redirect(url_for("doctor.dashboard"))
    
    try:
        # حذف الملف القديم إذا كان موجوداً
        if prescription.pdf_file:
            old_path = os.path.join(current_app.root_path, prescription.pdf_file)
            if os.path.exists(old_path):
                os.remove(old_path)
        
        # إنشاء ملف PDF جديد
        pdf_path = generate_prescription_pdf(prescription, visit)
        prescription.pdf_file = pdf_path
        db.session.commit()
        
        flash("تم إعادة إنشاء الوصفة بنجاح!", "success")
        return redirect(url_for("doctor.view_prescription", prescription_id=prescription.id))
        
    except Exception as e:
        flash(f"حدث خطأ في إعادة إنشاء الوصفة: {str(e)}", "danger")
        return redirect(url_for("doctor.view_visit", visit_id=visit.id))


@doctor.route("/doctor/get_predefined_prescription_meds/<int:predefined_id>")
@login_required
def get_predefined_prescription_meds(predefined_id):
    predefined_prescription = PredefinedPrescription.query.get_or_404(predefined_id)
    meds_data = []
    for ppm in predefined_prescription.medications:
        meds_data.append({
            'id': ppm.medication.id,
            'name': ppm.medication.name,
            'dosage': ppm.medication.dosage,
            'instructions': ppm.instructions
        })
    return jsonify(meds_data)


@doctor.route("/doctor/visit-history")
@login_required
@doctor_required
def visit_history():
    """عرض تاريخ الزيارات"""
    # الحصول على جميع الزيارات التي قام بها الطبيب
    visits = Visit.query.filter_by(doctor_id=current_user.id).order_by(Visit.date.desc()).all()

    return render_template(
        "doctor/visit_history.html",
        title="سجل الزيارات",
        visits=visits
    )


@doctor.route("/doctor/view-visit/<int:visit_id>")
@login_required
@doctor_required
def view_visit(visit_id):
    """عرض تفاصيل زيارة معينة"""
    visit = Visit.query.get_or_404(visit_id)
    if visit.doctor != current_user:
        abort(403)
    return render_template("doctor/view_visit.html", title="تفاصيل الزيارة", visit=visit)


@doctor.route("/doctor/edit-visit/<int:visit_id>", methods=["GET", "POST"])
@login_required
@doctor_required
def edit_visit(visit_id):
    """تعديل زيارة موجودة"""
    visit = Visit.query.get_or_404(visit_id)
    if visit.doctor != current_user:
        abort(403)
    form = VisitForm()
    if form.validate_on_submit():
        visit.symptoms = form.symptoms.data
        visit.diagnosis = form.diagnosis.data
        visit.treatment = form.treatment.data
        visit.notes = form.notes.data
        visit.status = form.status.data
        visit.price = form.price.data
        visit.payment_status = form.payment_status.data
        db.session.commit()
        flash("تم تحديث معلومات الزيارة بنجاح", "success")
        return redirect(url_for("doctor.view_visit", visit_id=visit.id))
    elif request.method == "GET":
        form.symptoms.data = visit.symptoms
        form.diagnosis.data = visit.diagnosis
        form.treatment.data = visit.treatment
        form.notes.data = visit.notes
        form.status.data = visit.status
        form.price.data = visit.price
        form.payment_status.data = visit.payment_status
    return render_template("doctor/edit_visit.html", title="تعديل الزيارة", form=form, visit=visit)


@doctor.route("/doctor/delete-visit/<int:visit_id>", methods=["POST"])
@login_required
@doctor_required
def delete_visit(visit_id):
    """حذف زيارة"""
    visit = Visit.query.get_or_404(visit_id)
    if visit.doctor != current_user:
        abort(403)
    db.session.delete(visit)
    db.session.commit()
    flash("تم حذف الزيارة بنجاح", "success")
    return redirect(url_for("doctor.visit_history"))


@doctor.route("/doctor/settings", methods=["GET", "POST"])
@login_required
@doctor_required
def doctor_settings():
    settings = DoctorSettings.query.filter_by(user_id=current_user.id).first()
    if not settings:
        settings = DoctorSettings(user_id=current_user.id)
        db.session.add(settings)
        db.session.commit()

    form = DoctorSettingsForm(obj=settings)

    if form.validate_on_submit():
        form.populate_obj(settings)
        db.session.commit()
        flash('تم حفظ الإعدادات بنجاح!', 'success')
        return redirect(url_for('doctor.doctor_settings'))

    return render_template('doctor/settings.html', title='إعدادات الطبيب', form=form, settings=settings)





from datetime import timedelta


@doctor.route("/doctor/payments")
@login_required
@doctor_required
def payments_list():
    """عرض قائمة المدفوعات مع إمكانية التصفية"""
    # الحصول على معايير التصفية من الطلب
    selected_month = request.args.get('month', type=int)
    selected_year = request.args.get('year', type=int)
    selected_status = request.args.get('status')
    
    # بناء الاستعلام الأساسي للزيارات التي قام بها الطبيب
    query = Visit.query.filter_by(doctor_id=current_user.id)
    
    # تطبيق التصفية حسب الشهر والسنة
    if selected_month and selected_year:
        query = query.filter(
            db.extract('month', Visit.date) == selected_month,
            db.extract('year', Visit.date) == selected_year
        )
    elif selected_year:
        query = query.filter(db.extract('year', Visit.date) == selected_year)
    elif selected_month:
        query = query.filter(db.extract('month', Visit.date) == selected_month)
    
    # تطبيق التصفية حسب حالة الدفع
    if selected_status:
        query = query.filter_by(payment_status=selected_status)
    
    # ترتيب النتائج حسب التاريخ (الأحدث أولاً)
    payments = query.order_by(Visit.date.desc()).all()
    
    # حساب الإحصائيات
    all_visits = Visit.query.filter_by(doctor_id=current_user.id).all()
    
    # المدفوعات المكتملة
    paid_visits = [v for v in all_visits if v.payment_status == "مدفوع"]
    paid_count = len(paid_visits)
    paid_amount = sum(v.price or 0 for v in paid_visits)
    
    # المدفوعات الجزئية
    partial_paid_visits = [v for v in all_visits if v.payment_status == "مدفوع جزئياً"]
    partial_paid_count = len(partial_paid_visits)
    partial_paid_amount = sum(v.price or 0 for v in partial_paid_visits)
    
    # المدفوعات المستحقة
    unpaid_visits = [v for v in all_visits if v.payment_status == "غير مدفوع"]
    unpaid_count = len(unpaid_visits)
    unpaid_amount = sum(v.price or 0 for v in unpaid_visits)
    
    # إجمالي المدفوعات
    total_paid = paid_amount + partial_paid_amount
    
    return render_template(
        "doctor/payments.html",
        title="المحاسبة",
        payments=payments,
        selected_month=selected_month,
        selected_year=selected_year,
        selected_status=selected_status,
        current_year=datetime.now().year,
        total_paid=total_paid,
        paid_count=paid_count,
        paid_amount=paid_amount,
        partial_paid_count=partial_paid_count,
        partial_paid_amount=partial_paid_amount,
        unpaid_count=unpaid_count,
        unpaid_amount=unpaid_amount
    )


@doctor.route("/doctor/patient-details/<int:patient_id>")
@login_required
@doctor_required
def patient_details(patient_id):
    """عرض تفاصيل المريض وتاريخ زياراته"""
    patient = Patient.query.get_or_404(patient_id)
    
    # الحصول على جميع زيارات المريض مع هذا الطبيب
    visits = Visit.query.filter_by(
        patient_id=patient.id,
        doctor_id=current_user.id
    ).order_by(Visit.date.desc()).all()
    
    return render_template(
        "doctor/patient_details.html",
        title=f"تفاصيل المريض - {patient.full_name}",
        patient=patient,
        visits=visits
    )


@doctor.route("/doctor/patients")
@login_required
@doctor_required
def list_patients():
    """قائمة المرضى المسجلين"""
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "")

    if search:
        # البحث عن المرضى بالاسم أو رقم الهاتف
        patients = Patient.query.filter(Patient.full_name.ilike(f"%{search}%") | Patient.phone.ilike(f"%{search}%")).paginate(page=page, per_page=10)
    else:
        # عرض جميع المرضى مرتبين حسب تاريخ التسجيل (الأحدث أولاً)
        patients = Patient.query.order_by(Patient.created_at.desc()).paginate(page=page, per_page=10)

    return render_template("doctor/patients.html", title="قائمة المرضى", patients=patients, search=search)


@doctor.route("/doctor/api/calendar-visits")
@login_required
@doctor_required
def calendar_daily_visits():
    """الحصول على زيارات يوم معين للتقويم"""
    date_str = request.args.get('date')
    if not date_str:
        return jsonify([])
    
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # الحصول على زيارات اليوم
        visits = Visit.query.filter(
            Visit.doctor_id == current_user.id,
            db.func.date(Visit.date) == date
        ).order_by(Visit.date).all()
        
        visits_data = []
        for visit in visits:
            visits_data.append({
                'patient_name': visit.patient.full_name,
                'time': visit.date.strftime('%H:%M'),
                'status': visit.status or 'مكتملة',
                'url': url_for('doctor.view_visit', visit_id=visit.id)
            })
        
        return jsonify(visits_data)
    except ValueError:
        return jsonify([])


@doctor.route("/doctor/calendar")
@login_required
@doctor_required
def doctor_calendar():
    """عرض التقويم مع الزيارات"""
    # الحصول على الشهر والسنة من المعاملات
    year = request.args.get('year', type=int) or datetime.now().year
    month = request.args.get('month', type=int) or datetime.now().month
    
    # التأكد من صحة القيم
    if month < 1:
        month = 12
        year -= 1
    elif month > 12:
        month = 1
        year += 1
    
    # حساب الشهر السابق والتالي
    prev_month = month - 1 if month > 1 else 12
    prev_month_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_month_year = year if month < 12 else year + 1
    
    # إنشاء بيانات التقويم
    import calendar
    cal = calendar.monthcalendar(year, month)
    
    # الحصول على زيارات الشهر
    start_date = datetime(year, month, 1).date()
    if month == 12:
        end_date = datetime(year + 1, 1, 1).date()
    else:
        end_date = datetime(year, month + 1, 1).date()
    
    visits = Visit.query.filter(
        Visit.doctor_id == current_user.id,
        Visit.date >= start_date,
        Visit.date < end_date
    ).all()
    
    # تجميع الزيارات حسب التاريخ
    visits_by_date = {}
    for visit in visits:
        date_key = visit.date.date()
        if date_key not in visits_by_date:
            visits_by_date[date_key] = []
        visits_by_date[date_key].append(visit)
    
    # إنشاء بيانات التقويم مع الزيارات
    calendar_data = []
    for week in cal:
        week_data = []
        for day in week:
            if day == 0:
                # يوم من الشهر السابق أو التالي
                if len(week_data) < 4:  # بداية الشهر
                    prev_month_days = calendar.monthrange(prev_month_year, prev_month)[1]
                    actual_day = prev_month_days - (6 - len(week_data))
                    # التأكد من أن اليوم ضمن النطاق الصحيح للشهر
                    actual_day = max(1, min(actual_day, prev_month_days))
                    date_obj = datetime(prev_month_year, prev_month, actual_day).date()
                else:  # نهاية الشهر
                    actual_day = len(week_data) - 6
                    # التأكد من أن اليوم ضمن النطاق الصحيح للشهر
                    next_month_days = calendar.monthrange(next_month_year, next_month)[1]
                    actual_day = max(1, min(actual_day, next_month_days))
                    date_obj = datetime(next_month_year, next_month, actual_day).date()
            else:
                date_obj = datetime(year, month, day).date()
            
            day_visits = visits_by_date.get(date_obj, [])
            week_data.append({
                'date': date_obj,
                'visits': day_visits
            })
        calendar_data.append(week_data)
    
    # حساب إحصائيات الشهر
    total_visits = len(visits)
    unique_patients = len(set(visit.patient_id for visit in visits))
    avg_daily_visits = round(total_visits / 30, 1) if total_visits > 0 else 0
    
    return render_template(
        "doctor/calendar.html",
        title="التقويم",
        calendar_data=calendar_data,
        current_month=month,
        current_year=year,
        prev_month_month=prev_month,
        prev_month_year=prev_month_year,
        next_month_month=next_month,
        next_month_year=next_month_year,
        today=datetime.now().date(),
        total_visits=total_visits,
        unique_patients=unique_patients,
        avg_daily_visits=avg_daily_visits
    )


# ==================== طرق المواعيد ====================

@doctor.route("/appointments")
@login_required
@doctor_required
def appointments():
    """عرض قائمة المواعيد"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    
    # بناء الاستعلام
    query = Appointment.query.filter_by(doctor_id=current_user.id)
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    # ترتيب حسب تاريخ الموعد
    appointments = query.order_by(Appointment.appointment_date.asc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    return render_template('doctor/appointments.html', 
                         appointments=appointments, 
                         status_filter=status_filter)


@doctor.route("/create_appointment/<int:visit_id>", methods=['GET', 'POST'])
@login_required
@doctor_required
def create_appointment(visit_id):
    """إنشاء موعد جديد من زيارة معلقة"""
    visit = Visit.query.get_or_404(visit_id)
    
    # التأكد أن الزيارة للطبيب الحالي وأن حالتها معلقة
    if visit.doctor_id != current_user.id:
        abort(403)
    
    if visit.status != "معلقة":
        flash("يمكن إنشاء موعد فقط للزيارات المعلقة", "warning")
        return redirect(url_for('doctor.view_visit', visit_id=visit_id))
    
    form = AppointmentForm()
    
    if form.validate_on_submit():
        # التحقق من عدم وجود موعد مسبق لنفس الزيارة
        existing_appointment = Appointment.query.filter_by(visit_id=visit_id).first()
        if existing_appointment:
            flash("يوجد موعد مسبق لهذه الزيارة", "warning")
            return redirect(url_for('doctor.view_visit', visit_id=visit_id))
        
        # إنشاء الموعد الجديد
        appointment = Appointment(
            patient_id=visit.patient_id,
            doctor_id=current_user.id,
            visit_id=visit_id,
            appointment_date=form.appointment_date.data,
            notes=form.notes.data,
            status="مجدول"
        )
        
        db.session.add(appointment)
        db.session.commit()
        
        flash(f"تم حجز موعد للمريض {visit.patient.full_name} بتاريخ {appointment.appointment_date.strftime('%Y-%m-%d %H:%M')}", "success")
        return redirect(url_for('doctor.appointments'))
    
    return render_template('doctor/create_appointment.html', 
                         form=form, 
                         visit=visit)


@doctor.route("/appointment/<int:appointment_id>")
@login_required
@doctor_required
def view_appointment(appointment_id):
    """عرض تفاصيل موعد"""
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # التأكد أن الموعد للطبيب الحالي
    if appointment.doctor_id != current_user.id:
        abort(403)
    
    return render_template('doctor/view_appointment.html', appointment=appointment)


@doctor.route("/appointment/<int:appointment_id>/update_status", methods=['POST'])
@login_required
@doctor_required
def update_appointment_status(appointment_id):
    """تحديث حالة الموعد"""
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # التأكد أن الموعد للطبيب الحالي
    if appointment.doctor_id != current_user.id:
        abort(403)
    
    new_status = request.form.get('status')
    valid_statuses = ['مجدول', 'مكتمل', 'ملغي', 'فائت']
    
    if new_status in valid_statuses:
        appointment.status = new_status
        appointment.updated_at = datetime.utcnow()
        db.session.commit()
        
        flash(f"تم تحديث حالة الموعد إلى: {new_status}", "success")
    else:
        flash("حالة غير صحيحة", "error")
    
    return redirect(url_for('doctor.view_appointment', appointment_id=appointment_id))


@doctor.route("/appointment/<int:appointment_id>/delete", methods=['POST'])
@login_required
@doctor_required
def delete_appointment(appointment_id):
    """حذف موعد"""
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # التأكد أن الموعد للطبيب الحالي
    if appointment.doctor_id != current_user.id:
        abort(403)
    
    # لا يمكن حذف المواعيد المكتملة
    if appointment.status == "مكتمل":
        flash("لا يمكن حذف موعد مكتمل", "error")
        return redirect(url_for('doctor.view_appointment', appointment_id=appointment_id))
    
    patient_name = appointment.patient.full_name
    db.session.delete(appointment)
    db.session.commit()
    
    flash(f"تم حذف موعد المريض {patient_name}", "success")
    return redirect(url_for('doctor.appointments'))


# ==================== إدارة قائمة الانتظار للطبيب ====================

@doctor.route("/call_next_patient", methods=['POST'])
@login_required
@doctor_required
def call_next_patient():
    """استدعاء المريض التالي مع إعطاء الأولوية للمواعيد"""
    try:
        today = datetime.now().date()
        
        # إنهاء التذكرة المستدعاة حالياً إذا كانت موجودة
        current_ticket = Ticket.query.filter(
            db.func.date(Ticket.created_at) == today,
            Ticket.status == "called"
        ).first()
        
        if current_ticket:
            current_ticket.status = "examined"
            db.session.commit()
        
        # البحث عن التذكرة التالية مع إعطاء الأولوية للمواعيد
        # أولاً: البحث عن تذاكر الأولوية (المواعيد)
        next_ticket = Ticket.query.filter(
            db.func.date(Ticket.created_at) == today,
            Ticket.status == "waiting"
        ).order_by(
            Ticket.priority.desc(),  # الأولوية أولاً (1 = أولوية، 0 = عادي)
            Ticket.number.asc()      # ثم الرقم تصاعدياً
        ).first()
        
        if next_ticket:
            # تحديث حالة التذكرة إلى مستدعاة
            next_ticket.status = "called"
            db.session.commit()
            
            # رسالة مختلفة حسب نوع التذكرة
            if next_ticket.priority == 1:
                flash(f"تم استدعاء التذكرة ذات الأولوية رقم {next_ticket.display_number} - {next_ticket.patient.full_name} (لديه موعد)", "success")
            else:
                flash(f"تم استدعاء التذكرة رقم {next_ticket.display_number} - {next_ticket.patient.full_name}", "success")
        else:
            flash("لا توجد تذاكر في قائمة الانتظار", "info")
            
    except Exception as e:
        db.session.rollback()
        flash(f"حدث خطأ أثناء استدعاء المريض: {str(e)}", "error")
    
    return redirect(url_for('doctor.dashboard'))


@doctor.route("/waiting_queue_status")
@login_required
@doctor_required
def waiting_queue_status():
    """عرض حالة قائمة الانتظار للطبيب"""
    today = datetime.now().date()
    
    # الحصول على التذاكر المنتظرة مرتبة حسب الأولوية
    waiting_tickets = Ticket.query.filter(
        db.func.date(Ticket.created_at) == today,
        Ticket.status == "waiting"
    ).order_by(
        Ticket.priority.desc(),  # الأولوية أولاً
        Ticket.number.asc()      # ثم الرقم
    ).all()
    
    # الحصول على التذكرة المستدعاة حالياً
    called_ticket = Ticket.query.filter(
        db.func.date(Ticket.created_at) == today,
        Ticket.status == "called"
    ).first()
    
    # تصنيف التذاكر
    priority_tickets = [t for t in waiting_tickets if t.priority == 1]
    regular_tickets = [t for t in waiting_tickets if t.priority == 0]
    
    return render_template('doctor/waiting_queue_status.html',
                         waiting_tickets=waiting_tickets,
                         called_ticket=called_ticket,
                         priority_tickets=priority_tickets,
                         regular_tickets=regular_tickets)
