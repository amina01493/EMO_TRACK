from app import app, db, User

def create_test_user():
    with app.app_context():
        # Check if user already exists
        user = User.query.filter_by(email='test@test.com').first()
        if user:
            print("User test@test.com already exists. Updating password...")
            user.set_password('test1234')
        else:
            print("Creating new test user: test@test.com")
            new_user = User(
                username='TestUser',
                email='test@test.com',
                phone_number='1234567890'
            )
            new_user.set_password('test1234')
            db.session.add(new_user)
        
        db.session.commit()
        print("Success!")

if __name__ == '__main__':
    create_test_user()
