from app import app, db, User

def create_simple_user():
    with app.app_context():
        # Check if user already exists
        user = User.query.filter_by(username='test').first()
        if user:
            print("User 'test' already exists. Updating password...")
            user.set_password('test')
        else:
            print("Creating new user: test / test")
            new_user = User(
                username='test',
                email='test@example.com',
                phone_number='0000000000'
            )
            new_user.set_password('test')
            db.session.add(new_user)
        
        db.session.commit()
        print("Success!")

if __name__ == '__main__':
    create_simple_user()
