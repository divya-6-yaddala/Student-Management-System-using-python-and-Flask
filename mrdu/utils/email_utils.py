from flask_mail import Message
from extensions import mail
from flask import current_app
from threading import Thread


def send_async_email(app, msg):
    """Send email in background thread with proper app context."""
    with app.app_context():
        try:
            mail.send(msg)
            print(f"[EMAIL] Sent successfully to: {msg.recipients}")
        except Exception as e:
            print(f"[EMAIL ERROR] Failed to send: {e}")


def send_email(subject, recipients, body_html, body_text=None):
    """Send email — tries async first, falls back to sync."""
    if not recipients:
        print("[EMAIL] No recipients provided, skipping.")
        return False

    # Clean up recipients — remove blanks
    clean_recipients = [r.strip() for r in recipients if r and r.strip()]
    if not clean_recipients:
        return False

    try:
        msg = Message(
            subject=subject,
            recipients=clean_recipients,
            html=body_html,
            body=body_text or ''
        )
        app = current_app._get_current_object()
        # Send synchronously so errors surface immediately
        # Change to Thread(...).start() if you want non-blocking
        with app.app_context():
            mail.send(msg)
        print(f"[EMAIL] Sent '{subject}' to {clean_recipients}")
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] {type(e).__name__}: {e}")
        return False


