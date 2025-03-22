from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, jsonify
from flask_socketio import SocketIO, join_room, leave_room, emit
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.utils import secure_filename
from colorama import Fore, Style
from flask_session import Session
from celery import Celery
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
import os
import socket
import secrets
from collections import defaultdict
from functools import wraps

# تهيئة التطبيق
app = Flask(__name__)
hostname = socket.gethostname()
socketio = SocketIO(app, async_mode="eventlet")

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
local_ip = s.getsockname()[0]
s.close()

# إعداد المفتاح السري
SECRET_KEY_FILE = 'key.txt'

if os.path.exists(SECRET_KEY_FILE):
    with open(SECRET_KEY_FILE, 'r') as key_file:
        app.secret_key = key_file.read().strip()
else:
    app.secret_key = secrets.token_hex(32)  
    with open(SECRET_KEY_FILE, 'w') as key_file:
        key_file.write(app.secret_key)

# إعداد نظام تسجيل الأخطاء (Logging)
handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=3)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

# إعداد Flask-Session
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# إعداد Celery
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

# إعداد Limiter للحد من الطلبات
limiter = Limiter(app=app, key_func=get_remote_address)

# إعداد مجلد رفع الملفات
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt','csv', 'apk', 'mp3', 'mp4', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# إنشاء مجلد الرفع إذا لم يكن موجودًا
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# تحميل كلمة المرور من الملف (بدون تشفير)
PASSWORD_FILE = "password.txt"

if os.path.exists(PASSWORD_FILE):
    with open(PASSWORD_FILE, "r") as f:
        user_password = f.read().strip()
else:
    user_password = "21102004"  # كلمة مرور افتراضية
    with open(PASSWORD_FILE, "w") as f:
        f.write(user_password)

# بيانات المدير
admin_credentials = {
    "username": "mohamed9x60",
    "password": "mohamed9x60"
}

# إعداد قائمة العناوين المحظورة
BAN_FILE = "banned_ips.txt"

def load_banned_ips():
    """تحميل قائمة العناوين المحظورة."""
    if os.path.exists(BAN_FILE):
        with open(BAN_FILE, 'r') as f:
            return set(line.strip() for line in f)
    return set()

def save_banned_ip(ip):
    """حفظ عنوان IP محظور."""
    if ip:
        with open(BAN_FILE, 'a') as f:
            f.write(ip + "\n")

banned_ips = load_banned_ips()
ip_attempts = defaultdict(int)


channels = defaultdict(list)

# التحقق من صحة امتداد الملف
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# تسجيل إحصائيات الاستخدام
usage_stats = {
    'active_users': 0,
    'total_requests': 0,
    'last_request_time': None
}

@app.before_request
def track_usage():
    usage_stats['total_requests'] += 1
    usage_stats['last_request_time'] = datetime.now()

# وظيفة للتحقق من الصلاحيات
def requires_role(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'username' not in session or session.get('role') != role:
                return jsonify({"error": "غير مصرح لك بالوصول لهذه الصفحة."}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# الصفحة الرئيسية
@app.route('/')
def index():
    return render_template('index.html')

# صفحة تسجيل الدخول
@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    user_ip = request.remote_addr
    if user_ip in banned_ips:
        flash("تم حظرك من الدخول.", "error")
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == admin_credentials['username'] and password == admin_credentials['password']:
            session['username'] = username
            session['is_admin'] = True
            session['role'] = 'admin'
            return redirect(url_for('admin'))

        if password == user_password:
            session['username'] = username
            session['is_admin'] = False
            session['role'] = 'user'
            return redirect(url_for('chat'))
        else:
            ip_attempts[user_ip] += 1
            if ip_attempts[user_ip] >= 3:
                banned_ips.add(user_ip)
                save_banned_ip(user_ip)
                flash("تم حظرك بسبب محاولات الدخول الفاشلة المتكررة.", "error")
            else:
                flash("اسم المستخدم أو كلمة المرور غير صحيحة.", "error")

    return render_template('login.html')

# صفحة الدردشة
@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect(url_for('login'))
    uploaded_files = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('chat.html', username=session['username'], channels=channels.keys(), uploaded_files=uploaded_files)

# صفحة الأدمن
@app.route('/admin')
@requires_role('admin')
def admin():
    uploaded_files = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('admin.html', channels=channels, banned_ips=banned_ips, uploaded_files=uploaded_files)

# رفع الملفات
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash("لم يتم اختيار ملف.", "error")
        return redirect(request.url)

    file = request.files['file']
    if file.filename == '':
        flash("لم يتم اختيار ملف.", "error")
        return redirect(request.url)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        flash("تم رفع الملف بنجاح.", "success")
        return redirect(url_for('chat'))
    else:
        flash("نوع الملف غير مسموح به.", "error")
        return redirect(request.url)

# تحميل الملفات
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# طرد مستخدم 
@app.route('/kick_user', methods=['POST'])
def kick_user():
    username = request.args.get('username')
    room_code = request.args.get('room_code')

    if room_code in channels and username in channels[room_code]:
        channels[room_code].remove(username)
        socketio.emit('update_users', channels[room_code], room=room_code)
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "User not found"})

# حظر مستخدم في حالة تسجيل دخول خاكئة
@app.route('/ban_user', methods=['POST'])
def ban_user():
    username = request.args.get('username')
    banned_ips.add(username)
    save_banned_ip(username)
    socketio.emit('update_banned_ips', list(banned_ips), broadcast=True)  
    return jsonify({"success": True})

# حذف ملف معين 
@app.route('/delete_file', methods=['POST'])
def delete_file():
    filename = request.args.get('filename')
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "File not found"})

# SocketIO Events
@socketio.on('join_room')
def handle_join(data):
    room_code = data.get('room_code')
    username = session.get('username')

    if not username:
        return  # منع المستخدم غير المسجل من الانضمام

    if room_code not in channels:
        channels[room_code] = []
    if username not in channels[room_code]:
        channels[room_code].append(username)

    join_room(room_code)
    emit('update_users', channels[room_code], room=room_code)

@socketio.on('send_message')
def handle_message(data):
    room_code = data.get('room_code')
    username = session.get('username')
    message = data.get('message')

    if not username:
        return  # منع المستخدم غير المسجل من إرسال رسائل

    emit('receive_message', {'username': username, 'message': message}, room=room_code)

@socketio.on('leave_room')
def handle_leave(data):
    room_code = data.get('room_code')
    username = session.get('username')

    if room_code in channels and username in channels[room_code]:
        channels[room_code].remove(username)

    leave_room(room_code)
    emit('update_users', channels[room_code], room=room_code)

# تشغيل التطبيق
if __name__ == '__main__':
   print(f"Server is running on http://{local_ip}:5000")
   print(Fore.GREEN + f"Server is running on http://{local_ip}:5000" + Style.RESET_ALL)
   socketio.run(app, host=local_ip, port=5000, debug=True)
