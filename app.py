from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
import os
import requests
import socket
import threading
import time
from datetime import datetime, timedelta
import secrets
import random
import string
# Version Control
APP_VERSION = "1.0.6"
MIN_COMPATIBLE_VERSION = "1.0.0"

def generate_unique_code(length=6):
    """Generate a unique random alphanumeric code."""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))
from detection_utils import EmotionDetector
import numpy as np
import cv2
import json


def start_discovery_broadcast():
    """Broadcasts the server's presence over UDP for auto-discovery."""
    DISCOVERY_PORT = 5005
    MAGIC_MESSAGE = "EMO_TRACK_DISCOVERY"
    
    def broadcast():
        print(f"Discovery broadcast started on port {DISCOVERY_PORT}...")
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            while True:
                try:
                    # Get the current local IP
                    s_temp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    try:
                        s_temp.connect(("8.8.8.8", 80))
                        local_ip = s_temp.getsockname()[0]
                    except Exception:
                        local_ip = socket.gethostbyname(socket.gethostname())
                    finally:
                        s_temp.close()
                    
                    message = f"{MAGIC_MESSAGE}:{local_ip}:5000"
                    print(f"Discovery broadcast: {message}")
                    s.sendto(message.encode(), ('<broadcast>', DISCOVERY_PORT))
                except Exception as e:
                    print(f"Broadcast error: {e}")
                time.sleep(5)

    thread = threading.Thread(target=broadcast, daemon=True)
    thread.start()

print("Starting app...")
print("Initializing EmotionDetector...")
try:
    emotion_detector = EmotionDetector()
except Exception as e:
    print(f"Failed to initialize EmotionDetector: {e}")



app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'devsecret')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['GOOGLE_MAPS_API_KEY'] = 'AIzaSyDs0vIRVVFGpK_tFZGWpQkyRMjSAKWWdGc'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- Database Migration Hook ---
with app.app_context():
    try:
        from sqlalchemy import text
        with db.engine.connect() as conn:
            # Check and add heart_rate
            try:
                conn.execute(text('ALTER TABLE child ADD COLUMN heart_rate INTEGER DEFAULT 0'))
                conn.commit()
            except: pass
            # Check and add battery_level
            try:
                conn.execute(text('ALTER TABLE child ADD COLUMN battery_level INTEGER DEFAULT 100'))
                conn.commit()
            except: pass
            # Check and add location columns
            try:
                conn.execute(text('ALTER TABLE child ADD COLUMN current_lat FLOAT'))
                conn.commit()
            except: pass
            try:
                conn.execute(text('ALTER TABLE child ADD COLUMN current_lng FLOAT'))
                conn.commit()
            except: pass
            try:
                conn.execute(text('ALTER TABLE child ADD COLUMN last_location_update DATETIME'))
                conn.commit()
            except: pass
            # Check and add is_locked
            try:
                conn.execute(text('ALTER TABLE child ADD COLUMN is_locked BOOLEAN DEFAULT 0'))
                conn.commit()
            except: pass
            # Check and add emotion columns to location_history
            try:
                conn.execute(text('ALTER TABLE location_history ADD COLUMN emotion VARCHAR(50)'))
                conn.commit()
            except: pass
            try:
                conn.execute(text('ALTER TABLE location_history ADD COLUMN confidence FLOAT'))
                conn.commit()
            except: pass
            
        # Create all tables
        db.create_all()
    except Exception as e:
        print(f"Migration hook info: {e}")
