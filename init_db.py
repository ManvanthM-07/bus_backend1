from app import db, User, StudentProfile, ParentProfile, DriverProfile, Bus, Notification, Stop, app
import datetime
import os
from dotenv import load_dotenv

load_dotenv()

def seed_db():
    with app.app_context():
        # Clean current data
        db.drop_all()
        db.create_all()

        # 1. Add Default Admin
        admin = User(username='Principal', password='admin@123', role='admin', approved=True)
        db.session.add(admin)

        # 2. Add sample Buses and Stops
        b1 = Bus(id='1', name='Bus 1', route_name='Station → College', lat=12.9716, lng=77.5946)
        b2 = Bus(id='2', name='Bus 2', route_name='Mall → Campus', lat=12.9800, lng=77.6000)
        db.session.add_all([b1, b2])
        db.session.flush()

        # Add stops for Bus 1
        s1 = Stop(name='Station', bus=b1)
        s2 = Stop(name='Bogadi', bus=b1)
        db.session.add_all([s1, s2])

        # 3. Add Sample Student
        u_student = User(username='student', password='123', role='student', approved=True)
        db.session.add(u_student)
        db.session.flush()
        sp = StudentProfile(user_id=u_student.id, full_name='student', assigned_bus='1', assigned_stop='Bogadi')
        db.session.add(sp)

        # 4. Add Sample Driver
        u_driver = User(username='driver', password='123', role='driver', approved=True)
        db.session.add(u_driver)
        db.session.flush()
        dp = DriverProfile(user_id=u_driver.id, full_name='driver', assigned_bus='1')
        db.session.add(dp)

        # 5. Add Sample Parent (with student_name and full_name)
        u_parent = User(username='parent', password='123', role='parent', approved=True)
        db.session.add(u_parent)
        db.session.flush()
        pp = ParentProfile(user_id=u_parent.id, full_name='parent', student_name='student')
        db.session.add(pp)

        db.session.commit()
        print("Database re-initialized: Sample names now match usernames.")

if __name__ == '__main__':
    seed_db()
