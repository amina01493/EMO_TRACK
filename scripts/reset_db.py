#!/usr/bin/env python3
"""
Quick Database Reset & Initialize
Use this when you want to reset the database and start fresh
"""

import os
import sys
from pathlib import Path

def reset_database():
    """Reset and reinitialize the database"""
    db_path = Path('instance/site.db')
    
    print("=" * 50)
    print(" Database Reset & Initialize")
    print("=" * 50)
    
    # Remove old database
    if db_path.exists():
        response = input(f"\n⚠️  Found existing database at {db_path}\nDelete it? (y/n): ").lower()
        if response == 'y':
            db_path.unlink()
            print("✓ Old database deleted")
        else:
            print("Cancelled")
            return
    
    # Create instance directory if needed
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Import and initialize
    print("\n🗄️  Importing database modules...")
    try:
        from app import app, db, User, Child, Disease, Medication, Location, Alert
        from datetime import datetime, timedelta
        
        with app.app_context():
            print("📊 Creating tables...")
            db.create_all()
            print("✓ Tables created")
            
            print("👨‍👩‍👧 Creating sample data...")
            
            # Create parent
            parent = User(
                username='demo_parent',
                email='parent@example.com',
                phone_number='+201012345678'
            )
            parent.set_password('password123')
            db.session.add(parent)
            db.session.flush()
            
            # Create children
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
            
            # Medical data for Ahmed
            disease = Disease(
                child_id=child1.id,
                name='Asthma',
                description='Mild seasonal asthma'
            )
            
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
            
            db.session.add_all([disease, med1, med2])
            db.session.flush()
            
            # Locations
            locations = [
                Location(child_id=child1.id, name='Home', latitude=30.0444, longitude=31.2357, radius=100),
                Location(child_id=child1.id, name='School', latitude=30.0500, longitude=31.2400, radius=200),
                Location(child_id=child1.id, name='Club', latitude=30.0600, longitude=31.2500, radius=150),
                Location(child_id=child2.id, name='Home', latitude=30.0444, longitude=31.2357, radius=100),
                Location(child_id=child2.id, name='School', latitude=30.0500, longitude=31.2400, radius=200),
            ]
            
            db.session.add_all(locations)
            
            # Alert
            alert = Alert(
                child_id=child1.id,
                alert_type='emergency',
                description='Child left safe zone',
                timestamp=datetime.now() - timedelta(hours=2)
            )
            
            db.session.add(alert)
            db.session.commit()
            
            print("✓ Sample data created")
            print("\n" + "=" * 50)
            print("✅ Database initialized successfully!")
            print("=" * 50)
            print("\n📋 Sample Data Added:")
            print("  • Users: 1 (demo_parent)")
            print("  • Children: 2 (Ahmed, Fatima)")
            print("  • Diseases: 1")
            print("  • Medications: 2")
            print("  • Locations: 5")
            print("  • Alerts: 1")
            print("\n🔑 Login with:")
            print("  Username: demo_parent")
            print("  Password: password123")
            print("\n🚀 Start the app with: python app.py")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    reset_database()
