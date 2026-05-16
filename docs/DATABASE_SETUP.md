# 🗄️ SQLite Database Setup Guide

## ✅ What's Already Done

Your project already has:
- ✅ SQLite database at `instance/site.db`
- ✅ Flask-SQLAlchemy configured in `app.py`
- ✅ All database models defined (User, Child, Disease, Medication, Location, Alert)
- ✅ `requirements.txt` with all dependencies

## 🚀 Quick Start

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Initialize Database with Sample Data
```bash
python init_db.py
```

This will:
- Create all database tables
- Add a demo parent user (username: `demo_parent`, password: `password123`)
- Add 2 sample children (Ahmed - boy, Fatima - girl)
- Add medical records, medications, and safe zones

### Step 3: Check Database Status
```bash
python check_db.py
```

This shows you:
- All tables in the database
- Number of records in each table
- Column names and types

### Step 4: Run the Flask App
```bash
python app.py
```

Then open: http://127.0.0.1:5000

---

## 📊 Database Schema

### Users Table
- `id` - Primary key
- `username` - Unique username
- `email` - Unique email
- `password_hash` - Hashed password
- `phone_number` - Parent's phone

### Children Table
- `id` - Primary key
- `parent_id` - Foreign key to User
- `name` - Child's name
- `gender` - 'boy' or 'girl'
- `bracelet_code` - Unique bracelet ID
- `age` - Child's age

### Diseases Table
- `id` - Primary key
- `child_id` - Foreign key to Child
- `name` - Disease name
- `description` - Disease details
- `created_at` - Timestamp

### Medications Table
- `id` - Primary key
- `child_id` - Foreign key to Child
- `name` - Medication name
- `dosage` - Dosage amount
- `frequency` - How often (e.g., "twice daily")
- `schedule_time` - Time to take (e.g., "08:00")
- `start_date` - Start date
- `end_date` - End date
- `notes` - Additional notes

### Locations Table
- `id` - Primary key
- `child_id` - Foreign key to Child
- `name` - Location name (Home, School, Club)
- `latitude` - GPS latitude
- `longitude` - GPS longitude
- `radius` - Safe zone radius in meters
- `created_at` - Timestamp

### Alerts Table
- `id` - Primary key
- `child_id` - Foreign key to Child
- `alert_type` - Type of alert (emergency, crying, danger, left_zone)
- `description` - Alert details
- `voice_recording` - Path to voice file
- `timestamp` - When alert was triggered

---

## 🔍 Verify Installation

Run these commands to verify everything is working:

```bash
# Check Python version
python --version

# Check Flask is installed
python -c "import flask; print(f'Flask {flask.__version__}')"

# Check database
python check_db.py

# Start the app
python app.py
```

---

## 📝 Test Credentials

After running `init_db.py`, use these to log in:
- **Username**: `demo_parent`
- **Password**: `password123`
- **Children**: Ahmed (boy), Fatima (girl)

---

## 🛠️ SQLite Tools

### View Database with SQLite3 Command Line:
```bash
sqlite3 instance/site.db
```

Then in SQLite:
```sql
.tables                           -- Show all tables
SELECT * FROM user;              -- Show all users
SELECT * FROM child;             -- Show all children
PRAGMA table_info(child);         -- Show child table structure
.quit                             -- Exit SQLite
```

### View Database with GUI:
Download **DB Browser for SQLite**:
- Windows: https://sqlitebrowser.org/dl/
- Open `instance/site.db`
- Browse tables visually

---

## ⚠️ Important Notes

1. **Database Location**: `instance/site.db` - this file is where all data is stored
2. **Backup**: Keep backups of `instance/site.db`
3. **Reset Database**: Delete `instance/site.db` to start fresh, then run `init_db.py`
4. **Never commit to Git**: Add `instance/` to `.gitignore` (already done if using Flask structure)

---

## 📞 Support

If you get errors:
1. Make sure all packages are installed: `pip install -r requirements.txt`
2. Check if Python 3.8+ is installed: `python --version`
3. Verify the `app.py` file exists
4. Run `python check_db.py` to diagnose database issues
