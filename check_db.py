import os
from app import app, db, Child

def check_db():
    with app.app_context():
        children = Child.query.all()
        print(f"Total Children: {len(children)}")
        for c in children:
            print(f"Child ID: {c.id}, Name: {c.name}, Code: {c.bracelet_code}, Lat: {c.current_lat}, HR: {c.heart_rate}, Bat: {c.battery_level}")

if __name__ == '__main__':
    check_db()
