from flask import current_app, render_template, url_for
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4, inch
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
from reportlab.lib.units import mm, cm
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
from reportlab.platypus.flowables import HRFlowable

def generate_prescription_pdf(prescription, visit):
    # إنشاء مجلد للوصفات الطبية إذا لم يكن موجودًا
    static_folder = os.path.join(current_app.root_path, "static")
    os.makedirs(static_folder, exist_ok=True)
    
    prescriptions_dir = os.path.join(static_folder, "prescriptions")
    os.makedirs(prescriptions_dir, exist_ok=True)

    # إنشاء اسم الملف
    current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"prescription_{visit.patient_id}_{visit.id}_{current_date}.pdf"
    file_path = os.path.join(prescriptions_dir, filename)

    # إنشاء ملف PDF بحجم A4
    doc = SimpleDocTemplate(
        file_path, 
        pagesize=A4, 
        rightMargin=20*mm, 
        leftMargin=20*mm, 
        topMargin=20*mm, 
        bottomMargin=20*mm
    )
    styles = getSampleStyleSheet()
    story = []

    # إعدادات الخطوط المحسنة
    clinic_title = ParagraphStyle(
        'ClinicTitle',
        parent=styles['Title'],
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        fontSize=16,
        spaceAfter=2,
        leading=20,
        textColor=colors.black
    )
    
    subtitle_style = ParagraphStyle(
        'SubtitleStyle',
        parent=styles['Normal'],
        alignment=TA_CENTER,
        fontName='Helvetica',
        fontSize=12,
        spaceAfter=5,
        leading=14,
        textColor=colors.black
    )
    
    date_location_style = ParagraphStyle(
        'DateLocationStyle',
        parent=styles['Normal'],
        alignment=TA_LEFT,
        fontName='Helvetica',
        fontSize=11,
        spaceAfter=15,
        leading=14,
        textColor=colors.black
    )
    
    patient_label_style = ParagraphStyle(
        'PatientLabelStyle',
        parent=styles['Normal'],
        alignment=TA_LEFT,
        fontName='Helvetica',
        fontSize=11,
        spaceAfter=0,
        leading=14,
        textColor=colors.black
    )
    
    patient_value_style = ParagraphStyle(
        'PatientValueStyle',
        parent=styles['Normal'],
        alignment=TA_LEFT,
        fontName='Helvetica',
        fontSize=11,
        spaceAfter=8,
        leftIndent=50,
        leading=14,
        textColor=colors.black
    )
    
    prescription_title = ParagraphStyle(
        'PrescriptionTitle',
        parent=styles['Title'],
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        fontSize=14,
        spaceAfter=15,
        spaceBefore=25,
        leading=18,
        textColor=colors.black
    )
    
    medication_style = ParagraphStyle(
        'MedicationStyle',
        parent=styles['Normal'],
        alignment=TA_LEFT,
        fontName='Helvetica',
        fontSize=11,
        spaceAfter=15,
        leftIndent=25,
        leading=16,
        textColor=colors.black
    )
    
    # رأس الوصفة - معلومات العيادة
    story.append(Paragraph(f"cabinet Dentaire {visit.doctor.username}", clinic_title))
    story.append(Paragraph("7/7j", subtitle_style))
    story.append(Spacer(1, 30))
    
    # التاريخ والموقع
    location = "Oran"  # يمكنك تغيير هذا حسب موقع العيادة
    date_text = f"{location} le : {visit.date.strftime('%d/%m/%Y')}"
    story.append(Paragraph(date_text, date_location_style))
    
    # معلومات المريض في نفس السطر
    # الاسم
    patient_name = visit.patient.last_name.upper() if hasattr(visit.patient, 'last_name') else visit.patient.full_name.split()[-1].upper()
    name_table = Table([["Nom :", patient_name]], colWidths=[50, 200])
    name_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(name_table)
    
    # الأسماء
    patient_firstname = visit.patient.first_name.upper() if hasattr(visit.patient, 'first_name') else visit.patient.full_name.split()[0].upper()
    prenom_table = Table([["Prénoms :", patient_firstname]], colWidths=[50, 200])
    prenom_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(prenom_table)
    
    # حساب العمر
    patient_age = ""
    if visit.patient.birth_date:
        from datetime import date
        today = date.today()
        age = today.year - visit.patient.birth_date.year - ((today.month, today.day) < (visit.patient.birth_date.month, visit.patient.birth_date.day))
        patient_age = f"{age} an(s)"
    
    age_table = Table([["Age :", patient_age]], colWidths=[50, 200])
    age_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(age_table)
    
    # عنوان الوصفة
    story.append(Paragraph("ORDONNANCE", prescription_title))
    
    # قائمة الأدوية
    medications_text = ""
    for i, med in enumerate(prescription.prescription_medications, 1):
        # بناء نص الدواء
        med_text = f"{i}.<br/>"
        med_text += f"&nbsp;&nbsp;&nbsp;&nbsp;{med.medication.name.upper()}"
        
        if med.quantity:
            med_text += f" {med.quantity.upper()}"
        
        med_text += "<br/>"
        
        if med.instructions:
            med_text += f"&nbsp;&nbsp;&nbsp;&nbsp;{med.instructions.upper()}"
        
        if i < len(prescription.prescription_medications):
            med_text += "<br/><br/>"
        
        medications_text += med_text
    
    story.append(Paragraph(medications_text, medication_style))
    
    # مساحة للتوقيع والختم
    story.append(Spacer(1, 100))
    
    # إنشاء الملف النهائي
    doc.build(story)
    
    # إرجاع المسار النسبي للملف
    relative_path = os.path.join("static", "prescriptions", filename)
    return relative_path