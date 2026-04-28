from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime

from extensions import db
from models import Student, Attendance, Mark, Fee, Event, Timetable

student = Blueprint('student', __name__)


def student_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'student':
            flash('Access denied.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def get_student():
    return Student.query.filter_by(user_id=current_user.id).first()


@student.route('/dashboard')
@login_required
@student_required
def dashboard():
    s = get_student()
    if not s:
        flash('Student profile not found. Contact admin.', 'warning')
        return redirect(url_for('auth.logout'))

    recent_att = Attendance.query.filter_by(student_id=s.id).order_by(Attendance.date.desc()).limit(7).all()
    recent_marks = Mark.query.filter_by(student_id=s.id).order_by(Mark.created_at.desc()).limit(5).all()
    pending_fees = Fee.query.filter_by(student_id=s.id).filter(Fee.status.in_(['pending', 'partial'])).all()
    events = Event.query.filter(Event.start_date >= datetime.utcnow()).order_by(Event.start_date).limit(3).all()

    return render_template('student/dashboard.html', student=s,
                           recent_att=recent_att, recent_marks=recent_marks,
                           pending_fees=pending_fees, events=events)


@student.route('/profile')
@login_required
@student_required
def profile():
    s = get_student()
    return render_template('student/profile.html', student=s)


@student.route('/attendance')
@login_required
@student_required
def attendance():
    s = get_student()
    subject_filter = request.args.get('subject', '')

    query = Attendance.query.filter_by(student_id=s.id)
    if subject_filter:
        query = query.filter_by(subject=subject_filter)

    records = query.order_by(Attendance.date.desc()).all()
    total = len(records)
    present = sum(1 for r in records if r.status == 'present')
    absent = sum(1 for r in records if r.status == 'absent')
    late = sum(1 for r in records if r.status == 'late')
    pct = round((present / total * 100), 2) if total else 0

    subjects = db.session.query(Attendance.subject).filter_by(student_id=s.id).distinct().all()

    return render_template('student/attendance.html', student=s, records=records,
                           total=total, present=present, absent=absent, late=late,
                           percentage=pct, subjects=[x[0] for x in subjects if x[0]])


@student.route('/marks')
@login_required
@student_required
def marks():
    s = get_student()
    semester = request.args.get('semester', '')
    exam_type = request.args.get('exam_type', '')

    query = Mark.query.filter_by(student_id=s.id)
    if semester:
        query = query.filter_by(semester=int(semester))
    if exam_type:
        query = query.filter_by(exam_type=exam_type)

    marks_list = query.order_by(Mark.created_at.desc()).all()
    exam_types = db.session.query(Mark.exam_type).filter_by(student_id=s.id).distinct().all()
    semesters = db.session.query(Mark.semester).filter_by(student_id=s.id).distinct().all()

    summary = {}
    for m in marks_list:
        key = f"{m.exam_type} - Sem {m.semester}"
        if key not in summary:
            summary[key] = {'total': 0, 'obtained': 0, 'count': 0}
        summary[key]['total'] += m.max_marks
        summary[key]['obtained'] += m.marks_obtained
        summary[key]['count'] += 1

    return render_template('student/marks.html', student=s, marks=marks_list,
                           exam_types=[x[0] for x in exam_types if x[0]],
                           semesters=[x[0] for x in semesters if x[0]],
                           summary=summary)


@student.route('/fees')
@login_required
@student_required
def fees():
    s = get_student()
    fees_list = Fee.query.filter_by(student_id=s.id).order_by(Fee.created_at.desc()).all()
    total_due = sum(f.amount for f in fees_list)
    total_paid = sum(f.amount_paid for f in fees_list)
    total_balance = total_due - total_paid
    return render_template('student/fees.html', student=s, fees=fees_list,
                           total_due=total_due, total_paid=total_paid,
                           total_balance=total_balance)


@student.route('/timetable')
@login_required
@student_required
def timetable():
    s = get_student()
    tt = Timetable.query.filter_by(department=s.department, semester=s.semester).all()
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    timetable_dict = {day: [] for day in days}
    for entry in tt:
        if entry.day in timetable_dict:
            timetable_dict[entry.day].append(entry)
    for day in timetable_dict:
        timetable_dict[day].sort(key=lambda x: x.period)
    return render_template('student/timetable.html', student=s,
                           timetable=timetable_dict, days=days)


@student.route('/events')
@login_required
@student_required
def events():
    s = get_student()
    events_list = Event.query.order_by(Event.start_date.desc()).all()
    return render_template('student/events.html', student=s, events=events_list)
