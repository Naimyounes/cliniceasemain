from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from clinic_app import db
from clinic_app.models import Patient, Ticket, Visit, User, Appointment
from clinic_app.secretary.forms import PatientForm, SecretaryAppointmentForm, PaymentUpdateForm
from datetime import datetime, timedelta
from functools import wraps

# إنشاء بلوبرينت للسكرتير
secretary = Blueprint("secretary", __name__)


def secretary_required(f):
    """تأكد أن المستخدم هو سكرتير"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role != "secretary":
            flash("غير مسموح لك بالوصول إلى هذه الصفحة", "danger")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function


def get_notification_data():
    """الحصول على بيانات الإشعارات للسكرتيرة"""
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


@secretary.route("/dashboard/secretary")
@login_required
@secretary_required
def dashboard():
    """لوحة تحكم السكرتير"""
    today = datetime.now().date()
    
    # الحصول على قائمة المرضى المسجلين اليوم
    recent_patients = Patient.query.filter(
        db.func.date(Patient.created_at) == today
    ).order_by(Patient.created_at.desc()).all()

    # الحصول على قائمة الانتظار الحالية مرتبة حسب الأولوية
    waiting_tickets = Ticket.query.filter(
        db.func.date(Ticket.created_at) == today,
        Ticket.status.in_(["waiting", "called"])
    ).order_by(
        Ticket.priority.desc(),
        Ticket.number.asc()
    ).all()

    # الحصول على المريض الحالي - الذي لديه تذكرة بحالة called
    current_ticket = Ticket.query.filter(
        db.func.date(Ticket.created_at) == today,
        Ticket.status == "called"
    ).first()
    
    # الحصول على المدفوعات المستحقة (الزيارات غير المدفوعة)
    pending_payments = Visit.query.filter_by(payment_status="غير مدفوع").order_by(Visit.date.desc()).all()
    
    # حساب إجمالي المبالغ المستحقة
    total_pending_amount = sum(visit.price or 0 for visit in pending_payments)
    
    # الحصول على آخر زيارة مكتملة اليوم غير مدفوعة
    last_unpaid_visit = Visit.query.filter(
        db.func.date(Visit.date) == today,
        Visit.payment_status == "غير مدفوع"
    ).order_by(Visit.date.desc()).first()
    

    
    # حساب الإحصائيات اليومية
    patients_today = len(recent_patients)
    visits_today = Visit.query.filter(db.func.date(Visit.date) == today).count()
    
    daily_stats = {
        'patients_today': patients_today,
        'visits_today': visits_today
    }

    # إضافة إحصائيات إضافية
    daily_stats['total_patients'] = Patient.query.count()
    
    return render_template(
        "secretary/dashboard_improved.html",
        title="لوحة تحكم السكرتير",
        recent_patients=recent_patients,
        waiting_tickets=waiting_tickets,
        current_ticket=current_ticket,
        pending_payments=pending_payments,
        total_pending_amount=total_pending_amount,
        daily_stats=daily_stats,
        last_unpaid_visit=last_unpaid_visit
    )


@secretary.route("/secretary/api/update-payment/<int:visit_id>", methods=["POST"])
@login_required
@secretary_required
def update_payment_api(visit_id):
    """تحديث حالة الدفع للزيارة (API)"""
    try:
        visit = Visit.query.get_or_404(visit_id)
        payment_status = request.form.get("payment_status", "مدفوع")
        
        # تحديث حالة الدفع
        visit.payment_status = payment_status
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "تم تحديث حالة الدفع بنجاح",
            "payment_status": payment_status
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": f"حدث خطأ: {str(e)}"
        }), 500


@secretary.route("/secretary/update-payment/<int:visit_id>", methods=["POST"])
@login_required
@secretary_required
def update_payment_form(visit_id):
    """تحديث حالة الدفع للزيارة (نموذج)"""
    visit = Visit.query.get_or_404(visit_id)
    
    # تحديث حالة الدفع إلى مدفوع
    visit.payment_status = "مدفوع"
    db.session.commit()
    
    flash(f"تم تحديث حالة الدفع للمريض {visit.patient.full_name} بنجاح", "success")
    return redirect(url_for("secretary.dashboard"))


@secretary.route("/secretary/patient/new", methods=["GET", "POST"])
@login_required
@secretary_required
def new_patient():
    """تسجيل مريض جديد"""
    form = PatientForm()

    if form.validate_on_submit():
        patient = Patient(
            full_name=form.full_name.data,
            phone=form.phone.data,
            birth_date=form.birth_date.data,
            gender=form.gender.data if form.gender.data else None,
            blood_group=form.blood_group.data if form.blood_group.data else None,
            address=form.address.data if form.address.data else None
        )

        db.session.add(patient)
        db.session.commit()

        flash(f"تم تسجيل المريض {patient.full_name} بنجاح!", "success")
        return redirect(url_for("secretary.create_waiting_ticket", patient_id=patient.id))

    return render_template("secretary/patient_form.html", title="إضافة مريض جديد", form=form, legend="تسجيل مريض جديد")


@secretary.route("/secretary/patient/<int:patient_id>/edit", methods=["GET", "POST"])
@login_required
@secretary_required
def edit_patient(patient_id):
    """تعديل بيانات مريض"""
    patient = Patient.query.get_or_404(patient_id)
    form = PatientForm()

    if form.validate_on_submit():
        patient.full_name = form.full_name.data
        patient.phone = form.phone.data
        patient.birth_date = form.birth_date.data
        patient.gender = form.gender.data if form.gender.data else None
        patient.blood_group = form.blood_group.data if form.blood_group.data else None
        patient.address = form.address.data if form.address.data else None

        db.session.commit()
        flash(f"تم تحديث بيانات المريض {patient.full_name} بنجاح!", "success")
        return redirect(url_for("secretary.dashboard"))

    elif request.method == "GET":
        form.full_name.data = patient.full_name
        form.phone.data = patient.phone
        form.birth_date.data = patient.birth_date
        form.gender.data = patient.gender

    return render_template("secretary/patient_form.html", title="تعديل بيانات مريض", form=form, legend="تعديل بيانات مريض")


@secretary.route("/secretary/patients")
@login_required
@secretary_required
def list_patients():
    """قائمة المرضى المسجلين"""
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "")
    is_ajax = request.args.get("ajax", "0") == "1"

    if search:
        patients = Patient.query.filter(Patient.full_name.ilike(f"%{search}%") | Patient.phone.ilike(f"%{search}%")).paginate(page=page, per_page=10)
    else:
        patients = Patient.query.order_by(Patient.created_at.desc()).paginate(page=page, per_page=10)

    # إرجاع طريقة عرض مختلفة للطلبات العادية وطلبات AJAX
    if is_ajax:
        # طلب AJAX، نرجع الجدول فقط
        return render_template("secretary/patients.html", title="قائمة المرضى", patients=patients, search=search, is_ajax=True)
    else:
        # طلب عادي، نرجع الصفحة كاملة
        return render_template("secretary/patients.html", title="قائمة المرضى", patients=patients, search=search, is_ajax=False)


@secretary.route("/secretary/patient/<int:patient_id>")
@login_required
@secretary_required
def patient_details(patient_id):
    """تفاصيل مريض محدد"""
    patient = Patient.query.get_or_404(patient_id)
    now = datetime.now()
    return render_template("secretary/patient_details.html", title=f"تفاصيل المريض - {patient.full_name}", patient=patient, now=now)


@secretary.route("/secretary/create-ticket")
@login_required
@secretary_required
def create_ticket_page():
    """صفحة إنشاء تذكرة جديدة"""
    today = datetime.now().date()
    
    # إحصائيات سريعة
    total_patients = Patient.query.count()
    waiting_count = Ticket.query.filter(
        db.func.date(Ticket.created_at) == today,
        Ticket.status.in_(["waiting", "called"])
    ).count()
    
    # رقم التذكرة التالي
    last_ticket = Ticket.query.filter(Ticket.created_at >= today).order_by(Ticket.number.desc()).first()
    next_ticket_number = 1 if not last_ticket else last_ticket.number + 1
    
    # تذاكر اليوم
    today_tickets = Ticket.query.filter(db.func.date(Ticket.created_at) == today).count()
    
    return render_template(
        "secretary/create_ticket.html",
        title="إنشاء تذكرة انتظار",
        total_patients=total_patients,
        waiting_count=waiting_count,
        next_ticket_number=next_ticket_number,
        today_tickets=today_tickets
    )


@secretary.route("/secretary/ticket/create/<int:patient_id>")
@login_required
@secretary_required
def create_ticket(patient_id):
    """إنشاء تذكرة جديدة للمريض"""
    patient = Patient.query.get_or_404(patient_id)

    # التحقق من وجود تذكرة نشطة للمريض
    today = datetime.now().date()
    existing_ticket = Ticket.query.filter(
        Ticket.patient_id == patient_id,
        Ticket.created_at >= today,
        Ticket.status.in_(["waiting", "called"])
    ).first()

    if existing_ticket:
        flash(f"المريض {patient.full_name} لديه بالفعل تذكرة نشطة برقم {existing_ticket.number}", "info")
        return redirect(url_for("secretary.dashboard"))

    # الحصول على آخر رقم تذكرة لهذا اليوم
    last_ticket = Ticket.query.filter(Ticket.created_at >= today).order_by(Ticket.number.desc()).first()
    next_number = 1 if not last_ticket else last_ticket.number + 1

    # التحقق من وجود موعد للمريض اليوم
    appointment = Appointment.query.filter(
        Appointment.patient_id == patient_id,
        db.func.date(Appointment.appointment_date) == today,
        Appointment.status == "مجدول"
    ).first()
    
    # تحديد نوع التذكرة والأولوية
    if appointment:
        ticket_type = "reservation"
        priority = 1
    else:
        ticket_type = "walk_in"
        priority = 0
    
    # إنشاء تذكرة جديدة
    ticket = Ticket(
        patient_id=patient.id,
        number=next_number,
        status="waiting",
        ticket_type=ticket_type,
        priority=priority,
        appointment_id=appointment.id if appointment else None
    )

    db.session.add(ticket)
    db.session.commit()

    flash(f"تم إنشاء تذكرة برقم {next_number} للمريض {patient.full_name}", "success")
    return redirect(url_for("secretary.dashboard"))


@secretary.route("/secretary/ticket/search", methods=["POST"])
@login_required
@secretary_required
def search_patient_for_ticket():
    """البحث عن مريض لإنشاء تذكرة"""
    search_data = request.form.get("search")

    if not search_data:
        flash("يرجى تحديد المريض أولاً", "warning")
        return redirect(url_for("secretary.dashboard"))

    # محاولة معالجة البيانات كمعرف مريض إذا كان رقماً
    if search_data.isdigit():
        patient = Patient.query.get(int(search_data))
        if patient:
            # تم العثور على المريض، إعادة التوجيه لإنشاء تذكرة
            return redirect(url_for("secretary.create_ticket", patient_id=patient.id))

    # إذا وصلنا هنا فإما أن البيانات ليست رقماً، أو لم يتم العثور على المريض بهذا المعرف
    search_term = search_data

    patients = Patient.query.filter(
        Patient.full_name.ilike(f"%{search_term}%") | 
        Patient.phone.ilike(f"%{search_term}%")
    ).all()

    if not patients:
        flash("لا يوجد مرضى مطابقين للبحث. يرجى تسجيل المريض أولاً.", "info")
        return redirect(url_for("secretary.new_patient"))

    if len(patients) == 1:
        return redirect(url_for("secretary.create_ticket", patient_id=patients[0].id))

    return render_template("secretary/search_results.html", title="نتائج البحث", patients=patients, search=search_term)


@secretary.route("/secretary/waiting-list")
@login_required
@secretary_required
def waiting_list():
    """عرض قائمة الانتظار الكاملة"""
    today = datetime.now().date()
    tickets = Ticket.query.filter(
        Ticket.created_at >= today
    ).order_by(Ticket.status.desc(), Ticket.number).all()

    return render_template("secretary/waiting_list.html", title="قائمة الانتظار", tickets=tickets)


@secretary.route("/secretary/api/waiting-list")
@login_required
@secretary_required
def api_waiting_list():
    """واجهة برمجية لقائمة الانتظار للتحديث التلقائي"""
    today = datetime.now().date()
    tickets = Ticket.query.filter(
        Ticket.created_at >= today,
        Ticket.status.in_(["waiting", "called"])
    ).order_by(Ticket.number).all()

    # التهيئة للتنسيق JSON
    tickets_data = []
    for ticket in tickets:
        tickets_data.append({
            "id": ticket.id,
            "number": ticket.number,
            "status": ticket.status,
            "patient_name": ticket.patient.full_name
        })

    # الحصول على المريض الحالي
    current_ticket = Ticket.query.filter_by(status="called").first()
    current_data = None

    if current_ticket:
        current_data = {
            "id": current_ticket.id,
            "number": current_ticket.number,
            "patient_name": current_ticket.patient.full_name
        }

    return jsonify({
        "waiting": tickets_data,
        "current": current_data
    })


@secretary.route("/secretary/api/search-patients")
@login_required
@secretary_required
def api_search_patients():
    """واجهة برمجية للبحث عن المرضى"""
    search_term = request.args.get("term", "")

    if not search_term or len(search_term) < 2:
        return jsonify([])

    # البحث عن المرضى
    patients = Patient.query.filter(
        Patient.full_name.ilike(f"%{search_term}%") | 
        Patient.phone.ilike(f"%{search_term}%")
    ).limit(10).all()

    # تهيئة البيانات
    patients_data = []
    for patient in patients:
        patients_data.append({
            "id": patient.id,
            "full_name": patient.full_name,
            "phone": patient.phone,
            "view_url": url_for('secretary.patient_details', patient_id=patient.id)
        })

    return jsonify(patients_data)


# ==================== إدارة المواعيد ====================

@secretary.route("/appointments")
@login_required
@secretary_required
def appointments():
    """عرض قائمة المواعيد"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    doctor_filter = request.args.get('doctor', 'all')
    
    # بناء الاستعلام
    query = Appointment.query
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    if doctor_filter != 'all':
        query = query.filter_by(doctor_id=doctor_filter)
    
    # ترتيب حسب تاريخ الموعد
    appointments = query.order_by(Appointment.appointment_date.asc()).paginate(
        page=page, per_page=15, error_out=False
    )
    
    # الحصول على قائمة الأطباء للفلتر
    doctors = User.query.filter_by(role='doctor').all()
    
    return render_template('secretary/appointments.html', 
                         appointments=appointments, 
                         status_filter=status_filter,
                         doctor_filter=doctor_filter,
                         doctors=doctors)


