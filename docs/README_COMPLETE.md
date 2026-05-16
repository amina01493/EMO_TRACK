# 👶 Child Guardian - Parental Monitoring App

A Flask-based web application for parents to monitor their children's safety, health, and location using smartwatch bracelets.

## ✨ Features

- **👤 User Authentication**: Parent registration & login with phone number
- **👧👦 Multi-Child Management**: Add and monitor multiple children
- **💊 Medical Records**: Track diseases, medications, and schedules
- **📍 Safe Zones**: Define and monitor safe locations (home, school, club)
- **📊 Real-time Status**: Monitor heart rate, temperature, location, battery
- **🚨 Emergency Alerts**: Alert system for emergencies and zone violations
- **📹 Live Camera**: Access to child's smartwatch camera feed
- **📱 Mobile-First Design**: Responsive design with phone frame mockup
- **🎨 Dynamic Color Theme**: Blue for boys, Pink for girls
- **📑 Tabbed Dashboard**: Organized interface with 4 main sections

## 🚀 Quick Start

### Option 1: Automated Setup (Windows)
Double-click `setup_and_run.bat` - it will:
- Create virtual environment
- Install dependencies
- Initialize database
- Start the Flask app

### Option 2: Manual Setup

**Step 1: Install Dependencies**
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1    # On Windows PowerShell
pip install -r requirements.txt
```

**Step 2: Initialize Database**
```bash
python init_db.py
```

**Step 3: Run the App**
```bash
python app.py
```

Open: **http://127.0.0.1:5000**

## 🔑 Test Credentials

After initialization, log in with:
- **Username**: `demo_parent`
- **Password**: `password123`
- **Children**: Ahmed (boy 👦), Fatima (girl 👧)

## 📋 Database Commands

### Check Database Status
```bash
python check_db.py
```

### Reset Database (Delete & Recreate)
```bash
python reset_db.py
```

### View Database (SQLite CLI)
```bash
sqlite3 instance/site.db
.tables                 # Show tables
SELECT * FROM user;     # Show users
SELECT * FROM child;    # Show children
.quit                   # Exit
```

## 📁 Project Structure

```
.
├── app.py                      # Flask app with models & routes
├── init_db.py                  # Initialize database with sample data
├── check_db.py                 # Check database status
├── reset_db.py                 # Reset database
├── setup_and_run.bat           # Windows setup script
├── requirements.txt            # Python dependencies
├── instance/
│   └── site.db                 # SQLite database
├── templates/
│   ├── base.html               # Base template with navbar
│   ├── index.html              # Home page
│   ├── register.html           # Registration form
│   ├── login.html              # Login form
│   ├── dashboard.html          # Main dashboard (tabbed interface)
│   ├── add_child.html          # Add child form
│   ├── child_medical.html      # Medical records management
│   ├── child_locations.html    # Safe zones management
│   └── author.html             # Author profile page
└── static/
    └── style.css               # Responsive mobile-first styling
```

## 🗄️ Database Schema

### Users
- `id`, `username`, `email`, `password_hash`, `phone_number`

### Children
- `id`, `parent_id`, `name`, `gender`, `bracelet_code`, `age`

### Medical Records
- **Diseases**: `id`, `child_id`, `name`, `description`, `created_at`
- **Medications**: `id`, `child_id`, `name`, `dosage`, `frequency`, `schedule_time`, `start_date`, `end_date`, `notes`

### Locations (Safe Zones)
- `id`, `child_id`, `name`, `latitude`, `longitude`, `radius`, `created_at`

### Alerts
- `id`, `child_id`, `alert_type`, `description`, `voice_recording`, `timestamp`

## 🌐 Routes

| Route | Method | Purpose |
|-------|--------|---------|
| `/` | GET | Home page |
| `/register` | GET/POST | User registration |
| `/login` | GET/POST | User login |
| `/logout` | GET | User logout |
| `/dashboard` | GET | Main dashboard with child selector |
| `/add-child` | GET/POST | Add new child |
| `/child/<id>/medical` | GET/POST | Manage medical records |
| `/child/<id>/locations` | GET/POST | Manage safe zones |
| `/author/<id>` | GET | View parent profile |

## 🎨 Dashboard Features

The dashboard uses a **tabbed interface** with 4 sections:

### 1. 🛡️ Status Tab
- Real-time monitoring
- Live location, heart rate, temperature, battery
- Emergency alert button
- Live camera access

### 2. 🏥 Medical Tab
- Diseases and medications list
- Schedule times
- Edit medical info

### 3. 📍 Zones Tab
- Safe zones map placeholder
- List of configured zones
- Manage zones link

### 4. 📊 Activity Tab
- Daily activity summary
- Video surveillance player
- Alert logs

## 💻 Technologies Used

- **Backend**: Flask 2.x, Flask-SQLAlchemy, Flask-Login
- **Database**: SQLite3
- **Frontend**: Bootstrap 5.3.0, HTML5, CSS3
- **Authentication**: Werkzeug (password hashing)
- **Server**: Python 3.8+

## 🎨 Styling Highlights

- **Mobile-First Design**: Optimized for mobile phones
- **Phone Frame Mockup**: 420px width with CSS notch
- **Dynamic Colors**: 
  - Blue (#0d6efd) for boys
  - Pink (#ec4899) for girls
- **Gradient Backgrounds**: Purple gradient (#667eea → #764ba2)
- **Smooth Animations**: Tab transitions and hover effects
- **Responsive Grid**: Adapts to different screen sizes

## ⚙️ Configuration

Edit `app.py` to modify:

```python
app.config['SECRET_KEY'] = 'devsecret'  # Change for production!
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.run(debug=True)  # Set to False in production
```

## 🔒 Security Notes

⚠️ **This is a development version!**

For production:
1. Change `SECRET_KEY` to a secure random value
2. Set `debug=False` in `app.run()`
3. Use a proper database (PostgreSQL, MySQL)
4. Add HTTPS/SSL certificates
5. Implement proper password reset functionality
6. Add email verification
7. Add rate limiting for login attempts
8. Implement role-based access control (RBAC)

## 🆘 Troubleshooting

### Database errors?
```bash
python reset_db.py  # Recreate from scratch
```

### Port already in use?
```bash
python app.py --port 5001  # Use different port
```

### Module not found errors?
```bash
pip install -r requirements.txt --upgrade
```

### Colors not changing between children?
- Refresh the page after switching children
- Check browser console for JavaScript errors
- Try clearing browser cache

## 📞 Support

For issues or questions, check:
- `DATABASE_SETUP.md` - Detailed database setup guide
- `app.py` - Source code with inline documentation
- `check_db.py` - Database diagnostics tool

## 📝 License

Development version - use for learning purposes only.

---

**Last Updated**: November 2025
**Version**: 1.0.0
