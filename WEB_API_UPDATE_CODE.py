# كود تحديث Web API لحل مشكلة تداخل Sessions
# يجب إضافة هذا الكود في ملف app.py في web API

"""
تحديث مطلوب في ملف app.py على الموقع المستضاف:
https://appointment-1-96c4.onrender.com/

1. استبدل الجزء الحالي:
   app.secret_key = 'your-secret-key-here'

2. بهذا الكود:
"""

from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)

# ===== إعدادات منفصلة عن ClinicEase لتجنب تداخل الـ sessions =====
app.secret_key = 'web_api_appointments_secret_key_2024_unique_render'  # مختلف تماماً عن ClinicEase

# إعدادات Cookie منفصلة لتجنب التداخل مع ClinicEase
app.config['SESSION_COOKIE_NAME'] = 'appointments_api_session'  # اسم مختلف عن ClinicEase
app.config['SESSION_COOKIE_PATH'] = '/'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = True  # للإنتاج على HTTPS (Render)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_DOMAIN'] = None  # للسماح بالعمل على النطاقات المختلفة
app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30 دقيقة (أقل من ClinicEase)

# إعدادات إضافية لتجنب التداخل
app.config['APPLICATION_ROOT'] = '/'
app.config['SESSION_REFRESH_EACH_REQUEST'] = False  # مختلف عن ClinicEase

# إعدادات أمان إضافية للإنتاج
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS فقط على Render
app.config['WTF_CSRF_ENABLED'] = False  # تعطيل CSRF لأن هذا API بسيط

# ===== نهاية الإعدادات الجديدة =====

# إعدادات قاعدة البيانات (باقي الكود يبقى كما هو)
DATABASE = 'appointments.db'
API_TOKEN = '123456'

# باقي الكود يبقى نفسه...

"""
===== تعليمات التطبيق =====

1. افتح Dashboard الخاص بـ Render
2. اذهب لمشروع appointment-1-96c4
3. افتح ملف app.py
4. استبدل الجزء من app.secret_key حتى DATABASE = 'appointments.db' بالكود أعلاه
5. احفظ واتركه ينشر التحديث تلقائياً

===== أو البديل الأسرع =====

إذا كنت تريد إضافة الحد الأدنى فقط، أضف هذين السطرين فقط:

app.config['SESSION_COOKIE_NAME'] = 'appointments_api_session'
app.secret_key = 'unique_appointments_api_secret_2024_render'

===== النتيجة المتوقعة =====

بعد التحديث:
- ClinicEase سيستخدم cookie باسم 'clinicease_session'
- Web API سيستخدم cookie باسم 'appointments_api_session'
- لن يحدث تداخل بين النظامين
- السكرتيرة ستبقى مسجلة دخول في ClinicEase حتى لو حجزت موعد من الموقع المستضاف

===== اختبار الحل =====

1. سجل دخول في ClinicEase كسكرتيرة
2. افتح تبويب جديد: https://appointment-1-96c4.onrender.com/book
3. احجز موعد
4. ارجع لـ ClinicEase → يجب أن تبقى مسجلة دخول ✅
"""

# رسالة تأكيد للمطور
print("🔧 يجب تطبيق هذه التحديثات على الموقع المستضاف في Render")
print("📎 الرابط: https://appointment-1-96c4.onrender.com/")
print("✅ بعد التحديث ستنحل مشكلة تسجيل الخروج التلقائي")