@secretary.route("/create_appointment", methods=['GET', 'POST'])
@login_required
@secretary_required
def create_appointment():
    """إنشاء موعد جديد"""
    form = SecretaryAppointmentForm()
    
    # تحديد خيارات المرضى والأطباء
    form.patient_id.choices = [(0, 'اختر المريض')] + [(p.id, p.full_name) for p in Patient.query.all()]
    form.doctor_id.choices = [(0, 'اختر الطبيب')] + [(d.id, d.username) for d in User.query.filter_by(role='doctor').all()]
    
    if form.validate_on_submit():
        appointment = Appointment(
            patient_id=form.patient_id.data,
            doctor_id=form.doctor_id.data,
            appointment_date=form.appointment_date.data,
            notes=form.notes.data,
            status="مجدول"
        )
        
        db.session.add(appointment)
        db.session.commit()
        
        patient = Patient.query.get(form.patient_id.data)
        doctor = User.query.get(form.doctor_id.data)
        
        flash(f"تم حجز موعد للمريض {patient.full_name} مع د. {doctor.username} بتاريخ {appointment.appointment_date.strftime('%Y-%m-%d %H:%M')}", "success")
        return redirect(url_for('secretary.appointments'))
    
    return render_template('secretary/create_appointment.html', form=form)


