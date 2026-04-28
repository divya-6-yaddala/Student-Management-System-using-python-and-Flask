from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, date
import random, string

from extensions import db
from models import User, Student, Admin, Attendance, Subject, Mark, Fee, Timetable, Notification, Event
from utils.email_utils import send_welcome_email, send_fee_notification, send_result_notification, send_general_notification

admin = Blueprint('admin', __name__)


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def gen_receipt():
    return 'MRDU' + ''.join(random.choices(string.digits, k=8))


# ─── DASHBOARD ───────────────────────────────────────────────
@admin.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_due = db.session.query(db.func.sum(Fee.amount)).scalar() or 0
    total_paid = db.session.query(db.func.sum(Fee.amount_paid)).scalar() or 0
    stats = {
        'total_students': Student.query.count(),
        'total_fees_collected': total_paid,
        'pending_fees': total_due - total_paid,
        'notifications_sent': Notification.query.count(),
        'upcoming_events': Event.query.filter(Event.start_date >= datetime.utcnow()).count(),
    }
    recent_students = Student.query.order_by(Student.id.desc()).limit(5).all()
    recent_fees = Fee.query.order_by(Fee.created_at.desc()).limit(5).all()
    upcoming_events = Event.query.filter(Event.start_date >= datetime.utcnow()).order_by(Event.start_date).limit(4).all()
    return render_template('admin/dashboard.html', stats=stats,
                           recent_students=recent_students, recent_fees=recent_fees,
                           upcoming_events=upcoming_events)


# ─── STUDENTS ────────────────────────────────────────────────
@admin.route('/students')
@login_required
@admin_required
def students():
    dept = request.args.get('dept', '')
    year = request.args.get('year', '')
    search = request.args.get('search', '')
    query = Student.query.join(User)
    if dept:
        query = query.filter(Student.department == dept)
    if year:
        query = query.filter(Student.year == int(year))
    if search:
        query = query.filter(
            (User.full_name.ilike(f'%{search}%')) |
            (Student.roll_number.ilike(f'%{search}%'))
        )
    students_list = query.all()
    departments = db.session.query(Student.department).distinct().all()
    return render_template('admin/students.html', students=students_list,
                           departments=[d[0] for d in departments if d[0]])


