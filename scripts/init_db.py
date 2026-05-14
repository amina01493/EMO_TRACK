#!/usr/bin/env python3
"""
Database Initialization Script
Creates all tables and populates with sample data
"""

from app import app, db, User, Child, Disease, Medication, Location, Alert
from datetime import datetime, timedelta

def init_db():
    """Initialize database with tables and sample data"""
    with app.app_context():
        # Drop all tables if they exist (optional - remove for production)
        print("🗑️  Clearing existing database...")
        db.drop_all()
        
        # Create all tables
        print("📊 Creating tables...")
        db.create_all()
        print("✅ Tables created successfully!")
        
        # Create sample parent user
        print("\n👨‍👩‍👧 Creating sample data...")
        parent = User(
            username='demo_parent',
            email='parent@example.com',
            phone_number='+201012345678'
        )
        parent.set_password('password123')
        db.session.add(parent)
        db.session.flush()
        
        # Create sample children
        child1 = Child(
            parent_id=parent.id,
            name='Ahmed',
            gender='boy',
            bracelet_code='BRACELET001',
            age=8
        )
        
        child2 = Child(
            parent_id=parent.id,
            name='Fatima',
            gender='girl',
            bracelet_code='BRACELET002',
            age=6
        )
        
        db.session.add_all([child1, child2])
        db.session.flush()
        
        # Add diseases to Ahmed
        disease1 = Disease(
            child_id=child1.id,
            name='Asthma',
            description='Mild seasonal asthma',
            created_at=datetime.now()
        )
        db.session.add(disease1)
        db.session.flush()
        
        # Add medications to Ahmed
        med1 = Medication(
            child_id=child1.id,
            name='Albuterol',
            dosage='2 puffs',
            frequency='As needed',
            schedule_time='08:00',
            notes='Use before exercise'
        )
        
        med2 = Medication(
            child_id=child1.id,
            name='Vitamins',
            dosage='1 tablet',
            frequency='Once daily',
            schedule_time='09:00',
            notes='With breakfast'
        )
        
        db.session.add_all([med1, med2])
        db.session.flush()
        
        # Add safe locations
        loc1 = Location(
            child_id=child1.id,
            name='Home',
            latitude=30.0444,
            longitude=31.2357,
            radius=100,
            created_at=datetime.now()
        )
        
        loc2 = Location(
            child_id=child1.id,
            name='School',
            latitude=30.0500,
            longitude=31.2400,
            radius=200,
            created_at=datetime.now()
        )
        
        loc3 = Location(
            child_id=child1.id,
            name='Club',
            latitude=30.0600,
            longitude=31.2500,
            radius=150,
            created_at=datetime.now()
        )
        
        # Add same locations for Fatima
        loc4 = Location(
            child_id=child2.id,
            name='Home',
            latitude=30.0444,
            longitude=31.2357,
            radius=100,
            created_at=datetime.now()
        )
        
        loc5 = Location(
            child_id=child2.id,
            name='School',
            latitude=30.0500,
            longitude=31.2400,
            radius=200,
            created_at=datetime.now()
        )
        
        db.session.add_all([loc1, loc2, loc3, loc4, loc5])
        db.session.flush()
        
        # Add sample alerts
        alert1 = Alert(
            child_id=child1.id,
            alert_type='emergency',
            description='Child left safe zone',
            timestamp=datetime.now() - timedelta(hours=2)
        )
        
        db.session.add(alert1)
        
        # Commit all changes
        db.session.commit()
        
        print("✅ Sample data added successfully!")
        print("\n📋 Database Summary:")
        print(f"   - Users: 1 (demo_parent)")
        print(f"   - Children: 2 (Ahmed, Fatima)")
        print(f"   - Diseases: 1 (Asthma)")
        print(f"   - Medications: 2 (Albuterol, Vitamins)")
        print(f"   - Locations: 5 (3 for Ahmed, 2 for Fatima)")
        print(f"   - Alerts: 1")
        
        print("\n🚀 Database ready! You can now run:")
        print("   python app.py")

if __name__ == '__main__':
    init_db()