@secretary.route("/appointment/<int:appointment_id>")
@login_required
@secretary_required
def view_appointment(appointment_id):
    """عرض تفاصيل موعد"""
    appointment = Appointment.query.get_or_404(appointment_id)
    return render_template('secretary/view_appointment.html', appointment=appointment)


@secretary.route("/appointment/<int:appointment_id>/delete", methods=['POST'])
@login_required
@secretary_required
def delete_appointment(appointment_id):
    """حذف موعد"""
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # لا يمكن حذف المواعيد المكتملة
    if appointment.status == "مكتمل":
        flash("لا يمكن حذف موعد مكتمل", "error")
        return redirect(url_for('secretary.view_appointment', appointment_id=appointment_id))
    
    patient_name = appointment.patient.full_name
    doctor_name = appointment.doctor.username
    db.session.delete(appointment)
    db.session.commit()
    
    flash(f"تم حذف موعد المريض {patient_name} مع د. {doctor_name}", "success")
    return redirect(url_for('secretary.appointments'))


# ==================== إدارة قائمة الانتظار ====================







@secretary.route("/ticket/<int:ticket_id>/delete", methods=['POST'])
@login_required
@secretary_required
def delete_ticket(ticket_id):
    """حذف تذكرة من قائمة الانتظار"""
    ticket = Ticket.query.get_or_404(ticket_id)
    
    # لا يمكن حذف التذاكر المكتملة أو المستدعاة
    if ticket.status in ["examined", "called"]:
        flash("لا يمكن حذف تذكرة مكتملة أو مستدعاة", "error")
        return redirect(url_for('secretary.waiting_queue'))
    
    patient_name = ticket.patient.full_name
    db.session.delete(ticket)
    db.session.commit()
    
    flash(f"تم حذف تذكرة المريض {patient_name} من قائمة الانتظار", "success")
    return redirect(url_for('secretary.waiting_queue'))





