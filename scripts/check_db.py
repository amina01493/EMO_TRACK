#!/usr/bin/env python3
"""
SQLite Database Check & Initialize Script
Verifies the database structure and creates sample data if needed
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = 'instance/site.db'

def check_database():
    """Check if database exists and show its structure"""
    if os.path.exists(DB_PATH):
        print(f"✅ Database found at: {DB_PATH}")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if tables:
            print(f"\n📊 Found {len(tables)} tables:")
            for table in tables:
                table_name = table[0]
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                print(f"\n  📋 {table_name.upper()}:")
                for col in columns:
                    print(f"     - {col[1]} ({col[2]})")
                
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"     Records: {count}")
        else:
            print("\n⚠️  Database exists but is empty - no tables found")
            print("Run 'init_db.py' to initialize the database")
        
        conn.close()
    else:
        print(f"❌ Database not found at: {DB_PATH}")
        print("Creating empty database...")
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.close()
        print("✅ Empty database created!")
        print("\nRun 'init_db.py' to add tables and sample data")

if __name__ == '__main__':
    check_database()
