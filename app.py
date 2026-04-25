from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
import os
from datetime import datetime, timedelta
import secrets

print("Starting app...")

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'devsecret')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['GOOGLE_MAPS_API_KEY'] = os.environ.get('GOOGLE_MAPS_API_KEY', 'YOUR_GOOGLE_MAPS_API_KEY')

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


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


class Disease(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('child.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: db.func.now())


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
    created_at = db.Column(db.DateTime, default=lambda: db.func.now())


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
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        phone_number = request.form.get('phone_number', '').strip()
        child_name = request.form.get('child_name', '').strip()
        gender = request.form.get('gender', 'boy')
        bracelet_code = request.form.get('bracelet_code', '').strip()
        child_age = request.form.get('child_age', type=int)
        
        if not all([username, email, password, phone_number, child_name, bracelet_code]):
            flash('Please fill all fields', 'warning')
            return redirect(url_for('register'))
        
        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash('Username or email already exists', 'danger')
            return redirect(url_for('register'))
        
        if Child.query.filter_by(bracelet_code=bracelet_code).first():
            flash('Bracelet code already exists', 'danger')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email, phone_number=phone_number)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        
        child = Child(parent_id=user.id, name=child_name, gender=gender, bracelet_code=bracelet_code, age=child_age)
        db.session.add(child)
        db.session.commit()
        
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register_en.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('dashboard'))
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
    
    return render_template('dashboard_en.html', active_child=active_child, children=current_user.children)


@app.route('/add-child', methods=['GET', 'POST'])
@login_required
def add_child():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        gender = request.form.get('gender', 'boy')
        bracelet_code = request.form.get('bracelet_code', '').strip()
        age = request.form.get('age', type=int)
        
        if not all([name, bracelet_code]):
            flash('Please fill required fields', 'warning')
            return redirect(url_for('add_child'))
        
        if Child.query.filter_by(bracelet_code=bracelet_code).first():
            flash('Bracelet code already exists', 'danger')
            return redirect(url_for('add_child'))
        
        child = Child(parent_id=current_user.id, name=name, gender=gender, bracelet_code=bracelet_code, age=age)
        db.session.add(child)
        db.session.commit()
        flash('Child added successfully', 'success')
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
        location_name = request.form.get('location_name', '').strip()
        latitude = request.form.get('latitude', type=float)
        longitude = request.form.get('longitude', type=float)
        radius = request.form.get('radius', default=200, type=float)
        
        if location_name and latitude and longitude:
            location = Location(child_id=child.id, name=location_name, latitude=latitude, longitude=longitude, radius=radius)
            db.session.add(location)
            db.session.commit()
            flash('Safe zone added', 'success')
        else:
            flash('Please fill all required fields', 'warning')
    
    google_maps_api_key = app.config['GOOGLE_MAPS_API_KEY']
    return render_template('child_locations_en.html', child=child, google_maps_api_key=google_maps_api_key)


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
        try:
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


if __name__ == '__main__':
    app.run(debug=True)
