# سكريبت للتبديل السريع بين الموقع المستضاف و localhost
# استخدم هذا إذا كنت تريد العودة لـ localhost مؤقتاً

import os
import fileinput

def switch_to_localhost():
    """تحديث URLs للعمل مع localhost بدلاً من الموقع المستضاف"""
    
    routes_file = r"c:\Users\pc cam\Desktop\ClinicEase-main\clinic_app\secretary\routes.py"
    
    print("🔄 تحديث URLs للعمل مع localhost...")
    
    # قراءة الملف وتحديثه
    with open(routes_file, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # استبدال URLs
    old_url = 'https://appointment-1-96c4.onrender.com/api/appointments/'
    new_url = 'http://localhost:4000/api/appointments/'
    
    updated_content = content.replace(old_url, new_url)
    
    # كتابة الملف المحدث
    with open(routes_file, 'w', encoding='utf-8') as file:
        file.write(updated_content)
    
    print("✅ تم تحديث URLs بنجاح!")
    print(f"📝 تم استبدال: {old_url}")
    print(f"📝 بـ: {new_url}")
    print()
    print("🚀 خطوات التشغيل:")
    print("1. شغّل web API محلياً:")
    print('   cd "c:\\Users\\pc cam\\Desktop\\web api"')
    print("   python app.py")
    print()
    print("2. شغّل ClinicEase:")
    print('   cd "c:\\Users\\pc cam\\Desktop\\ClinicEase-main"')
    print("   python run.py")
    print()
    print("✨ الآن النظام سيعمل مع localhost!")

def switch_to_render():
    """تحديث URLs للعمل مع الموقع المستضاف"""
    
    routes_file = r"c:\Users\pc cam\Desktop\ClinicEase-main\clinic_app\secretary\routes.py"
    
    print("🔄 تحديث URLs للعمل مع الموقع المستضاف...")
    
    # قراءة الملف وتحديثه
    with open(routes_file, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # استبدال URLs
    old_url = 'http://localhost:4000/api/appointments/'
    new_url = 'https://appointment-1-96c4.onrender.com/api/appointments/'
    
    updated_content = content.replace(old_url, new_url)
    
    # كتابة الملف المحدث
    with open(routes_file, 'w', encoding='utf-8') as file:
        file.write(updated_content)
    
    print("✅ تم تحديث URLs بنجاح!")
    print(f"📝 تم استبدال: {old_url}")
    print(f"📝 بـ: {new_url}")
    print()
    print("🌐 الآن النظام سيعمل مع الموقع المستضاف!")
    print("⚠️  تأكد من أن الموقع المستضاف يحتوي على API endpoints")

def main():
    print("🔧 أداة تبديل API URLs")
    print("=" * 50)
    print("1. التبديل إلى localhost")
    print("2. التبديل إلى الموقع المستضاف")
    print("3. عرض الحالة الحالية")
    print("4. خروج")
    print()
    
    while True:
        choice = input("اختر رقم الخيار (1-4): ").strip()
        
        if choice == '1':
            switch_to_localhost()
            break
        elif choice == '2':
            switch_to_render()
            break
        elif choice == '3':
            show_current_status()
        elif choice == '4':
            print("👋 وداعاً!")
            break
        else:
            print("❌ خيار غير صحيح. اختر رقم من 1-4")

def show_current_status():
    """عرض الحالة الحالية للـ URLs"""
    
    routes_file = r"c:\Users\pc cam\Desktop\ClinicEase-main\clinic_app\secretary\routes.py"
    
    try:
        with open(routes_file, 'r', encoding='utf-8') as file:
            content = file.read()
        
        if 'localhost:4000' in content:
            print("📍 الحالة الحالية: localhost")
            print("🔗 API URL: http://localhost:4000/api/appointments/")
            print("⚠️  تأكد من تشغيل web API محلياً")
        elif 'appointment-1-96c4.onrender.com' in content:
            print("📍 الحالة الحالية: الموقع المستضاف")
            print("🔗 API URL: https://appointment-1-96c4.onrender.com/api/appointments/")
            print("⚠️  تأكد من وجود API endpoints على الموقع المستضاف")
        else:
            print("❓ لا يمكن تحديد الحالة الحالية")
        
        print()
        
    except FileNotFoundError:
        print("❌ لم يتم العثور على ملف routes.py")
    except Exception as e:
        print(f"❌ خطأ في قراءة الملف: {e}")

if __name__ == "__main__":
    main()

"""
===== كيفية الاستخدام =====

1. شغّل هذا السكريبت:
   python SWITCH_TO_LOCALHOST.py

2. اختر الخيار المناسب:
   - الخيار 1: للعمل مع localhost
   - الخيار 2: للعمل مع الموقع المستضاف

===== متى تستخدم كل خيار =====

استخدم localhost عندما:
✅ تريد اختبار سريع
✅ الموقع المستضاف لا يحتوي على API
✅ تريد تطوير وتجريب

استخدم الموقع المستضاف عندما:
✅ الموقع يحتوي على API كامل
✅ تريد حل دائم ومستقر
✅ تريد وصول من أجهزة متعددة

===== ملاحظات مهمة =====

🚨 عند استخدام localhost:
- يجب تشغيل web API محلياً أولاً
- cd "c:\Users\pc cam\Desktop\web api"
- python app.py

🌐 عند استخدام الموقع المستضاف:
- تأكد من إضافة API endpoints للموقع
- استخدم الكود في COMPLETE_WEB_API_CODE.py
"""