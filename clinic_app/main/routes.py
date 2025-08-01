from flask import Blueprint, render_template, redirect, url_for, jsonify, Response, request
from flask_login import current_user
from clinic_app.models import Ticket, Patient
from datetime import datetime
from sqlalchemy import desc
import json
import time
import threading
import queue

# إنشاء بلوبرينت للمسارات الرئيسية
main = Blueprint("main", __name__)

# قائمة انتظار للإشعارات الصوتية
announcement_queue = queue.Queue()
connected_clients = []


@main.route("/")
@main.route("/home")
def home():
    """الصفحة الرئيسية"""
    if current_user.is_authenticated:
        if current_user.role == "doctor":
            return redirect(url_for("doctor.dashboard"))
        else:
            return redirect(url_for("secretary.dashboard"))

    return render_template("main/home.html", title="الصفحة الرئيسية")


@main.route("/waiting-room")
def waiting_room():
    """صفحة قاعة الانتظار - تعرض المريض الحالي وعدد المرضى في الانتظار"""
    # الحصول على المريض الحالي
    current_ticket = Ticket.query.filter_by(status="called").first()

    # الحصول على قائمة الانتظار
    today = datetime.now().date()
    waiting_tickets = Ticket.query.filter(
        Ticket.created_at >= today,
        Ticket.status == "waiting"
    ).order_by(Ticket.number).all()

    return render_template(
        "main/waiting_room.html",
        title="قاعة الانتظار",
        current_ticket=current_ticket,
        waiting_tickets=waiting_tickets,  # تمرير قائمة التذاكر الكاملة
        waiting_count=len(waiting_tickets)
    )


@main.route("/api/waiting-data")
def api_waiting_data():
    """API للحصول على بيانات قاعة الانتظار بتنسيق JSON"""
    # الحصول على المريض الحالي
    current_ticket = Ticket.query.filter_by(status="called").first()

    # الحصول على قائمة الانتظار
    today = datetime.now().date()
    waiting_tickets = Ticket.query.filter(
        Ticket.created_at >= today,
        Ticket.status == "waiting"
    ).order_by(Ticket.number).all()

    # تهيئة البيانات للرد
    response_data = {
        "current_ticket": None,
        "waiting_tickets": [],
        "waiting_count": len(waiting_tickets)
    }

    # إضافة بيانات التذكرة الحالية
    if current_ticket:
        # الحصول على بيانات المريض
        patient = Patient.query.get(current_ticket.patient_id)
        response_data["current_ticket"] = {
            "id": current_ticket.id,
            "number": current_ticket.number,
            "status": current_ticket.status,
            "patient_name": patient.full_name if patient else ""
        }

    # إضافة بيانات التذاكر في الانتظار
    for ticket in waiting_tickets:
        # الحصول على بيانات المريض
        patient = Patient.query.get(ticket.patient_id)
        response_data["waiting_tickets"].append({
            "id": ticket.id,
            "number": ticket.number,
            "status": ticket.status,
            "patient_name": patient.full_name if patient else ""
        })

    return jsonify(response_data)


@main.route("/api/get-current-ticket")
def get_current_ticket():
    """API للحصول على التذكرة الحالية بتنسيق JSON"""
    # الحصول على المريض الحالي
    current_ticket = Ticket.query.filter_by(status="called").first()

    # تهيئة البيانات للرد
    response_data = {
        "current_ticket": None
    }

    # إضافة بيانات التذكرة الحالية
    if current_ticket:
        response_data["current_ticket"] = {
            "id": current_ticket.id,
            "number": current_ticket.number,
            "status": current_ticket.status
        }

    return jsonify(response_data)


@main.route("/api/get-waiting-tickets")
def get_waiting_tickets():
    """API للحصول على قائمة التذاكر في الانتظار بتنسيق JSON"""
    # الحصول على قائمة الانتظار
    today = datetime.now().date()
    waiting_tickets = Ticket.query.filter(
        Ticket.created_at >= today,
        Ticket.status == "waiting"
    ).order_by(Ticket.number).all()

    # تهيئة البيانات للرد
    response_data = {
        "waiting_tickets": [],
        "waiting_count": len(waiting_tickets)
    }

    # إضافة بيانات التذاكر في الانتظار
    for ticket in waiting_tickets:
        response_data["waiting_tickets"].append({
            "id": ticket.id,
            "number": ticket.number,
            "status": ticket.status
        })

    return jsonify(response_data)


@main.route("/about")
def about():
    """صفحة عن التطبيق"""
    return render_template("main/about.html", title="عن التطبيق")


@main.route("/api/announcement-stream")
def announcement_stream():
    """Server-Sent Events stream للإشعارات الصوتية"""
    def event_stream():
        client_queue = queue.Queue()
        connected_clients.append(client_queue)
        
        try:
            while True:
                try:
                    # انتظار إشعار جديد مع timeout
                    announcement = client_queue.get(timeout=30)
                    yield f"data: {json.dumps(announcement)}\n\n"
                except queue.Empty:
                    # إرسال heartbeat للحفاظ على الاتصال
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
        except GeneratorExit:
            # إزالة العميل عند قطع الاتصال
            if client_queue in connected_clients:
                connected_clients.remove(client_queue)
    
    response = Response(event_stream(), mimetype="text/event-stream")
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Connection'] = 'keep-alive'
    return response


@main.route("/api/trigger-announcement", methods=["POST"])
def trigger_announcement():
    """API لإرسال إشعار مناداة إلى جميع شاشات قاعة الانتظار"""
    from flask_login import current_user
    
    # التحقق من أن المستخدم مسجل دخول وله صلاحية
    if not current_user.is_authenticated:
        return jsonify({'error': 'غير مصرح'}), 401
    
    if current_user.role not in ['secretary', 'doctor']:
        return jsonify({'error': 'ليس لديك صلاحية'}), 403
    
    try:
        data = request.get_json()
        ticket_number = data.get('ticket_number')
        patient_name = data.get('patient_name')
        
        if not ticket_number or not patient_name:
            return jsonify({'error': 'بيانات غير مكتملة'}), 400
        
        # إنشاء إشعار المناداة
        announcement = {
            'type': 'announcement',
            'ticket_number': ticket_number,
            'patient_name': patient_name,
            'timestamp': datetime.now().isoformat(),
            'triggered_by': current_user.username
        }
        
        # إرسال الإشعار إلى جميع العملاء المتصلين
        for client_queue in connected_clients[:]:  # نسخة من القائمة لتجنب التعديل أثناء التكرار
            try:
                client_queue.put_nowait(announcement)
            except queue.Full:
                # إزالة العملاء المنقطعين
                connected_clients.remove(client_queue)
        
        return jsonify({
            'success': True, 
            'message': 'تم إرسال الإشعار بنجاح',
            'clients_notified': len(connected_clients)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