# ==================== إدارة المدفوعات ====================

@secretary.route("/payments")
@login_required
@secretary_required
def payments():
    """عرض قائمة المدفوعات المعلقة"""
    page = request.args.get('page', 1, type=int)
    payment_filter = request.args.get('payment', 'all')
    
    # بناء الاستعلام
    query = Visit.query
    
    if payment_filter != 'all':
        query = query.filter_by(payment_status=payment_filter)
    
    # ترتيب حسب التاريخ
    visits = query.order_by(Visit.date.desc()).paginate(
        page=page, per_page=15, error_out=False
    )
    
    return render_template('secretary/payments.html', 
                         visits=visits, 
                         payment_filter=payment_filter)


@secretary.route("/visit/<int:visit_id>/update_payment", methods=['GET', 'POST'])
@login_required
@secretary_required
def update_visit_payment(visit_id):
    """تحديث حالة الدفع للزيارة"""
    visit = Visit.query.get_or_404(visit_id)
    form = PaymentUpdateForm()
    
    if request.method == 'GET':
        form.payment_status.data = visit.payment_status
    
    if form.validate_on_submit():
        old_status = visit.payment_status
        visit.payment_status = form.payment_status.data
        db.session.commit()
        
        flash(f"تم تحديث حالة الدفع للمريض {visit.patient.full_name} من '{old_status}' إلى '{form.payment_status.data}'", "success")
        return redirect(url_for('secretary.payments'))
    
    return render_template('secretary/update_payment.html', form=form, visit=visit)


