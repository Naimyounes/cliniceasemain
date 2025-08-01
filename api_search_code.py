
@secretary.route("/api/search/patients")
@login_required
@secretary_required
def api_search_patients():
    """API للبحث الفوري عن المرضى أثناء الكتابة"""
    search_term = request.args.get("term", "")

    if not search_term or len(search_term) < 2:
        # لا نقوم بإرجاع نتائج إذا كان مصطلح البحث فارغًا أو حرف واحد فقط
        return jsonify([])

    # البحث في قاعدة البيانات
    patients = Patient.query.filter(
        Patient.full_name.ilike(f"%{search_term}%") |
        Patient.phone.ilike(f"%{search_term}%")
    ).limit(10).all()  # نحدد النتائج بـ 10 فقط لتحسين الأداء

    # إنشاء قائمة بنتائج البحث
    results = []
    for patient in patients:
        patient_data = {
            "id": patient.id,
            "full_name": patient.full_name,
            "phone": patient.phone,
            "gender": patient.gender if hasattr(patient, 'gender') else "غير محدد",
            "url": url_for("secretary.patient_details", patient_id=patient.id)
        }
        results.append(patient_data)

    return jsonify(results)
