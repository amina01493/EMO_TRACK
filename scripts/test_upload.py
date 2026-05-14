#!/usr/bin/env python3
"""
Test script to verify upload functionality
"""
import os
import sys

def check_directories():
    """Check if upload directories exist and are writable"""
    dirs = [
        'static/uploads',
        'static/uploads/reports',
        'static/uploads/recordings'
    ]
    
    print("Checking directories...")
    for dir_path in dirs:
        if os.path.exists(dir_path):
            print(f"✅ {dir_path} exists")
            if os.access(dir_path, os.W_OK):
                print(f"   ✅ Directory is writable")
            else:
                print(f"   ❌ Directory is NOT writable")
        else:
            print(f"❌ {dir_path} does NOT exist")
            print(f"   Creating directory...")
            try:
                os.makedirs(dir_path, exist_ok=True)
                print(f"   ✅ Directory created")
            except Exception as e:
                print(f"   ❌ Failed to create: {e}")

def check_database():
    """Check if database models are properly configured"""
    try:
        from app import app, db, DailyRecording
        with app.app_context():
            print("\nChecking database...")
            print("✅ Database connection successful")
            
            # Check if table exists
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'daily_recording' in tables:
                print("✅ DailyRecording table exists")
                
                # Check columns
                columns = [col['name'] for col in inspector.get_columns('daily_recording')]
                required_cols = ['id', 'child_id', 'file_path', 'description', 'recording_type', 'uploaded_at', 'recorded_at']
                
                for col in required_cols:
                    if col in columns:
                        print(f"   ✅ Column '{col}' exists")
                    else:
                        print(f"   ❌ Column '{col}' MISSING")
            else:
                print("❌ DailyRecording table NOT found")
                
    except Exception as e:
        print(f"❌ Database check failed: {e}")

def test_file_write():
    """Test if we can write a test file"""
    try:
        print("\nTesting file write...")
        test_file = 'static/uploads/recordings/test_write.txt'
        os.makedirs(os.path.dirname(test_file), exist_ok=True)
        
        with open(test_file, 'w') as f:
            f.write('Test write successful')
        
        if os.path.exists(test_file):
            print("✅ File write test successful")
            os.remove(test_file)
            print("✅ Cleanup successful")
        else:
            print("❌ File was not created")
            
    except Exception as e:
        print(f"❌ File write test failed: {e}")

if __name__ == '__main__':
    print("=" * 50)
    print("Upload Functionality Test")
    print("=" * 50)
    
    check_directories()
    check_database()
    test_file_write()
    
    print("\n" + "=" * 50)
    print("Test complete!")
    print("=" * 50)