@secretary.route("/visit/<int:visit_id>/quick_update_payment", methods=['POST'])
@login_required
@secretary_required
def quick_update_payment(visit_id):
    """تحديث سريع لحالة الدفع"""
    visit = Visit.query.get_or_404(visit_id)
    
    new_status = request.form.get('payment_status')
    valid_statuses = ['مدفوع', 'غير مدفوع', 'مدفوع جزئياً']
    
    if new_status in valid_statuses:
        old_status = visit.payment_status
        visit.payment_status = new_status
        db.session.commit()
        
        flash(f"تم تحديث حالة الدفع للمريض {visit.patient.full_name} من '{old_status}' إلى '{new_status}'", "success")
    else:
        flash("حالة دفع غير صحيحة", "error")
    
    return redirect(url_for('secretary.payments'))


# ==================== مواعيد الأيام القادمة ====================

@secretary.route("/upcoming_appointments")
@login_required
@secretary_required
def upcoming_appointments():
    """عرض مواعيد الأيام القادمة (اليوم، الغد، بعد الغد)"""
    from datetime import datetime, timedelta
    
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    day_after_tomorrow = today + timedelta(days=2)
    
    # مواعيد اليوم
    today_appointments = Appointment.query.filter(
        db.func.date(Appointment.appointment_date) == today,
        Appointment.status == "مجدول"
    ).order_by(Appointment.appointment_date.asc()).all()
    
    # مواعيد الغد
    tomorrow_appointments = Appointment.query.filter(
        db.func.date(Appointment.appointment_date) == tomorrow,
        Appointment.status == "مجدول"
    ).order_by(Appointment.appointment_date.asc()).all()
    
    # مواعيد بعد الغد
    day_after_appointments = Appointment.query.filter(
        db.func.date(Appointment.appointment_date) == day_after_tomorrow,
        Appointment.status == "مجدول"
    ).order_by(Appointment.appointment_date.asc()).all()
    
    return render_template('secretary/upcoming_appointments.html',
                         today_appointments=today_appointments,
                         tomorrow_appointments=tomorrow_appointments,
                         day_after_appointments=day_after_appointments,
                         today=today,
                         tomorrow=tomorrow,
                         day_after_tomorrow=day_after_tomorrow)


@secretary.route("/appointment/<int:appointment_id>/mark_contacted", methods=['POST'])
@login_required
@secretary_required
def mark_appointment_contacted(appointment_id):
    """تحديد موعد كمتصل به"""
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # إضافة ملاحظة أنه تم الاتصال
    contact_note = f"تم الاتصال بالمريض في {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    if appointment.notes:
        appointment.notes += f"\n{contact_note}"
    else:
        appointment.notes = contact_note
    
    appointment.updated_at = datetime.now()
    db.session.commit()
    
    flash(f"تم تسجيل الاتصال بالمريض {appointment.patient.full_name}", "success")
    return redirect(url_for('secretary.upcoming_appointments'))


# ==================== نظام التذاكر مع الأولوية ====================

@secretary.route("/create_waiting_ticket/<int:patient_id>")
@login_required
@secretary_required
def create_waiting_ticket(patient_id):
    """إنشاء تذكرة انتظار للمريض"""
    patient = Patient.query.get_or_404(patient_id)
    today = datetime.now().date()
    
    # التحقق من وجود موعد للمريض اليوم
    today_appointment = Appointment.query.filter(
        Appointment.patient_id == patient_id,
        db.func.date(Appointment.appointment_date) == today,
        Appointment.status == "مجدول"
    ).first()
    
    # تحديد نوع التذكرة والأولوية
    ticket_type = "regular"
    priority = 0
    appointment_id = None
    
    if today_appointment:
        # التحقق من وقت الموعد
        appointment_time = today_appointment.appointment_date.time()
        current_time = datetime.now().time()
        
        # إذا كان الوقت الحالي >= وقت الموعد، يحصل على أولوية
        if current_time >= appointment_time:
            ticket_type = "reservation"
            priority = 1
            appointment_id = today_appointment.id
    
    # الحصول على آخر رقم تذكرة اليوم
    last_ticket = Ticket.query.filter(
        db.func.date(Ticket.created_at) == today
    ).order_by(Ticket.number.desc()).first()
    
    next_number = (last_ticket.number + 1) if last_ticket else 1
    
    # إنشاء التذكرة
    ticket = Ticket(
        patient_id=patient_id,
        number=next_number,
        ticket_type=ticket_type,
        appointment_id=appointment_id,
        priority=priority,
        status="waiting"
    )
    
    db.session.add(ticket)
    db.session.commit()
    
    # رسالة تأكيد مختلفة حسب نوع التذكرة
    if ticket_type == "reservation":
        flash(f"تم إنشاء تذكرة أولوية رقم {ticket.display_number} للمريض {patient.full_name} (لديه موعد اليوم)", "success")
    else:
        flash(f"تم إنشاء تذكرة رقم {ticket.display_number} للمريض {patient.full_name}", "success")
    
    return redirect(url_for('secretary.waiting_queue'))