def email_template(title, body_content):
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8">
<style>
  body{{font-family:'Segoe UI',Arial,sans-serif;background:#f0f4f8;margin:0;padding:20px}}
  .wrap{{max-width:600px;margin:auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,.1)}}
  .hdr{{background:linear-gradient(135deg,#1a237e,#283593);color:#fff;padding:28px;text-align:center}}
  .hdr h1{{margin:0;font-size:22px;letter-spacing:1px}}
  .hdr p{{margin:6px 0 0;opacity:.7;font-size:13px}}
  .body{{padding:28px;color:#333;line-height:1.7}}
  .body h2{{color:#1a237e;margin-top:0}}
  .ftr{{background:#f5f5f5;padding:18px;text-align:center;font-size:12px;color:#999;border-top:1px solid #eee}}
  .badge{{display:inline-block;background:#1a237e;color:#fff;padding:4px 14px;border-radius:20px;font-size:12px;margin-bottom:14px}}
  .info-box{{background:#e8eaf6;border-left:4px solid #3f51b5;padding:14px;border-radius:6px;margin:14px 0}}
  table{{border-collapse:collapse;width:100%}}
  th{{background:#1a237e;color:#fff;padding:10px}}
  td{{padding:9px;border-bottom:1px solid #eee}}
</style>
</head>
<body>
<div class="wrap">
  <div class="hdr">
    <h1>🎓 Mallareddy Deemed University</h1>
    <p>MRDU — Hyderabad, Telangana</p>
  </div>
  <div class="body">
    <h2>{title}</h2>
    {body_content}
  </div>
  <div class="ftr">
    <p>© 2024 Mallareddy Deemed University, Hyderabad, Telangana</p>
    <p>This is an automated message. Please do not reply.</p>
  </div>
</div>
</body>
</html>"""


def send_welcome_email(user, student):
    subject = "Welcome to MRDU – Registration Successful 🎓"
    body = f"""
    <div class="badge">✅ Registration Confirmed</div>
    <p>Dear <strong>{user.full_name}</strong>,</p>
    <p>Welcome to <strong>Mallareddy Deemed University (MRDU)</strong>!
       Your student account has been successfully created.</p>
    <div class="info-box">
      <strong>Your Login Details:</strong><br><br>
      🔑 Username: <code><b>{user.username}</b></code><br>
      🎓 Roll Number: <code><b>{student.roll_number}</b></code><br>
      🏛️ Department: {student.department or 'N/A'}<br>
      📚 Course: {student.course or 'N/A'}<br>
      📅 Year / Semester: Year {student.year}, Sem {student.semester}
    </div>
    <p>Log in at <a href="http://localhost:5000/auth/login">MRDU Student Portal</a>
       to check your attendance, marks, timetable, and fees.</p>
    <p>Best wishes for your academic journey! 🌟</p>
    <p>Warm regards,<br><strong>MRDU Admissions Office</strong></p>"""
    send_email(subject, [user.email], email_template("Registration Successful!", body))


def send_fee_notification(student, fee):
    subject = f"💰 Fee {'Payment Received' if fee.status == 'paid' else 'Reminder'} – {fee.fee_type} | MRDU"
    status_line = (
        f"<span style='color:green'><b>✅ PAID IN FULL</b></span>"
        if fee.status == 'paid' else
        f"<span style='color:orange'><b>⚠️ PARTIAL PAYMENT</b></span>"
        if fee.status == 'partial' else
        f"<span style='color:red'><b>❌ PENDING</b></span>"
    )
    body = f"""
    <div class="badge">Fee Notification</div>
    <p>Dear Parent/Guardian of <strong>{student.user.full_name}</strong>,</p>
    <div class="info-box">
      <strong>Fee Details:</strong><br><br>
      👤 Student: {student.user.full_name} ({student.roll_number})<br>
      🏛️ Department: {student.department}<br>
      📋 Fee Type: {fee.fee_type}<br>
      💵 Total Amount: ₹{fee.amount:,.2f}<br>
      ✅ Amount Paid: ₹{fee.amount_paid:,.2f}<br>
      🔴 Balance Due: ₹{fee.balance:,.2f}<br>
      📅 Due Date: {fee.due_date.strftime('%d %B %Y') if fee.due_date else 'N/A'}<br>
      Status: {status_line}
    </div>
    {"<p style='color:green'>Thank you for your payment! Please retain your receipt for records.</p>" if fee.status == 'paid' else
     "<p style='color:#b71c1c'>Please clear the outstanding balance before the due date to avoid late charges.</p>"}
    <p>For queries contact: <strong>accounts@mrdu.edu.in</strong> | 040-XXXXXXXX</p>
    <p>Regards,<br><strong>MRDU Accounts Department</strong></p>"""

    recipients = [student.user.email]
    if student.parent_email:
        recipients.append(student.parent_email)
    send_email(subject, recipients, email_template("Fee Payment Notification", body))


def send_result_notification(student, marks_list, exam_type):
    subject = f"📊 Results Published – {exam_type} | MRDU"
    rows = "".join(
        f"<tr><td>{m.subject.name}</td><td style='text-align:center'>{m.marks_obtained}/{m.max_marks}</td>"
        f"<td style='text-align:center'>{m.percentage}%</td>"
        f"<td style='text-align:center;font-weight:700;color:{'green' if m.grade not in ['F','C'] else 'red'}'>{m.grade}</td></tr>"
        for m in marks_list
    )
    body = f"""
    <div class="badge">📊 Results Published</div>
    <p>Dear <strong>{student.user.full_name}</strong>,</p>
    <p>Your <strong>{exam_type}</strong> results have been published. Details below:</p>
    <table>
      <tr><th>Subject</th><th>Marks</th><th>Percentage</th><th>Grade</th></tr>
      {rows}
    </table>
    <p style="margin-top:14px">Log in to the <a href="http://localhost:5000/student/marks">Student Portal</a>
       for detailed performance analysis and subject-wise breakdown.</p>
    <p>Regards,<br><strong>MRDU Examination Cell</strong></p>"""

    recipients = [student.user.email]
    if student.parent_email:
        recipients.append(student.parent_email)
    send_email(subject, recipients, email_template(f"{exam_type} Results", body))


def send_general_notification(recipients_emails, title, message, notif_type="General"):
    subject = f"📢 {notif_type} – MRDU: {title}"
    body = f"""
    <div class="badge">{notif_type}</div>
    <p style="font-size:15px;line-height:1.8">{message}</p>
    <p>For more information, log in to the <a href="http://localhost:5000">MRDU Portal</a>.</p>
    <p>Regards,<br><strong>MRDU Administration</strong></p>"""
    send_email(subject, recipients_emails, email_template(title, body))
