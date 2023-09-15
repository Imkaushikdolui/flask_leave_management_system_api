from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, Resource, reqparse, marshal_with, fields, abort
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import CheckConstraint

app = Flask(__name__)
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////home/panda/Documents/learning_flask/flask_lms_api/db.sqlite'
db = SQLAlchemy(app)

# Define the User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default='employee', nullable=False)

    __table_args__ = (
        CheckConstraint(role.in_(['admin', 'employee']), name='valid_role_check'),
    )

    def __init__(self, email, password, name, role=None):
        self.email = email
        self.password = password
        self.name = name
        self.role = role if role is not None else 'employee'

    def is_admin(self):
        return self.role == 'admin'

    def is_employee(self):
        return self.role == 'employee'

# Create a request parser for user data
user_parser = reqparse.RequestParser()
user_parser.add_argument('email', type=str, required=True)
user_parser.add_argument('password', type=str, required=True)
user_parser.add_argument('name', type=str, required=True)
user_parser.add_argument('role', type=str)

# Define response fields for User
user_fields = {
    'id': fields.Integer,
    'email': fields.String,
    'name': fields.String,
    'role': fields.String
}

# Define the User resource with marshal_with decorator
class UserResource(Resource):
    @marshal_with(user_fields)  # Serialize the response using user_fields
    def get(self, user_id=None):
        if user_id is None:
            # If user_id is not provided, return a list of all users
            users = User.query.all()
            return users
        else:
            # Get a user by ID
            user = User.query.get(user_id)
            if user:
                return user
            else:
                abort(404, message='User not found')

    @marshal_with(user_fields)
    def put(self, user_id):
        args = user_parser.parse_args()
        user = User.query.get(user_id)
        if user:
            user.email = args['email']
            user.password = args['password']
            user.name = args['name']
            user.role = args['role'] if args['role'] is not None else 'employee'
            db.session.commit()
            return user
        else:
            abort(404, message='User not found')

    @marshal_with(user_fields)
    def delete(self, user_id):
        user = User.query.get(user_id)
        if user:
            db.session.delete(user)
            db.session.commit()
            return user
        else:
            abort(404, message='User not found')

    @marshal_with(user_fields)
    def post(self):
        args = user_parser.parse_args()
        user = User(**args)
        db.session.add(user)
        db.session.commit()
        return user

# Define the Leave Application model
class LeaveApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_from = db.Column(db.Date, nullable=False)
    date_to = db.Column(db.Date, nullable=False)
    reason = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default='Pending')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('leave_applications', lazy=True))
    
    __table_args__ = (
        CheckConstraint(status.in_(['Approved', 'Pending', 'Rejected']), name='valid_status_check'),
    )

    def __init__(self, date_from, date_to, reason, user_id, status=None):
        self.date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
        self.date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
        self.reason = reason
        self.user_id = user_id
        self.status = status if status is not None else 'Pending'

    def __repr__(self):
        return f"LeaveApplication({self.date_from}, {self.date_to}, {self.reason}, {self.status})"

# Create a request parser for leave application data
leave_parser = reqparse.RequestParser()
leave_parser.add_argument('date_from', type=str, required=True)
leave_parser.add_argument('date_to', type=str, required=True)
leave_parser.add_argument('reason', type=str, required=True)
leave_parser.add_argument('user_id', type=int, required=True)
leave_parser.add_argument('status', type=str)

# Define response fields for LeaveApplication
leave_fields = {
    'id': fields.Integer,
    'date_from': fields.String(attribute=lambda x: x.date_from.strftime('%Y-%m-%d')),
    'date_to': fields.String(attribute=lambda x: x.date_to.strftime('%Y-%m-%d')),
    'reason': fields.String,
    'status': fields.String,
    'user_id': fields.Integer
}

# Define the Leave Application resource with marshal_with decorator
class LeaveApplicationResource(Resource):
    @marshal_with(leave_fields)  # Serialize the response using leave_fields
    def get(self, leave_id=None):
        if leave_id is None:
            # If leave_id is not provided, return a list of all leaves
            leaves = LeaveApplication.query.all()
            return leaves
        else:
            # Get a leave by ID
            leave = LeaveApplication.query.get(leave_id)
            if leave:
                return leave
            else:
                abort(404, message='Leave application not found')

    @marshal_with(leave_fields)
    def put(self, leave_id):
        args = leave_parser.parse_args()
        leave = LeaveApplication.query.get(leave_id)
        if leave:
            leave.date_from = datetime.strptime(args['date_from'], '%Y-%m-%d').date()
            leave.date_to = datetime.strptime(args['date_to'], '%Y-%m-%d').date()
            leave.reason = args['reason']
            leave.status = args['status'] if args['status'] is not None else 'Pending'
            db.session.commit()
            return leave
        else:
            abort(404, message='Leave application not found')

    @marshal_with(leave_fields)
    def delete(self, leave_id):
        leave = LeaveApplication.query.get(leave_id)
        if leave:
            db.session.delete(leave)
            db.session.commit()
            return leave
        else:
            abort(404, message='Leave application not found')

    @marshal_with(leave_fields)
    def post(self):
        args = leave_parser.parse_args()
        leave = LeaveApplication(**args)
        db.session.add(leave)
        db.session.commit()
        return leave


with app.app_context():
    db.create_all()
    
    
    
# Add resources to the API
api.add_resource(UserResource, '/adduser', '/user/<int:user_id>', '/users')  # Add '/users' route
api.add_resource(LeaveApplicationResource, '/addleave', '/leave/<int:leave_id>', '/leaves')  # Add '/leaves' route





if __name__ == '__main__':
    app.run(debug=True)
