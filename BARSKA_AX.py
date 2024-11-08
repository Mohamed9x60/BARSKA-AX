# الخادم الرئيسي للتطبيق
print("welcom")
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from flask_socketio import SocketIO, join_room, leave_room, emit
import os
import secrets
import base64
from collections import defaultdict

app = Flask(__name__)

# إعداد المفتاح السري
if os.path.exists('key.txt'):
    with open('key.txt', 'r') as key_file:
        app.secret_key = key_file.read().strip()
else:
    app.secret_key = secrets.token_hex(16)
    with open('key.txt', 'w') as key_file:
        key_file.write(app.secret_key)

# إعداد SocketIO
socketio = SocketIO(app)

# إعداد ملف حظر الـ IPs
BAN_FILE = "banned_ips.txt"

def load_banned_ips():
    """تحميل قائمة العناوين المحظورة من الملف."""
    if os.path.exists(BAN_FILE):
        with open(BAN_FILE, 'r') as f:
            return set(line.strip() for line in f)
    return set()

def save_banned_ip(ip):
    """حفظ عنوان IP المحظور في الملف."""
    with open(BAN_FILE, 'a') as f:
        f.write(ip + "\n")

banned_ips = load_banned_ips()
ip_attempts = defaultdict(int)

# تحميل بيانات تسجيل الدخول من الملفات
with open("paswod.txt", "r") as f:
    user_password = f.read().strip()

admin_credentials = {"username": "mohamed", "password": "2842002"}
correct_pin = "1234"  # يمكنك تغيير الـ PIN هنا

# إعداد متغير لتخزين المستخدمين في كل قناة
channels = defaultdict(list)

@app.route('/')
def index():
    """الصفحة الرئيسية."""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """صفحة تسجيل الدخول."""
    user_ip = request.remote_addr
    if user_ip in banned_ips:
        return "تم حظرك من الدخول."

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # التحقق من بيانات الاعتماد
        if password == user_password:
            session['username'] = username
            session['is_admin'] = False
            return redirect(url_for('chat'))
        elif username == admin_credentials['username'] and password == admin_credentials['password']:
            session['username'] = username
            session['is_admin'] = True
            return redirect(url_for('admin'))
        else:
            ip_attempts[user_ip] += 1
            if ip_attempts[user_ip] >= 3:
                banned_ips.add(user_ip)
                save_banned_ip(user_ip)
                return "تم حظرك بسبب محاولات الدخول الفاشلة المتكررة."

    return render_template('login.html')

@app.route('/chat')
def chat():
    """صفحة الدردشة."""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('chat.html', username=session['username'], channels=channels.keys())

@app.route('/admin')
def admin():
    """صفحة الإدارة."""
    if 'username' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))

    return render_template('admin.html', channels=channels, banned_ips=banned_ips)

@socketio.on('join_room')
def handle_join(data):
    """الانضمام إلى غرفة الدردشة."""
    room_code = data['room_code']
    username = session.get('username')

    if room_code not in channels:
        channels[room_code] = []  # تأكد من وجود الغرفة
    if username not in channels[room_code]:
        channels[room_code].append(username)
    join_room(room_code)
    emit('update_users', channels[room_code], room=room_code)

@socketio.on('send_message')
def handle_message(data):
    """إرسال رسالة في غرفة الدردشة."""
    room_code = data['room_code']
    username = session.get('username')
    message = data['message']
    emit('receive_message', {'username': username, 'message': message}, room=room_code)

@socketio.on('leave_room')
def handle_leave(data):
    """ترك غرفة الدردشة."""
    room_code = data['room_code']
    username = session.get('username')

    if room_code in channels and username in channels[room_code]:
        channels[room_code].remove(username)
    leave_room(room_code)
    emit('update_users', channels[room_code], room=room_code)

# مشاركة الملفات مباشرة في الدردشة
@socketio.on('upload_file')
def handle_file_upload(data):
    """معالجة رفع الملفات."""
    room_code = data['room_code']
    username = session.get('username')
    file = data['file']
    filename = file['name']
    file_content = base64.b64decode(file['content'])

    # حفظ الملف في مجلد 'uploads'
    uploads_path = 'uploads'
    if not os.path.exists(uploads_path):
        os.makedirs(uploads_path)

    filepath = os.path.join(uploads_path, filename)
    with open(filepath, 'wb') as f:
        f.write(file_content)

    file_url = url_for('uploaded_file', filename=filename)
    emit('file_uploaded', {'username': username, 'filename': filename, 'url': file_url}, room=room_code)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """تحميل الملف المرفوع."""
    return send_from_directory('uploads', filename)

# طرد وحظر المستخدم من قبل المدير
@socketio.on('kick_user')
def kick_user(data):
    """طرد مستخدم من غرفة الدردشة."""
    if 'username' not in session or not session.get('is_admin'):
        return

    room_code = data['room_code']
    username_to_kick = data['username']

    if room_code in channels and username_to_kick in channels[room_code]:
        channels[room_code].remove(username_to_kick)
        emit('update_users', channels[room_code], room=room_code)
        emit('user_kicked', {'username': username_to_kick}, room=room_code)

@socketio.on('ban_user')
def ban_user(data):
    """حظر مستخدم من الدخول."""
    if 'username' not in session or not session.get('is_admin'):
        return

    username_to_ban = data['username']
    banned_ips.add(username_to_ban)
    save_banned_ip(username_to_ban)
    emit('user_banned', {'username': username_to_ban}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

print("god baay")
