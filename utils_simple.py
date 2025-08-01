from flask import current_app, render_template
import os
from datetime import datetime

def generate_prescription_pdf(prescription, visit):
    """
    بدلاً من إنشاء PDF، قم بإنشاء ملف HTML يمكن طباعته
    """
    # إنشاء مجلد للوصفات الطبية إذا لم يكن موجودًا
    prescriptions_dir = os.path.join(current_app.root_path, "static", "prescriptions")
    os.makedirs(prescriptions_dir, exist_ok=True)

    # إنشاء اسم الملف
    current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"prescription_{visit.patient_id}_{visit.id}_{current_date}.html"
    file_path = os.path.join(prescriptions_dir, filename)

    # إنشاء محتوى HTML للوصفة
    html_content = render_template(
        "doctor/prescription_pdf.html",
        prescription=prescription,
        visit=visit,
        patient=visit.patient,
        doctor=visit.doctor,
        date=datetime.now()
    )

    # كتابة ملف HTML
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # إرجاع المسار النسبي للملف
    return os.path.join("prescriptions", filename)
