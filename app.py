from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
# Allow CORS for the frontend
CORS(app, resources={r"/api/*": {"origins": "*"}})

# PostgreSQL Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), nullable=False) # student, parent, driver, admin
    approved = db.Column(db.Boolean, default=False)

    # Relationships to profiles
    student_info = db.relationship('StudentProfile', backref='user', uselist=False, cascade="all, delete-orphan")
    parent_info = db.relationship('ParentProfile', backref='user', uselist=False, cascade="all, delete-orphan")
    driver_info = db.relationship('DriverProfile', backref='user', uselist=False, cascade="all, delete-orphan")

    def to_dict(self):
        data = {
            "id": self.id, 
            "username": self.username, 
            "role": self.role,
            "approved": self.approved
        }
        
        # Merge profile details based on role
        if self.role == 'student' and self.student_info:
            data.update({
                "full_name": self.student_info.full_name,
                "assigned_bus": self.student_info.assigned_bus,
                "assigned_stop": self.student_info.assigned_stop
            })
        elif self.role == 'parent' and self.parent_info:
            data.update({
                "full_name": self.parent_info.full_name,
                "student_name": self.parent_info.student_name
            })
        elif self.role == 'driver' and self.driver_info:
            data.update({
                "full_name": self.driver_info.full_name,
                "assigned_bus": self.driver_info.assigned_bus
            })
        elif self.role == 'admin':
            data.update({"full_name": "Principal"})
            
        return data

class StudentProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    full_name = db.Column(db.String(100))
    assigned_bus = db.Column(db.String(10))
    assigned_stop = db.Column(db.String(100))

class ParentProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    full_name = db.Column(db.String(100))
    student_name = db.Column(db.String(100))

class DriverProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    full_name = db.Column(db.String(100))
    assigned_bus = db.Column(db.String(10))

class Bus(db.Model):
    id = db.Column(db.String(10), primary_key=True)
    name = db.Column(db.String(50), nullable=False, default="Unnamed Bus")
    route_name = db.Column(db.String(100))
    current_stop = db.Column(db.String(50))
    next_stop = db.Column(db.String(50))
    eta = db.Column(db.String(20))
    speed = db.Column(db.String(20))
    lat = db.Column(db.Float, default=12.9716) 
    lng = db.Column(db.Float, default=77.5946)
    
    stops = db.relationship('Stop', backref='bus', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "route_name": self.route_name,
            "current_stop": self.current_stop,
            "next_stop": self.next_stop,
            "eta": self.eta,
            "speed": self.speed,
            "lat": self.lat,
            "lng": self.lng,
            "stops": [s.name for s in self.stops]
        }

class Stop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    bus_id = db.Column(db.String(10), db.ForeignKey('bus.id'), nullable=False)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(500), nullable=False)
    sender = db.Column(db.String(20), default='admin')
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

    def to_dict(self):
        return {
            "id": self.id,
            "message": self.message,
            "sender": self.sender,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }

# API Routes
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')

    # ✅ SPECIAL RULE FOR ADMIN
    if role == 'admin':
        admin_user_env = os.getenv('ADMIN_USERNAME', 'Principal')
        admin_pass_env = os.getenv('ADMIN_PASSWORD', 'admin@123')
        
        if username == admin_user_env and password == admin_pass_env:
            # Check if admin user exists in DB, if not create/sync it
            admin_user = User.query.filter_by(username=admin_user_env, role='admin').first()
            if not admin_user:
                admin_user = User(username=admin_user_env, password=admin_pass_env, role='admin', approved=True)
                db.session.add(admin_user)
                db.session.commit()
            return jsonify({"success": True, "user": admin_user.to_dict()})
        return jsonify({"success": False, "message": "Invalid Admin Credentials"}), 401

    user = User.query.filter_by(username=username, password=password, role=role).first()
    if user:
        if not user.approved and user.role != 'admin':
            return jsonify({"success": False, "message": "Account pending admin approval"}), 403
        return jsonify({"success": True, "user": user.to_dict()})
    return jsonify({"success": False, "message": "Invalid credentials"}), 401

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.json
    username = data.get('username')
    role = data.get('role')
    
    # ✅ Auto-populate full_name with username if missing
    full_nm = data.get('full_name', username)

    # ✅ BLOCK ADMIN SIGNUP
    if role == 'admin':
        return jsonify({"success": False, "message": "Administrator registration is disabled"}), 403

    if User.query.filter_by(username=username).first():
        return jsonify({"success": False, "message": "Username already taken"}), 400

    try:
        new_user = User(username=username, password=data.get('password'), role=role, approved=False)
        db.session.add(new_user)
        db.session.flush()

        if role == 'student':
            profile = StudentProfile(user_id=new_user.id, full_name=full_nm, assigned_bus=data.get('assigned_bus'), assigned_stop=data.get('assigned_stop'))
            db.session.add(profile)
        elif role == 'parent':
            profile = ParentProfile(user_id=new_user.id, full_name=full_nm, student_name=data.get('student_name'))
            db.session.add(profile)
        elif role == 'driver':
            profile = DriverProfile(user_id=new_user.id, full_name=full_nm, assigned_bus=data.get('assigned_bus'))
            db.session.add(profile)

        db.session.commit()
        return jsonify({"success": True, "message": "Signup successful", "user": new_user.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/admin/pending_users', methods=['GET'])
def get_pending_users():
    users = User.query.filter_by(approved=False).all()
    return jsonify([user.to_dict() for user in users])

@app.route('/api/admin/all_users', methods=['GET'])
def get_all_users():
    users = User.query.filter(User.role != 'admin').all()
    return jsonify([user.to_dict() for user in users])

@app.route('/api/admin/approve_user/<int:user_id>', methods=['POST'])
def approve_user(user_id):
    user = User.query.get(user_id)
    if user:
        user.approved = True
        db.session.commit()
        return jsonify({"success": True, "message": f"User {user.username} approved"})
    return jsonify({"success": False, "message": "User not found"}), 404

@app.route('/api/admin/add_bus', methods=['POST'])
def add_bus():
    data = request.json
    try:
        new_bus = Bus(
            id=data.get('id'),
            name=data.get('name', "Bus " + str(data.get('id'))),
            route_name=data.get('route_name'),
            lat=data.get('lat', 12.9716),
            lng=data.get('lng', 77.5946)
        )
        stops_list = data.get('stops', [])
        for stop_name in stops_list:
            if stop_name.strip():
                new_stop = Stop(name=stop_name, bus=new_bus)
                db.session.add(new_stop)
        db.session.add(new_bus)
        db.session.commit()
        return jsonify({"success": True, "message": "Bus and stops added"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/notifications', methods=['GET', 'POST'])
def handle_notifications():
    if request.method == 'POST':
        data = request.json
        new_note = Notification(message=data.get('message'), sender=data.get('sender', 'admin'))
        db.session.add(new_note)
        db.session.commit()
        return jsonify({"success": True})
    notes = Notification.query.order_by(Notification.timestamp.desc()).limit(10).all()
    return jsonify([n.to_dict() for n in notes])

@app.route('/api/buses', methods=['GET'])
def get_buses():
    buses = Bus.query.all()
    return jsonify([bus.to_dict() for bus in buses])

@app.route('/api/buses/<bus_id>', methods=['GET'])
def get_bus(bus_id):
    bus = Bus.query.get(bus_id)
    if bus:
        return jsonify(bus.to_dict())
    return jsonify({"message": "Bus not found"}), 404

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(port=5001, debug=True)