# -------------------------------


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    children = db.relationship('Child', backref='parent', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Child(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    gender = db.Column(db.String(10), nullable=False)  # 'boy' or 'girl'
    bracelet_code = db.Column(db.String(100), unique=True, nullable=False)
    age = db.Column(db.Integer)
    diseases = db.relationship('Disease', backref='child', lazy=True, cascade='all, delete-orphan')
    medications = db.relationship('Medication', backref='child', lazy=True, cascade='all, delete-orphan')
    locations = db.relationship('Location', backref='child', lazy=True, cascade='all, delete-orphan')
    alerts = db.relationship('Alert', backref='child', lazy=True, cascade='all, delete-orphan')
    current_lat = db.Column(db.Float)
    current_lng = db.Column(db.Float)
    last_location_update = db.Column(db.DateTime)
    heart_rate = db.Column(db.Integer, default=0)
    battery_level = db.Column(db.Integer, default=100)
    is_locked = db.Column(db.Boolean, default=False)
    history = db.relationship('LocationHistory', backref='child', lazy=True, cascade='all, delete-orphan')


# Global state for live detections
latest_detections = {}

class Disease(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('child.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)


class Medication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('child.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    dosage = db.Column(db.String(100))
    frequency = db.Column(db.String(100))  # e.g., "every 8 hours"
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    duration_days = db.Column(db.Integer)  # مدة الجرعة بالأيام
    schedule_time = db.Column(db.String(50))  # e.g., "08:00"
    notes = db.Column(db.Text)


class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('child.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # 'school', 'home', 'club'
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    radius = db.Column(db.Float)  # safe zone radius
    created_at = db.Column(db.DateTime, default=datetime.now)


class LocationHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('child.id'), nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    heart_rate = db.Column(db.Integer)
    battery_level = db.Column(db.Integer)
    emotion = db.Column(db.String(50))
    confidence = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.now)


class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('child.id'), nullable=False)
    alert_type = db.Column(db.String(50))  # 'emergency', 'crying', 'danger', 'left_zone'
    description = db.Column(db.Text)
    voice_recording = db.Column(db.String(200))  # path to voice file
    timestamp = db.Column(db.DateTime, default=lambda: db.func.now())


class MedicalReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('child.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    doctor_name = db.Column(db.String(150))
    description = db.Column(db.Text)
    file_path = db.Column(db.String(300))  # path to PDF/image
    uploaded_at = db.Column(db.DateTime, default=lambda: db.func.now())
    shared_with = db.relationship('User', secondary='medical_report_shares', backref='shared_reports')


class DailyRecording(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('child.id'), nullable=False)
    recording_type = db.Column(db.String(50))  # 'video', 'photo', 'audio'
    file_path = db.Column(db.String(300))
    description = db.Column(db.Text)
    recorded_at = db.Column(db.DateTime)
    uploaded_at = db.Column(db.DateTime, default=lambda: db.func.now())
    shared_with = db.relationship('User', secondary='daily_recording_shares', backref='shared_recordings')


# Association tables for sharing
medical_report_shares = db.Table('medical_report_shares',
    db.Column('report_id', db.Integer, db.ForeignKey('medical_report.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

daily_recording_shares = db.Table('daily_recording_shares',
    db.Column('recording_id', db.Integer, db.ForeignKey('daily_recording.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


with app.app_context():
    db.create_all()


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index_en.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Support both JSON (watch) and Form (web)
        if request.is_json:
            data = request.get_json()
            username = data.get('username', '').strip()
            email = data.get('email', '').strip().lower()
            password = data.get('password', '')
            phone_number = data.get('phone_number', '').strip()
            # Watch might not send these, provide defaults
            child_name = data.get('child_name', f"{username}'s Child").strip()
            gender = data.get('gender', 'boy')
            bracelet_code = data.get('bracelet_code', f"BR-{email.split('@')[0]}").strip()
            child_age = data.get('child_age', 5)
        else:
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            phone_number = request.form.get('phone_number', '').strip()
            child_name = request.form.get('child_name', '').strip()
            gender = request.form.get('gender', 'boy')
            bracelet_code = request.form.get('bracelet_code', '').strip()
            child_age = request.form.get('child_age', type=int)
        
        if not all([username, email, password, phone_number, child_name, bracelet_code]):
            if request.is_json:
                return jsonify({'success': False, 'error': 'Missing required fields'}), 400
            flash('Please fill all fields', 'warning')
            return redirect(url_for('register'))
        
        if User.query.filter((User.username == username) | (User.email == email)).first():
            if request.is_json:
                return jsonify({'success': False, 'error': 'Username or email already exists'}), 409
            flash('Username or email already exists', 'danger')
            return redirect(url_for('register'))
        
        if Child.query.filter_by(bracelet_code=bracelet_code).first():
            if request.is_json:
                return jsonify({'success': False, 'error': 'Bracelet code already exists'}), 409
            flash('Bracelet code already exists', 'danger')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email, phone_number=phone_number)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        
        child = Child(parent_id=user.id, name=child_name, gender=gender, bracelet_code=bracelet_code, age=child_age)
        db.session.add(child)
        db.session.commit()
        
        if request.is_json:
            return jsonify({'success': True, 'message': 'Registration successful'})
            
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register_en.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if request.is_json:
            return jsonify({'success': True, 'message': 'Already authenticated'})
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        # Support both JSON (watch) and Form (web)
        if request.is_json:
            data = request.get_json()
            username = data.get('username', '').strip()
            password = data.get('password', '')
        else:
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            
        # Check username or email
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User.query.filter_by(email=username).first()
            
        if user and user.check_password(password):
            login_user(user)
            if request.is_json:
                return jsonify({'success': True, 'username': user.username})
            flash('Logged in successfully.', 'success')
            return redirect(url_for('dashboard'))
            
        if request.is_json:
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        flash('Invalid credentials', 'danger')
    return render_template('login_new.html')


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user = User.query.filter_by(email=email).first()
        if user:
            # Generate reset token
            s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
            token = s.dumps(user.email, salt='password-reset')
            
            reset_link = url_for('reset_password', token=token, _external=True)
            
            # في الإنتاج، يجب إرسال الإيميل هنا
            # لكن حالياً سنعرض الـ link مباشرة
            flash(f'Reset link: {reset_link}', 'info')
            print(f"Reset link for {user.email}: {reset_link}")
        
        flash('If email exists, reset link has been sent.', 'success')
        return redirect(url_for('login'))
    return render_template('forgot_password_en.html')


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        email = s.loads(token, salt='password-reset', max_age=3600)
    except:
        flash('Reset link is invalid or expired', 'danger')
        return redirect(url_for('login'))
    
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')
        
        if password != password_confirm:
            flash('Passwords do not match', 'warning')
            return redirect(url_for('reset_password', token=token))
        
        if len(password) < 6:
            flash('Password must be at least 6 characters', 'warning')
            return redirect(url_for('reset_password', token=token))
        
        user.set_password(password)
        db.session.commit()
        flash('Password reset successfully. Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('reset_password_en.html', token=token, email=email)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    active_child_id = request.args.get('child_id', default=None, type=int)
    if active_child_id:
        child = Child.query.get_or_404(active_child_id)
        if child.parent_id != current_user.id:
            flash('Unauthorized', 'danger')
            return redirect(url_for('dashboard'))
        active_child = child
    else:
        active_child = current_user.children[0] if current_user.children else None
    
    recent_recordings = []
    medical_reports = []
    recent_alerts = []
    if active_child:
        recent_recordings = DailyRecording.query.filter_by(child_id=active_child.id).order_by(DailyRecording.uploaded_at.desc()).limit(3).all()
        medical_reports = MedicalReport.query.filter_by(child_id=active_child.id).order_by(MedicalReport.uploaded_at.desc()).limit(3).all()
        recent_alerts = Alert.query.filter_by(child_id=active_child.id).order_by(Alert.timestamp.desc()).limit(5).all()
        history = LocationHistory.query.filter_by(child_id=active_child.id).order_by(LocationHistory.timestamp.desc()).limit(50).all()

    return render_template(
        'dashboard_en.html',
        active_child=active_child,
        children=current_user.children,
        recent_recordings=recent_recordings,
        medical_reports=medical_reports,
        recent_alerts=recent_alerts,
        history=history if active_child else []
    )


@app.route('/add-child', methods=['GET', 'POST'])
@login_required
def add_child():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        gender = request.form.get('gender', 'boy')
        age = request.form.get('age', type=int)
        
        # Auto-generate a unique code if not provided
        bracelet_code = request.form.get('bracelet_code', '').strip()
        if not bracelet_code:
            while True:
                bracelet_code = f"CG-{generate_unique_code(4)}"
                if not Child.query.filter_by(bracelet_code=bracelet_code).first():
                    break
        
        if not name:
            flash('Please enter child name', 'warning')
            return redirect(url_for('add_child'))
        
        if Child.query.filter_by(bracelet_code=bracelet_code).first():
            flash('Bracelet code already exists', 'danger')
            return redirect(url_for('add_child'))
        
        child = Child(parent_id=current_user.id, name=name, gender=gender, bracelet_code=bracelet_code, age=age)
        db.session.add(child)
        db.session.commit()
        flash(f'Child added successfully! Bracelet Code: {bracelet_code}', 'success')
        return redirect(url_for('dashboard', child_id=child.id))
    
    return render_template('add_child_en.html')


@app.route('/child/<int:child_id>/medical', methods=['GET', 'POST'])
@login_required
def child_medical(child_id):
    child = Child.query.get_or_404(child_id)
    if child.parent_id != current_user.id:
        flash('Unauthorized', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add_disease':
            disease_name = request.form.get('disease_name', '').strip()
            description = request.form.get('description', '').strip()
            if disease_name:
                disease = Disease(child_id=child.id, name=disease_name, description=description, created_at=datetime.now())
                db.session.add(disease)
                db.session.commit()
                flash('Disease added successfully', 'success')
            else:
                flash('Please enter disease name', 'warning')
        elif action == 'delete_disease':
            disease_id = request.form.get('disease_id', type=int)
            disease = Disease.query.get(disease_id)
            if disease and disease.child_id == child.id:
                db.session.delete(disease)
                db.session.commit()
                flash('Disease deleted', 'success')
        elif action == 'add_medication':
            med_name = request.form.get('med_name', '').strip()
            dosage = request.form.get('dosage', '').strip()
            frequency = request.form.get('frequency', '').strip()
            duration_days = request.form.get('duration_days', type=int)
            schedule_time = request.form.get('schedule_time', '').strip()
            if med_name:
                medication = Medication(
                    child_id=child.id, 
                    name=med_name, 
                    dosage=dosage, 
                    frequency=frequency, 
                    duration_days=duration_days,
                    schedule_time=schedule_time
                )
                db.session.add(medication)
                db.session.commit()
                flash('Medication added successfully', 'success')
            else:
                flash('Please enter medication name', 'warning')
        elif action == 'delete_medication':
            med_id = request.form.get('med_id', type=int)
            medication = Medication.query.get(med_id)
            if medication and medication.child_id == child.id:
                db.session.delete(medication)
                db.session.commit()
                flash('Medication deleted', 'success')
    
    return render_template('child_medical_en.html', child=child)


@app.route('/child/<int:child_id>/locations', methods=['GET', 'POST'])
@login_required
def child_locations(child_id):
    child = Child.query.get_or_404(child_id)
    if child.parent_id != current_user.id:
        flash('Unauthorized', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        action = request.form.get('action', 'add_location')
        if action == 'delete_location':
            location_id = request.form.get('location_id', type=int)
            location = Location.query.get(location_id)
            if location and location.child_id == child.id:
                db.session.delete(location)
                db.session.commit()
                flash('Safe zone deleted', 'success')
            return redirect(url_for('child_locations', child_id=child.id))

        location_name = (request.form.get('location_name') or request.form.get('name') or '').strip()
        latitude = request.form.get('latitude', type=float)
        longitude = request.form.get('longitude', type=float)
        radius = request.form.get('radius', default=200, type=float)
        
        if location_name and latitude is not None and longitude is not None:
            location = Location(
                child_id=child.id, 
                name=location_name, 
                latitude=latitude, 
                longitude=longitude, 
                radius=radius,
                created_at=datetime.now()
            )
            db.session.add(location)
            db.session.commit()
            flash('Safe zone added', 'success')
            return redirect(url_for('child_locations', child_id=child.id))

        flash('Please fill all required fields', 'warning')
    
    google_maps_api_key = app.config['GOOGLE_MAPS_API_KEY']
    
    # Convert locations to serializable format for JS
    locations_data = []
    for loc in child.locations:
        locations_data.append({
            'name': loc.name,
            'latitude': loc.latitude,
            'longitude': loc.longitude,
            'radius': loc.radius
        })
        
    return render_template('child_locations_en.html', 
                         child=child, 
                         locations_json=locations_data,
                         google_maps_api_key=google_maps_api_key)


@app.route('/author/<int:user_id>')
def author(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('author.html', author=user)


# API Endpoints للتطبيق الموبايل
@app.route('/api/update-location', methods=['POST'])
@login_required
def api_update_location():
    """تحديث موقع الطفل الحالي"""
    data = request.get_json()
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    
    # يمكن حفظ آخر موقع معروف للطفل هنا
    return jsonify({
        'success': True,
        'message': 'Location updated',
        'latitude': latitude,
        'longitude': longitude
    })


@app.route('/api/children', methods=['GET'])
@login_required
def api_get_children():
    """الحصول على قائمة الأطفال"""
    children = current_user.children
    return jsonify([{
        'id': child.id,
        'name': child.name,
        'gender': child.gender,
        'age': child.age,
        'bracelet_code': child.bracelet_code
    } for child in children])


@app.route('/api/child/<int:child_id>/status', methods=['GET'])
@login_required
def api_child_status(child_id):
    """الحصول على حالة الطفل الحالية"""
    child = Child.query.get_or_404(child_id)
    if child.parent_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify({
        'id': child.id,
        'name': child.name,
        'diseases': [{'id': d.id, 'name': d.name} for d in child.diseases],
        'medications': [{'id': m.id, 'name': m.name, 'time': m.schedule_time} for m in child.medications],
        'locations': [{'id': l.id, 'name': l.name, 'lat': l.latitude, 'lng': l.longitude} for l in child.locations]
    })


@app.route('/api/notifications', methods=['GET'])
@login_required
def api_get_notifications():
    """الحصول على الإشعارات"""
    # يمكن إضافة نموذج إشعارات لاحقاً
    return jsonify([])


@app.route('/api/detect-emotion', methods=['POST'])
def api_detect_emotion():
    """Receive image from watch and return detected emotion"""
    if emotion_detector is None:
        return jsonify({'success': False, 'error': 'Emotion detector not initialized'}), 500
        
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': 'No image part in request'}), 400
        
    file = request.files['image']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No selected image'}), 400
        
    try:
        image_bytes = file.read()
        
        # Save latest image for the web dashboard to display
        try:
            with open("static/latest_capture.jpg", "wb") as f:
                f.write(image_bytes)
        except Exception as e:
            print(f"Error saving latest capture: {e}")
            
        result = emotion_detector.detect_emotion(image_bytes)
        
        # Update live status
        if result.get('success'):
            emotion_data = result['data']
            # We use a simple strategy: latest detection is stored
            # Ideally we would map bracelet_code to child_id
            detection_payload = {
                'emotion': emotion_data['emotion'],
                'confidence': float(emotion_data['confidence']),
                'timestamp': datetime.now().strftime("%H:%M:%S"),
                'received_at': datetime.now().isoformat(timespec='seconds'),
                'source': request.form.get('source', 'watch-app')
            }
            latest_detections['global'] = detection_payload

            bracelet_code = request.form.get('bracelet_code')
            child_id = request.form.get('child_id')
            if bracelet_code:
                child = Child.query.filter_by(bracelet_code=bracelet_code).first()
                if child:
                    latest_detections[str(child.id)] = detection_payload
                    # Log to history
                    history_entry = LocationHistory(
                        child_id=child.id,
                        latitude=child.current_lat,
                        longitude=child.current_lng,
                        heart_rate=child.heart_rate,
                        battery_level=child.battery_level,
                        emotion=emotion_data['emotion'],
                        confidence=float(emotion_data['confidence'])
                    )
                    db.session.add(history_entry)
                    db.session.commit()
            elif child_id:
                latest_detections[str(child_id)] = detection_payload
                child = Child.query.get(child_id)
                if child:
                    # Log to history
                    history_entry = LocationHistory(
                        child_id=child.id,
                        latitude=child.current_lat,
                        longitude=child.current_lng,
                        heart_rate=child.heart_rate,
                        battery_level=child.battery_level,
                        emotion=emotion_data['emotion'],
                        confidence=float(emotion_data['confidence'])
                    )
                    db.session.add(history_entry)
                    db.session.commit()
            
            # POP-UP: Show detection on server desktop
            try:
                nparr = np.frombuffer(image_bytes, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if img is not None:
                    # Draw bbox
                    x1, y1, x2, y2 = emotion_data['bbox']
                    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    label = f"{emotion_data['emotion']} ({emotion_data['confidence']:.1f}%)"
                    cv2.putText(img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                    
                    cv2.imshow("EMO_TRACK Live Detection", img)
                    cv2.waitKey(1) # Refresh window
            except Exception as e:
                print(f"Error showing pop-up: {e}")

        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/live-status', methods=['GET'])
def api_live_status():
    """Get the latest detected emotion and watch metrics for the web dashboard."""
    child_id_raw = request.args.get('child_id')
    child_id = int(child_id_raw) if child_id_raw and child_id_raw.isdigit() else None
    
    data = latest_detections.get(str(child_id)) if child_id else None
    data = data or latest_detections.get('global')

    response = {
        'emotion': 'Unknown',
        'confidence': 0,
        'timestamp': '--:--:--',
        'received_at': None,
        'is_live': False,
        'last_seen_seconds': None,
        'source': 'watch-app',
        'heart_rate': '--',
        'battery_level': '--'
    }

    if data:
        last_seen_seconds = None
        is_live = False
        received_at = data.get('received_at')
        if received_at:
            try:
                last_seen = datetime.fromisoformat(received_at)
                last_seen_seconds = int((datetime.now() - last_seen).total_seconds())
                is_live = last_seen_seconds <= 15
            except ValueError:
                pass

        response.update(data)
        response['is_live'] = is_live
        response['last_seen_seconds'] = last_seen_seconds

    if child_id:
        child = Child.query.get(child_id)
        if child:
            # Always return numbers if they exist, otherwise '--'
            response['heart_rate'] = child.heart_rate if child.heart_rate is not None else '--'
            response['battery_level'] = child.battery_level if child.battery_level is not None else '--'
            response['current_lat'] = child.current_lat
            response['current_lng'] = child.current_lng
            response['name'] = child.name
            
    return jsonify(response)


@app.route('/api/logs', methods=['POST'])
def api_logs():
    """Receive logs from the watch for debugging."""
    data = request.json
    log_msg = data.get('log', '')
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("watch_logs.txt", "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {log_msg}\n")
    return jsonify({'success': True})


# Update Cache
GITHUB_REPO = "simplehima/EMO_TRACK"
last_github_check = None
cached_github_version = APP_VERSION

@app.route('/api/app-version', methods=['GET'])
def api_app_version():
    """Return the latest available version information, checking GitHub if needed."""
    global last_github_check, cached_github_version
    
    # Check GitHub every 1 hour
    now = datetime.now()
    if last_github_check is None or (now - last_github_check) > timedelta(hours=1):
        try:
            response = requests.get(f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest", timeout=5)
            if response.status_code == 200:
                data = response.json()
                # Remove 'v' prefix if present (e.g. v1.0.6 -> 1.0.6)
                tag = data.get('tag_name', APP_VERSION).replace('v', '')
                cached_github_version = tag
                last_github_check = now
        except Exception as e:
            print(f"GitHub version check failed: {e}")
            # Keep using local APP_VERSION as fallback if first check fails
    
    return jsonify({
        'version': cached_github_version,
        'local_version': APP_VERSION,
        'min_compatible': MIN_COMPATIBLE_VERSION,
        'build_number': 5,
        'release_date': datetime.now().strftime('%Y-%m-%d'),
        'github_repo': GITHUB_REPO
    })


@app.route('/api/latest-apk', methods=['GET'])
def api_latest_apk():
    """Serve the latest built APK file."""
    apk_dir = os.path.join(os.getcwd(), 'build', 'app', 'outputs', 'flutter-apk')
    # Use the split APK for the watch
    target_apk = 'app-armeabi-v7a-release.apk'
    if not os.path.exists(os.path.join(apk_dir, target_apk)):
        return jsonify({'error': 'APK not found on server'}), 404
    return send_from_directory(apk_dir, target_apk, as_attachment=True, mimetype='application/vnd.android.package-archive')


@app.route('/child/<int:child_id>/medical-reports', methods=['GET', 'POST'])
@login_required
def medical_reports(child_id):
    child = Child.query.get_or_404(child_id)
    if child.parent_id != current_user.id:
        flash('Unauthorized', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        doctor_name = request.form.get('doctor_name', '').strip()
        description = request.form.get('description', '').strip()
        
        file = request.files.get('file')
        file_path = None
        
        if file and file.filename:
            filename = f"report_{child_id}_{datetime.now().timestamp()}.pdf"
            file_path = f"uploads/reports/{filename}"
            os.makedirs('uploads/reports', exist_ok=True)
            file.save(os.path.join('static', file_path))
        
        report = MedicalReport(
            child_id=child_id,
            title=title,
            doctor_name=doctor_name,
            description=description,
            file_path=file_path
        )
        db.session.add(report)
        db.session.commit()
        flash('Medical report uploaded successfully', 'success')
        return redirect(url_for('medical_reports', child_id=child_id))
    
    reports = MedicalReport.query.filter_by(child_id=child_id).order_by(MedicalReport.uploaded_at.desc()).all()
    return render_template('medical_reports_en.html', child=child, reports=reports)


@app.route('/child/<int:child_id>/camera')
@login_required
def camera(child_id):
    child = Child.query.get_or_404(child_id)
    if child.parent_id != current_user.id:
        flash('Unauthorized', 'danger')
        return redirect(url_for('dashboard'))
    
    return render_template('camera_en.html', child=child)


@app.route('/child/<int:child_id>/daily-recordings', methods=['GET', 'POST'])
@login_required
def daily_recordings(child_id):
    child = Child.query.get_or_404(child_id)
    if child.parent_id != current_user.id:
        flash('Unauthorized', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # Logging for debugging
        with open('recordings_debug.txt', 'a') as f:
            f.write(f"[{datetime.now()}] POST to daily_recordings. Action: {request.form.get('action')}, ID: {request.form.get('recording_id')}\n")
            
        try:
            action = request.form.get('action')
            if action == 'delete_recording':
                recording_id = request.form.get('recording_id', type=int)
                recording = db.session.get(DailyRecording, recording_id)
                if recording and recording.child_id == child.id:
                    if recording.file_path:
                        full_path = os.path.join('static', recording.file_path)
                        if os.path.exists(full_path):
                            os.remove(full_path)
                    db.session.delete(recording)
                    db.session.commit()
                    flash('Recording deleted successfully', 'success')
                else:
                    flash('Recording not found or unauthorized', 'danger')
                return redirect(url_for('daily_recordings', child_id=child.id))

            recording_type = request.form.get('recording_type', 'video')
            description = request.form.get('description', '').strip()
            file = request.files.get('file')
            
            # Validate file exists
            if not file or file.filename == '':
                return jsonify({'error': 'No file provided'}), 400
            
            # Create uploads directory
            upload_dir = os.path.join('static', 'uploads', 'recordings')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generate filename with proper extension
            ext = os.path.splitext(file.filename)[1].lower() or '.webm'
            timestamp = int(datetime.now().timestamp() * 1000)  # Milliseconds for uniqueness
            filename = f"recording_{child_id}_{timestamp}{ext}"
            file_path = f"uploads/recordings/{filename}"
            full_path = os.path.join('static', file_path)
            
            # Save file
            file.save(full_path)
            
            # Verify file was saved and has content
            if not os.path.exists(full_path) or os.path.getsize(full_path) == 0:
                return jsonify({'error': 'File save failed'}), 500
            
            # Create recording entry in database
            recording = DailyRecording(
                child_id=child_id,
                recording_type=recording_type,
                description=description,
                file_path=file_path,
                recorded_at=datetime.now(),
                uploaded_at=datetime.now()
            )
            db.session.add(recording)
            db.session.commit()
            
            # Return redirect for normal form submission
            if request.headers.get('Accept') == 'application/json':
                return jsonify({'success': True, 'message': 'Recording uploaded successfully'}), 200
            else:
                flash('✅ Recording uploaded successfully!', 'success')
                return redirect(url_for('daily_recordings', child_id=child_id))
                
        except Exception as e:
            db.session.rollback()
            error_msg = f'Error uploading recording: {str(e)}'
            if request.headers.get('Accept') == 'application/json':
                return jsonify({'error': error_msg}), 500
            else:
                flash(error_msg, 'danger')
                return redirect(url_for('daily_recordings', child_id=child_id))
    
    recordings = DailyRecording.query.filter_by(child_id=child_id).order_by(DailyRecording.uploaded_at.desc()).all()
    return render_template('daily_recordings_en.html', child=child, recordings=recordings)


@app.route('/report/<int:report_id>/share', methods=['POST'])
@login_required
def share_medical_report(report_id):
    report = MedicalReport.query.get_or_404(report_id)
    if report.child.parent_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    user_id = request.form.get('user_id', type=int)
    user = User.query.get(user_id)
    
    if user and user not in report.shared_with:
        report.shared_with.append(user)
        db.session.commit()
        flash(f'Report shared with {user.username}', 'success')
    
    return redirect(url_for('medical_reports', child_id=report.child_id))


@app.route('/recording/<int:recording_id>/share', methods=['POST'])
@login_required
def share_recording(recording_id):
    recording = DailyRecording.query.get_or_404(recording_id)
    if recording.child.parent_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    user_id = request.form.get('user_id', type=int)
    user = User.query.get(user_id)
    
    if user and user not in recording.shared_with:
        recording.shared_with.append(user)
        db.session.commit()
        flash(f'Recording shared with {user.username}', 'success')
    
    return redirect(url_for('daily_recordings', child_id=recording.child_id))


@app.route('/api/toggle-lock/<int:child_id>', methods=['POST'])
@login_required
def toggle_lock(child_id):
    child = Child.query.get_or_404(child_id)
    if child.parent_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    child.is_locked = not child.is_locked
    db.session.commit()
    return jsonify({'success': True, 'is_locked': child.is_locked})


@app.route('/api/watch/location', methods=['POST'])
def watch_location():
    """Receive location and status from the watch."""
    data = request.get_json()
    bracelet_code = data.get('bracelet_code')
    lat = data.get('latitude')
    lng = data.get('longitude')
    
    print(f"Received telemetry from watch: {bracelet_code} (Lat: {lat}, Lng: {lng}, HR: {data.get('heart_rate')}, Bat: {data.get('battery_level')})")
    
    if not bracelet_code:
        return jsonify({'error': 'Missing bracelet_code'}), 400
        
    child = Child.query.filter_by(bracelet_code=bracelet_code).first()
    if not child:
        print(f"Error: No child found with bracelet code {bracelet_code}")
        return jsonify({'error': 'Child not found'}), 404
        
    child.current_lat = lat
    child.current_lng = lng
    child.heart_rate = data.get('heart_rate', child.heart_rate)
    child.battery_level = data.get('battery_level', child.battery_level)
    child.last_location_update = datetime.now()
    
    # Log to history
    history_entry = LocationHistory(
        child_id=child.id,
        latitude=lat,
        longitude=lng,
        heart_rate=child.heart_rate,
        battery_level=child.battery_level
    )
    db.session.add(history_entry)
    
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'message': 'Watch data updated',
        'is_locked': child.is_locked
    })


if __name__ == '__main__':
    print("--- Starting Discovery Broadcast Thread ---")
    start_discovery_broadcast()
    print("--- Starting Flask Server ---")
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
