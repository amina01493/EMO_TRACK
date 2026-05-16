from app import app, db, User, Child

def add_child_to_test():
    with app.app_context():
        user = User.query.filter_by(username='test').first()
        if not user:
            print("User 'test' not found!")
            return
            
        # Check if child already exists
        child = Child.query.filter_by(parent_id=user.id).first()
        if child:
            print(f"Child '{child.name}' already exists for user 'test'.")
        else:
            print("Adding child 'Junior' to user 'test'...")
            new_child = Child(
                parent_id=user.id,
                name='Junior',
                gender='boy',
                bracelet_code='BR12345',
                age=5
            )
            db.session.add(new_child)
            db.session.commit()
            print("Success!")

if __name__ == '__main__':
    add_child_to_test()