@admin.route('/students/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_student():
    if request.method == 'POST':
        f = request.form
        if User.query.filter_by(username=f['username']).first():
            flash('Username already exists!', 'danger')
            return render_template('admin/add_student.html')
        if User.query.filter_by(email=f['email']).first():
            flash('Email already exists!', 'danger')
            return render_template('admin/add_student.html')

        user = User(username=f['username'], email=f['email'],
                    full_name=f['full_name'], role='student')
        user.set_password(f['password'])
        db.session.add(user)
        db.session.flush()

        dob = datetime.strptime(f['dob'], '%Y-%m-%d').date() if f.get('dob') else None
        adm_date = datetime.strptime(f['admission_date'], '%Y-%m-%d').date() if f.get('admission_date') else date.today()

        student = Student(
            user_id=user.id, roll_number=f['roll_number'],
            admission_number=f.get('admission_number'),
            date_of_birth=dob, gender=f.get('gender'),
            phone=f.get('phone'), address=f.get('address'),
            city=f.get('city'), state=f.get('state'), pincode=f.get('pincode'),
            blood_group=f.get('blood_group'), department=f['department'],
            course=f['course'], year=int(f['year']), semester=int(f['semester']),
            section=f.get('section'), admission_date=adm_date,
            parent_name=f.get('parent_name'), parent_phone=f.get('parent_phone'),
            parent_email=f.get('parent_email'), parent_relation=f.get('parent_relation')
        )
        db.session.add(student)
        db.session.commit()
        try:
            send_welcome_email(user, student)
        except Exception:
            pass
        flash(f'Student {user.full_name} added successfully! Welcome email sent.', 'success')
        return redirect(url_for('admin.students'))

    return render_template('admin/add_student.html')


@admin.route('/students/<int:sid>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_student(sid):
    student = Student.query.get_or_404(sid)
    user = student.user
    if request.method == 'POST':
        f = request.form
        user.full_name = f['full_name']
        user.email = f['email']
        student.phone = f.get('phone')
        student.address = f.get('address')
        student.city = f.get('city')
        student.state = f.get('state')
        student.pincode = f.get('pincode')
        student.department = f['department']
        student.course = f['course']
        student.year = int(f['year'])
        student.semester = int(f['semester'])
        student.section = f.get('section')
        student.blood_group = f.get('blood_group')
        student.parent_name = f.get('parent_name')
        student.parent_phone = f.get('parent_phone')
        student.parent_email = f.get('parent_email')
        student.parent_relation = f.get('parent_relation')
        if f.get('dob'):
            student.date_of_birth = datetime.strptime(f['dob'], '%Y-%m-%d').date()
        db.session.commit()
        flash('Student details updated successfully!', 'success')
        return redirect(url_for('admin.view_student', sid=sid))
    return render_template('admin/edit_student.html', student=student)


@admin.route('/students/<int:sid>')
@login_required
@admin_required
def view_student(sid):
    student = Student.query.get_or_404(sid)
    return render_template('admin/view_student.html', student=student)


@admin.route('/students/<int:sid>/delete', methods=['POST'])
@login_required
@admin_required
def delete_student(sid):
    student = Student.query.get_or_404(sid)
    user = student.user
    db.session.delete(student)
    db.session.delete(user)
    db.session.commit()
    flash('Student deleted.', 'success')
    return redirect(url_for('admin.students'))


# ─── ATTENDANCE ──────────────────────────────────────────────
@admin.route('/attendance', methods=['GET', 'POST'])
@login_required
@admin_required
def attendance():
    dept = request.args.get('dept', '')
    att_date = request.args.get('date', date.today().isoformat())
    selected_subject = request.args.get('subject', '')

    students_list = Student.query
    if dept:
        students_list = students_list.filter_by(department=dept)
    students_list = students_list.all()

    if request.method == 'POST':
        att_date_obj = datetime.strptime(request.form['att_date'], '%Y-%m-%d').date()
        subj = request.form.get('subject', '')
        for s in students_list:
            status = request.form.get(f'att_{s.id}', 'absent')
            existing = Attendance.query.filter_by(student_id=s.id, date=att_date_obj, subject=subj).first()
            if existing:
                existing.status = status
            else:
                att = Attendance(student_id=s.id, date=att_date_obj, status=status,
                                 subject=subj, marked_by=current_user.full_name)
                db.session.add(att)
        db.session.commit()
        flash('Attendance saved successfully!', 'success')
        return redirect(url_for('admin.attendance'))

    departments = db.session.query(Student.department).distinct().all()
    attendance_map = {}
    att_date_obj = datetime.strptime(att_date, '%Y-%m-%d').date()
    for s in students_list:
        rec = Attendance.query.filter_by(student_id=s.id, date=att_date_obj, subject=selected_subject).first()
        attendance_map[s.id] = rec.status if rec else 'absent'

    return render_template('admin/attendance.html', students=students_list,
                           departments=[d[0] for d in departments if d[0]],
                           att_date=att_date, attendance_map=attendance_map,
                           selected_dept=dept, selected_subject=selected_subject)


# ─── MARKS ───────────────────────────────────────────────────
@admin.route('/marks', methods=['GET', 'POST'])
@login_required
@admin_required
def marks():
    students_list = Student.query.all()
    subjects = Subject.query.all()
    if request.method == 'POST':
        f = request.form
        student_id = int(f['student_id'])
        subject_id = int(f['subject_id'])
        exam_type = f['exam_type']
        marks_obtained = float(f['marks_obtained'])
        max_marks = float(f.get('max_marks', 100))
        semester = int(f.get('semester', 1))
        ay = f.get('academic_year', '2024-25')
        pct = (marks_obtained / max_marks) * 100
        grade = Mark.calculate_grade(pct)

        existing = Mark.query.filter_by(student_id=student_id, subject_id=subject_id,
                                        exam_type=exam_type, semester=semester, academic_year=ay).first()
        if existing:
            existing.marks_obtained = marks_obtained
            existing.max_marks = max_marks
            existing.grade = grade
        else:
            mark = Mark(student_id=student_id, subject_id=subject_id, exam_type=exam_type,
                        marks_obtained=marks_obtained, max_marks=max_marks, grade=grade,
                        semester=semester, academic_year=ay)
            db.session.add(mark)
        db.session.commit()
        student = Student.query.get(student_id)
        all_marks = Mark.query.filter_by(student_id=student_id, exam_type=exam_type,
                                         semester=semester, academic_year=ay).all()
        try:
            send_result_notification(student, all_marks, exam_type)
        except Exception:
            pass
        flash('Marks saved and result notification sent!', 'success')
        return redirect(url_for('admin.marks'))

    all_marks = Mark.query.order_by(Mark.created_at.desc()).limit(50).all()
    return render_template('admin/marks.html', students=students_list, subjects=subjects, marks=all_marks)


# ─── SUBJECTS ────────────────────────────────────────────────
@admin.route('/subjects', methods=['GET', 'POST'])
@login_required
@admin_required
def subjects():
    if request.method == 'POST':
        f = request.form
        if f.get('action') == 'delete':
            sub = Subject.query.get(int(f['subject_id']))
            if sub:
                db.session.delete(sub)
                db.session.commit()
                flash('Subject deleted.', 'success')
        else:
            sub = Subject(name=f['name'], code=f['code'], department=f['department'],
                          semester=int(f.get('semester', 1)), credits=int(f.get('credits', 3)))
            db.session.add(sub)
            db.session.commit()
            flash('Subject added!', 'success')
        return redirect(url_for('admin.subjects'))
    subjects_list = Subject.query.all()
    return render_template('admin/subjects.html', subjects=subjects_list)


# ─── TIMETABLE ───────────────────────────────────────────────
@admin.route('/timetable', methods=['GET', 'POST'])
@login_required
@admin_required
def timetable():
    if request.method == 'POST':
        f = request.form
        tt = Timetable(department=f['department'], section=f.get('section', 'A'),
                       semester=int(f['semester']), day=f['day'],
                       period=int(f['period']), subject=f['subject'],
                       faculty=f.get('faculty'), room=f.get('room'),
                       start_time=f.get('start_time'), end_time=f.get('end_time'))
        db.session.add(tt)
        db.session.commit()
        flash('Timetable entry added!', 'success')
        return redirect(url_for('admin.timetable'))

    dept = request.args.get('dept', '')
    sem = request.args.get('sem', '')
    query = Timetable.query
    if dept:
        query = query.filter_by(department=dept)
    if sem:
        query = query.filter_by(semester=int(sem))
    timetable_list = query.all()
    departments = db.session.query(Student.department).distinct().all()
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    return render_template('admin/timetable.html', timetable=timetable_list,
                           departments=[d[0] for d in departments if d[0]],
                           selected_dept=dept, selected_sem=sem, days=days_order)


# ─── FEES ────────────────────────────────────────────────────
@admin.route('/fees', methods=['GET', 'POST'])
@login_required
@admin_required
def fees():
    if request.method == 'POST':
        f = request.form
        action = f.get('action')
        if action == 'add':
            due = datetime.strptime(f['due_date'], '%Y-%m-%d').date() if f.get('due_date') else None
            fee = Fee(student_id=int(f['student_id']), fee_type=f['fee_type'],
                      amount=float(f['amount']), due_date=due,
                      academic_year=f.get('academic_year', '2024-25'),
                      receipt_number=gen_receipt(), status='pending')
            db.session.add(fee)
            db.session.commit()
            student = Student.query.get(int(f['student_id']))
            try:
                send_fee_notification(student, fee)
            except Exception:
                pass
            flash('Fee record added and notification sent!', 'success')

        elif action == 'pay':
            fee = Fee.query.get_or_404(int(f['fee_id']))
            pay_amt = float(f['pay_amount'])
            fee.amount_paid += pay_amt
            fee.paid_date = datetime.utcnow()
            fee.status = 'paid' if fee.amount_paid >= fee.amount else 'partial'
            fee.transaction_id = f.get('transaction_id', gen_receipt())
            db.session.commit()
            student = Student.query.get(fee.student_id)
            try:
                send_fee_notification(student, fee)
            except Exception:
                pass
            flash(f'Payment of ₹{pay_amt:,.2f} recorded!', 'success')

        return redirect(url_for('admin.fees'))

    students_list = Student.query.all()
    fees_list = Fee.query.order_by(Fee.created_at.desc()).all()
    return render_template('admin/fees.html', students=students_list, fees=fees_list)


# ─── NOTIFICATIONS ───────────────────────────────────────────
@admin.route('/notifications', methods=['GET', 'POST'])
@login_required
@admin_required
def notifications():
    if request.method == 'POST':
        f = request.form
        target = f['target']
        target_value = f.get('target_value', '')

        recipients = []
        if target == 'all':
            for s in Student.query.join(User).all():
                recipients.append(s.user.email)
                if s.parent_email:
                    recipients.append(s.parent_email)
        elif target == 'department':
            for s in Student.query.filter_by(department=target_value).join(User).all():
                recipients.append(s.user.email)
                if s.parent_email:
                    recipients.append(s.parent_email)
        elif target == 'student':
            s = Student.query.filter_by(roll_number=target_value).first()
            if s:
                recipients.append(s.user.email)
                if s.parent_email:
                    recipients.append(s.parent_email)

        notif = Notification(
            title=f['title'], message=f['message'],
            notification_type=f['notif_type'], target=target,
            target_value=target_value, sent_by=current_user.full_name, is_email=True
        )
        db.session.add(notif)

        if recipients:
            try:
                send_general_notification(list(set(recipients)), f['title'],
                                          f['message'], f['notif_type'])
                notif.email_sent = True
                flash(f'Notification sent to {len(set(recipients))} recipients!', 'success')
            except Exception as e:
                flash(f'Notification saved but email failed: {e}', 'warning')
        else:
            flash('Notification saved (no recipients found).', 'warning')

        db.session.commit()
        return redirect(url_for('admin.notifications'))

    notifications_list = Notification.query.order_by(Notification.created_at.desc()).all()
    departments = db.session.query(Student.department).distinct().all()
    return render_template('admin/notifications.html',
                           notifications=notifications_list,
                           departments=[d[0] for d in departments if d[0]])


# ─── EVENTS ──────────────────────────────────────────────────
@admin.route('/events', methods=['GET', 'POST'])
@login_required
@admin_required
def events():
    if request.method == 'POST':
        f = request.form
        if f.get('action') == 'delete':
            ev = Event.query.get_or_404(int(f['event_id']))
            db.session.delete(ev)
            db.session.commit()
            flash('Event deleted.', 'success')
        else:
            start = datetime.strptime(f['start_date'], '%Y-%m-%dT%H:%M') if f.get('start_date') else None
            end = datetime.strptime(f['end_date'], '%Y-%m-%dT%H:%M') if f.get('end_date') else None
            ev = Event(title=f['title'], description=f.get('description'),
                       event_type=f['event_type'], start_date=start, end_date=end,
                       venue=f.get('venue'), created_by=current_user.full_name)
            db.session.add(ev)
            db.session.commit()
            flash('Event added!', 'success')
        return redirect(url_for('admin.events'))

    events_list = Event.query.order_by(Event.start_date.desc()).all()
    return render_template('admin/events.html', events=events_list)
