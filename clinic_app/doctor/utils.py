from flask import current_app, render_template, url_for
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter, A5, inch
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT

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
    doc = SimpleDocTemplate(file_path, pagesize=letter, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()
    story = []

    # إعدادات الخطوط المحسنة
    clinic_title = ParagraphStyle(
        'ClinicTitle',
        parent=styles['Title'],
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        fontSize=24,
        spaceAfter=5,
        leading=28,
        textColor=colors.darkblue
    )
    
    doctor_style = ParagraphStyle(
        'DoctorStyle',
        parent=styles['Normal'],
        alignment=TA_CENTER,
        fontName='Helvetica',
        fontSize=14,
        spaceAfter=15,
        leading=18,
        textColor=colors.darkblue
    )
    
    prescription_title = ParagraphStyle(
        'PrescriptionTitle',
        parent=styles['Title'],
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        fontSize=20,
        spaceAfter=20,
        leading=24,
        textColor=colors.darkgreen
    )
    
    arabic_heading = ParagraphStyle(
        'ArabicHeading',
        parent=styles['Heading1'],
        alignment=TA_RIGHT,
        fontName='Helvetica-Bold',
        fontSize=12,
        spaceAfter=5,
        leading=16
    )
    
    arabic_normal = ParagraphStyle(
        'ArabicNormal',
        parent=styles['Normal'],
        alignment=TA_RIGHT,
        fontName='Helvetica',
        fontSize=11,
        spaceAfter=3,
        leading=14
    )
    
    # رأس الوصفة - معلومات العيادة
    story.append(Paragraph("Cabinet Dentaire", clinic_title))
    story.append(Paragraph(f"Dr. {visit.doctor.username}", doctor_style))
    
    # خط فاصل
    story.append(Spacer(1, 10))
    line_data = [['_' * 80]]
    line_table = Table(line_data, colWidths=[400])
    line_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.grey),
    ]))
    story.append(line_table)
    story.append(Spacer(1, 15))
    
    # معلومات المريض والزيارة في جدول منظم
    patient_age = ""
    if visit.patient.birth_date:
        from datetime import date
        today = date.today()
        age = today.year - visit.patient.birth_date.year - ((today.month, today.day) < (visit.patient.birth_date.month, visit.patient.birth_date.day))
        patient_age = f"{age} سنة"
    
    patient_info = [
        ["Nom:", visit.patient.full_name, "Age:", patient_age],
        ["Date:", visit.date.strftime("%d/%m/%Y"), "Tel:", visit.patient.phone or "غير محدد"]
    ]
    
    patient_table = Table(patient_info, colWidths=[60, 140, 60, 140])
    patient_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTNAME', (3, 0), (3, -1), 'Helvetica'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
    ]))
    
    story.append(patient_table)
    story.append(Spacer(1, 20))
    
    # عنوان الوصفة
    story.append(Paragraph("ORDONNANCE", prescription_title))
    story.append(Spacer(1, 15))

    # قائمة الأدوية
    medications_data = []
    
    # إضافة رأس الجدول
    medications_data.append([
        Paragraph("#", arabic_heading), 
        Paragraph("الدواء", arabic_heading), 
        Paragraph("الكمية/المدة", arabic_heading),
        Paragraph("التعليمات", arabic_heading)
    ])
    
    # إضافة الأدوية
    for i, med in enumerate(prescription.prescription_medications, 1):
        medications_data.append([
            Paragraph(str(i), arabic_normal),
            Paragraph(med.medication.name, arabic_normal),
            Paragraph(med.quantity or "غير محدد", arabic_normal),
            Paragraph(med.instructions or "حسب الحاجة", arabic_normal)
        ])
    
    # إنشاء جدول الأدوية
    col_widths = [25, 120, 80, 155]
    medications_table = Table(medications_data, colWidths=col_widths)
    medications_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    story.append(medications_table)
    story.append(Spacer(1, 40))
    
    # إضافة معلومات إضافية إذا وجدت
    if visit.notes:
        notes_style = ParagraphStyle(
            'NotesStyle',
            parent=styles['Normal'],
            alignment=TA_LEFT,
            fontName='Helvetica',
            fontSize=10,
            spaceAfter=15,
            leading=14
        )
        story.append(Paragraph(f"Notes: {visit.notes}", notes_style))
        story.append(Spacer(1, 20))
    
    # إضافة توقيع الطبيب
    signature_style = ParagraphStyle(
        'SignatureStyle',
        parent=styles['Normal'],
        alignment=TA_RIGHT,
        fontName='Helvetica-Bold',
        fontSize=12,
        spaceAfter=10,
        leading=16
    )
    
    signature_text = f"Dr. {visit.doctor.username}"
    story.append(Paragraph(signature_text, signature_style))
    
    # إضافة خط للتوقيع
    signature_line = [['_' * 30]]
    sig_table = Table(signature_line, colWidths=[200])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.grey),
    ]))
    story.append(sig_table)
    
    # إنشاء الملف النهائي
    doc.build(story)
    
    # إرجاع المسار النسبي للملف
    relative_path = os.path.join("static", "prescriptions", filename)
    return relative_path