@secretary.route("/waiting_queue")
@login_required
@secretary_required
def waiting_queue():
    """عرض قائمة الانتظار مع الأولوية"""
    today = datetime.now().date()
    
    # الحصول على التذاكر المنتظرة مرتبة حسب الأولوية ثم الرقم
    waiting_tickets = Ticket.query.filter(
        db.func.date(Ticket.created_at) == today,
        Ticket.status.in_(["waiting"])
    ).order_by(
        Ticket.priority.desc(),  # الأولوية أولاً (1 قبل 0)
        Ticket.number.asc()      # ثم الرقم تصاعدياً
    ).all()
    
    # الحصول على التذكرة المستدعاة حالياً
    called_ticket = Ticket.query.filter(
        db.func.date(Ticket.created_at) == today,
        Ticket.status == "called"
    ).first()
    
    return render_template('secretary/waiting_queue.html',
                         waiting_tickets=waiting_tickets,
                         called_ticket=called_ticket)


@secretary.route("/call_next_ticket", methods=['POST'])
@login_required
@secretary_required
def call_next_ticket():
    """استدعاء التذكرة التالية"""
    today = datetime.now().date()
    
    # إنهاء التذكرة المستدعاة حالياً
    current_called = Ticket.query.filter(
        db.func.date(Ticket.created_at) == today,
        Ticket.status == "called"
    ).first()
    
    if current_called:
        current_called.status = "done"
    
    # الحصول على التذكرة التالية (أولوية ثم ترتيب)
    next_ticket = Ticket.query.filter(
        db.func.date(Ticket.created_at) == today,
        Ticket.status == "waiting"
    ).order_by(
        Ticket.priority.desc(),
        Ticket.number.asc()
    ).first()
    
    if next_ticket:
        next_ticket.status = "called"
        db.session.commit()
        
        flash(f"تم استدعاء التذكرة رقم {next_ticket.display_number} - {next_ticket.patient.full_name}", "success")
    else:
        flash("لا توجد تذاكر في قائمة الانتظار", "info")
    
    return redirect(url_for('secretary.waiting_queue'))


@secretary.route("/delete_ticket/<int:ticket_id>", methods=['POST'])
@login_required
@secretary_required
def delete_ticket_new(ticket_id):
    """حذف تذكرة من قائمة الانتظار (النسخة الجديدة)"""
    ticket = Ticket.query.get_or_404(ticket_id)
    patient_name = ticket.patient.full_name
    ticket_number = ticket.display_number
    
    db.session.delete(ticket)
    db.session.commit()
    
    flash(f"تم حذف التذكرة رقم {ticket_number} للمريض {patient_name}", "success")
    return redirect(url_for('secretary.waiting_queue'))


@secretary.route("/update-payment-status", methods=['POST'])
@login_required
@secretary_required
def update_payment_status():
    """تحديث حالة الدفع للزيارة"""
    try:
        data = request.get_json()
        visit_id = data.get('visit_id')
        payment_status = data.get('payment_status')
        
        if not visit_id or not payment_status:
            return jsonify({'success': False, 'message': 'بيانات غير مكتملة'})
        
        # التحقق من صحة حالة الدفع
        valid_statuses = ['مدفوع', 'غير مدفوع', 'مدفوع جزئياً']
        if payment_status not in valid_statuses:
            return jsonify({'success': False, 'message': 'حالة دفع غير صحيحة'})
        
        # العثور على الزيارة وتحديثها
        visit = Visit.query.get_or_404(visit_id)
        visit.payment_status = payment_status
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'تم تحديث حالة الدفع إلى: {payment_status}'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'حدث خطأ في التحديث'})


