from clinic_app import create_app, db
import socket
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = create_app()  # ✅ هذا موجود في المستوى الأعلى، جيد!

# التحقق من وجود قاعدة البيانات
database_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'clinic.db')
if not os.path.exists(database_path):
    print("إنشاء قاعدة بيانات جديدة...")
    with app.app_context():
        db.create_all()
        print("تم إنشاء قاعدة البيانات بنجاح!")
else:
    print("قاعدة البيانات موجودة بالفعل...")

# فقط هذه الوظائف تحت if __name__ == "__main__"
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

if __name__ == "__main__":
    local_ip = get_local_ip()
    print(f"* شاشة الانتظار متاحة على: http://{local_ip}:5000/waiting-room")
    print(f"* تشغيل ClinicEase على: http://{local_ip}:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
