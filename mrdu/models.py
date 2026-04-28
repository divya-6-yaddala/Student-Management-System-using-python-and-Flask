from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')
    full_name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student_profile = db.relationship('Student', backref='user', uselist=False)
    admin_profile = db.relationship('Admin', backref='user', uselist=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    roll_number = db.Column(db.String(20), unique=True, nullable=False)
    admission_number = db.Column(db.String(20), unique=True)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    phone = db.Column(db.String(15))
    address = db.Column(db.Text)
    city = db.Column(db.String(50))
    state = db.Column(db.String(50))
    pincode = db.Column(db.String(10))
    blood_group = db.Column(db.String(5))
    department = db.Column(db.String(100))
    course = db.Column(db.String(100))
    year = db.Column(db.Integer)
    semester = db.Column(db.Integer)
    section = db.Column(db.String(5))
    admission_date = db.Column(db.Date, default=datetime.utcnow)
    photo_url = db.Column(db.String(200))
    parent_name = db.Column(db.String(100))
    parent_phone = db.Column(db.String(15))
    parent_email = db.Column(db.String(120))
    parent_relation = db.Column(db.String(30))

    attendances = db.relationship('Attendance', backref='student', lazy=True)
    marks = db.relationship('Mark', backref='student', lazy=True)
    fees = db.relationship('Fee', backref='student', lazy=True)

    @property
    def attendance_percentage(self):
        total = Attendance.query.filter_by(student_id=self.id).count()
        if total == 0:
            return 0
        present = Attendance.query.filter_by(student_id=self.id, status='present').count()
        return round((present / total) * 100, 2)

    def __repr__(self):
        return f'<Student {self.roll_number}>'


class Admin(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    department = db.Column(db.String(100))
    phone = db.Column(db.String(15))


class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(10), nullable=False, default='absent')
    subject = db.Column(db.String(100))
    marked_by = db.Column(db.String(50))
    remarks = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True)
    department = db.Column(db.String(100))
    semester = db.Column(db.Integer)
    credits = db.Column(db.Integer, default=3)
    marks = db.relationship('Mark', backref='subject', lazy=True)


class Mark(db.Model):
    __tablename__ = 'marks'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    exam_type = db.Column(db.String(50))
    marks_obtained = db.Column(db.Float)
    max_marks = db.Column(db.Float, default=100)
    grade = db.Column(db.String(5))
    semester = db.Column(db.Integer)
    academic_year = db.Column(db.String(10))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def percentage(self):
        if self.max_marks:
            return round((self.marks_obtained / self.max_marks) * 100, 2)
        return 0

    @staticmethod
    def calculate_grade(percentage):
        if percentage >= 90: return 'O'
        elif percentage >= 80: return 'A+'
        elif percentage >= 70: return 'A'
        elif percentage >= 60: return 'B+'
        elif percentage >= 50: return 'B'
        elif percentage >= 40: return 'C'
        else: return 'F'


class Fee(db.Model):
    __tablename__ = 'fees'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    fee_type = db.Column(db.String(50))
    amount = db.Column(db.Float, nullable=False)
    amount_paid = db.Column(db.Float, default=0)
    due_date = db.Column(db.Date)
    paid_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='pending')
    transaction_id = db.Column(db.String(50))
    receipt_number = db.Column(db.String(30))
    academic_year = db.Column(db.String(10))
    remarks = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def balance(self):
        return self.amount - self.amount_paid


class Timetable(db.Model):
    __tablename__ = 'timetable'
    id = db.Column(db.Integer, primary_key=True)
    department = db.Column(db.String(100))
    section = db.Column(db.String(5))
    semester = db.Column(db.Integer)
    day = db.Column(db.String(15))
    period = db.Column(db.Integer)
    subject = db.Column(db.String(100))
    faculty = db.Column(db.String(100))
    room = db.Column(db.String(20))
    start_time = db.Column(db.String(10))
    end_time = db.Column(db.String(10))
    is_exam = db.Column(db.Boolean, default=False)


class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50))
    target = db.Column(db.String(20), default='all')
    target_value = db.Column(db.String(100))
    sent_by = db.Column(db.String(50))
    is_email = db.Column(db.Boolean, default=True)
    email_sent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    event_type = db.Column(db.String(50))
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    venue = db.Column(db.String(100))
    created_by = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