@secretary.route("/secretary/visit/<int:visit_id>/mark_as_paid", methods=['POST'])
@login_required
@secretary_required
def mark_as_paid(visit_id):
    """تحديد الزيارة كمدفوعة سريع"""
    try:
        visit = Visit.query.get_or_404(visit_id)
        
        # تحديث حالة الدفع إلى مدفوع
        old_status = visit.payment_status
        visit.payment_status = 'مدفوع'
        db.session.commit()
        
        flash(f'تم تحديد زيارة المريض {visit.patient.full_name} كمدفوعة', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('حدث خطأ في تحديث حالة الدفع', 'danger')
    
    return redirect(url_for('secretary.dashboard'))





@secretary.route("/secretary/visit/<int:visit_id>/mark_as_paid_get", methods=['GET'])
@login_required
@secretary_required
def mark_as_paid_get(visit_id):
    """تحديد الزيارة كمدفوعة سريع (GET)"""
    try:
        visit = Visit.query.get_or_404(visit_id)
        
        # تحديث حالة الدفع إلى مدفوع
        old_status = visit.payment_status
        visit.payment_status = 'مدفوع'
        db.session.commit()
        
        flash(f'تم تحديد زيارة المريض {visit.patient.full_name} كمدفوعة', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('حدث خطأ في تحديث حالة الدفع', 'danger')
    
    return redirect(url_for('secretary.dashboard'))


def get_last_completed_visit():
    """الحصول على آخر زيارة مكتملة اليوم"""
    today = datetime.now().date()
    
    # البحث عن آخر زيارة مكتملة اليوم
    last_visit = Visit.query.filter(
        db.func.date(Visit.date) == today
    ).order_by(Visit.date.desc()).first()
    
    return last_visit


# ==================== API Endpoints ====================

@secretary.route("/secretary/api/search-patients-for-ticket")
@login_required
@secretary_required
def api_search_patients_for_ticket():
    """API للبحث عن المرضى لإنشاء التذاكر"""
    term = request.args.get('term', '').strip()
    
    if not term or len(term) < 2:
        return jsonify([])
    
    # البحث في الاسم ورقم الهاتف
    patients = Patient.query.filter(
        db.or_(
            Patient.full_name.contains(term),
            Patient.phone.contains(term)
        )
    ).limit(10).all()
    
    # تحويل النتائج إلى JSON مع التأكد من التشفير الصحيح
    results = []
    for patient in patients:
        results.append({
            'id': patient.id,
            'full_name': str(patient.full_name) if patient.full_name else '',
            'phone': str(patient.phone) if patient.phone else '',
            'birth_date': patient.birth_date.strftime('%Y-%m-%d') if patient.birth_date else None,
            'gender': str(patient.gender) if patient.gender else '',
            'blood_group': str(patient.blood_group) if patient.blood_group else ''
        })
    
    # إرجاع JSON مع التأكد من التشفير العربي
    from flask import current_app
    response = current_app.response_class(
        response=current_app.json.dumps(results, ensure_ascii=False),
        status=200,
        mimetype='application/json; charset=utf-8'
    )
    return response


@secretary.route("/secretary/api/search-patients")
@login_required
@secretary_required
def api_search_patients_general():
    """API للبحث عن المرضى (للاستخدام العام)"""
    term = request.args.get('term', '').strip()
    
    if not term or len(term) < 2:
        return jsonify([])
    
    # البحث في الاسم ورقم الهاتف
    patients = Patient.query.filter(
        db.or_(
            Patient.full_name.contains(term),
            Patient.phone.contains(term)
        )
    ).limit(10).all()
    
    # تحويل النتائج إلى JSON
    results = []
    for patient in patients:
        results.append({
            'id': patient.id,
            'full_name': patient.full_name,
            'phone': patient.phone,
            'view_url': url_for('secretary.patient_details', patient_id=patient.id)
        })
    
    return jsonify(results)


# ==================== المواعيد الأونلاين ====================

@secretary.route("/online-appointments")
@login_required
@secretary_required
def online_appointments():
    """عرض المواعيد الأونلاين المحجوزة عبر الإنترنت"""
    import requests
    from datetime import datetime
    from flask import session
    
    # تحديث session لمنع انتهاء الصلاحية
    session.permanent = True
    
    # الحصول على فلاتر من query parameters
    status_filter = request.args.get('status', '')
    date_filter = request.args.get('date', '')
    
    try:
        # بناء URL مع الفلاتر - استخدام الموقع المستضاف
        api_url = 'https://appointment-1-96c4.onrender.com/api/appointments/all?token=123456'
        
        if status_filter:
            api_url += f'&status={status_filter}'
        if date_filter:
            api_url += f'&date={date_filter}'
            
        # جلب المواعيد من API الخارجي
        response = requests.get(api_url, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            appointments = data.get('appointments', [])
            count = data.get('count', 0)
            
            # تحويل التواريخ إلى كائنات datetime لسهولة التعامل معها
            for appointment in appointments:
                try:
                    # تحويل التاريخ والوقت إلى datetime
                    date_str = appointment.get('date', '')
                    time_str = appointment.get('time', '')
                    if date_str and time_str:
                        datetime_str = f"{date_str} {time_str}"
                        appointment['datetime_obj'] = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
                    
                    # تحويل created_at إلى datetime
                    created_at = appointment.get('created_at', '')
                    if created_at:
                        appointment['created_at_obj'] = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
                except:
                    pass
            
            # قائمة الحالات المتاحة للفلترة (حسب API)
            available_statuses = ['قيد التأكيد', 'مؤكد', 'ملغي', 'مكتمل']
            
            return render_template('secretary/online_appointments.html',
                                 appointments=appointments,
                                 count=count,
                                 title="المواعيد الأونلاين",
                                 available_statuses=available_statuses,
                                 current_status_filter=status_filter,
                                 current_date_filter=date_filter)
        else:
            flash('فشل في جلب المواعيد الأونلاين', 'danger')
            return render_template('secretary/online_appointments.html',
                                 appointments=[],
                                 count=0,
                                 error="فشل في الاتصال بخدمة المواعيد",
                                 title="المواعيد الأونلاين",
                                 available_statuses=['قيد التأكيد', 'مؤكد', 'ملغي', 'مكتمل'],
                                 current_status_filter=status_filter,
                                 current_date_filter=date_filter)
    except requests.RequestException:
        flash('لا يمكن الاتصال بخدمة المواعيد الأونلاين. تأكد من اتصالك بالإنترنت.', 'warning')
        return render_template('secretary/online_appointments.html',
                             appointments=[],
                             count=0,
                             error="خدمة المواعيد غير متاحة حالياً",
                             title="المواعيد الأونلاين",
                             available_statuses=['قيد التأكيد', 'مؤكد', 'ملغي', 'مكتمل'],
                             current_status_filter=status_filter,
                             current_date_filter=date_filter)


@secretary.route("/online-appointments/call/<int:appointment_id>", methods=['POST'])
@login_required
@secretary_required
def call_online_appointment(appointment_id):
    """الاتصال المباشر بالمريض (توجيه لتطبيق الهاتف)"""
    # هذا الـ route لن يستخدم - سيتم الاتصال المباشر عبر tel: links
    flash('استخدم زر الاتصال المباشر (الأزرق) للاتصال بالمريض', 'info')
    return redirect(url_for('secretary.online_appointments'))


@secretary.route("/online-appointments/confirm/<int:appointment_id>", methods=['POST'])
@login_required
@secretary_required
def confirm_online_appointment(appointment_id):
    """تأكيد الموعد الأونلاين"""
    import requests
    from flask import session
    
    # تحديث session لمنع انتهاء الصلاحية
    session.permanent = True
    
    try:
        # إرسال طلب لتحديث حالة الموعد إلى "مؤكد"
        update_data = {
            'status': 'مؤكد'
        }
        
        response = requests.put(
            f'https://appointment-1-96c4.onrender.com/api/appointments/{appointment_id}/status?token=123456',
            json=update_data,
            headers={'Content-Type': 'application/json'},
            timeout=15
        )
        
        if response.status_code == 200:
            flash('تم تأكيد الموعد بنجاح', 'success')
        else:
            flash('فشل في تأكيد الموعد', 'danger')
            
    except requests.RequestException:
        flash('خطأ في الاتصال بخدمة المواعيد', 'danger')
    
    return redirect(url_for('secretary.online_appointments'))


@secretary.route("/online-appointments/cancel/<int:appointment_id>", methods=['POST'])
@login_required
@secretary_required
def cancel_online_appointment(appointment_id):
    """إلغاء الموعد الأونلاين"""
    import requests
    from flask import session
    
    # تحديث session لمنع انتهاء الصلاحية
    session.permanent = True
    
    try:
        # إرسال طلب لتحديث حالة الموعد إلى "ملغي"
        update_data = {
            'status': 'ملغي'
        }
        
        response = requests.put(
            f'https://appointment-1-96c4.onrender.com/api/appointments/{appointment_id}/status?token=123456',
            json=update_data,
            headers={'Content-Type': 'application/json'},
            timeout=15
        )
        
        if response.status_code == 200:
            flash('تم إلغاء الموعد', 'info')
        else:
            flash('فشل في إلغاء الموعد', 'danger')
            
    except requests.RequestException:
        flash('خطأ في الاتصال بخدمة المواعيد', 'danger')
    
    return redirect(url_for('secretary.online_appointments'))


@secretary.route("/online-appointments/complete/<int:appointment_id>", methods=['POST'])
@login_required
@secretary_required
def complete_online_appointment(appointment_id):
    """تحديد الموعد الأونلاين كمكتمل"""
    import requests
    from flask import session
    
    # تحديث session لمنع انتهاء الصلاحية
    session.permanent = True
    
    try:
        # إرسال طلب لتحديث حالة الموعد إلى "مكتمل"
        update_data = {
            'status': 'مكتمل'
        }
        
        response = requests.put(
            f'https://appointment-1-96c4.onrender.com/api/appointments/{appointment_id}/status?token=123456',
            json=update_data,
            headers={'Content-Type': 'application/json'},
            timeout=15
        )
        
        if response.status_code == 200:
            flash('تم تحديد الموعد كمكتمل', 'success')
        else:
            flash('فشل في تحديث الموعد', 'danger')
            
    except requests.RequestException:
        flash('خطأ في الاتصال بخدمة المواعيد', 'danger')
    
    return redirect(url_for('secretary.online_appointments'))
