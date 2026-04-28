# 🎓 MRDU Student Management System
### Mallareddy Deemed University — Hyderabad, Telangana

A full-featured Student Management System built with Flask.

---

## ✅ Features

| Module | Description |
|---|---|
| **Auth** | Login/Logout for Admin & Students, Change Password |
| **Students** | Add, View, Edit, Delete students with full profile |
| **Attendance** | Mark daily attendance by department/subject, percentage tracking |
| **Marks & Grades** | Enter exam results, auto grade calculation (O/A+/A/B+/B/C/F) |
| **Subjects** | Manage subjects per department and semester |
| **Timetable** | Set class schedules per department/semester |
| **Fees** | Add fees, record payments, track balance |
| **Notifications** | Send email notifications via SMTP to students & parents |
| **Events** | Manage university events and exam schedules |

---

## 🚀 Quick Start

```bash
# 1. Clone / extract the project
cd mrdu

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure SMTP (optional for email)
cp .env.example .env
# Edit .env with your SMTP credentials

# 4. Run the app
python app.py

# 5. Open browser
# http://localhost:5000
```

---

## 🔐 Default Login

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `admin123` |
| Student | (set by admin) | (set by admin) |

> ⚠️ Change the admin password after first login!

---

## 📧 SMTP Email Setup (Gmail)

1. Go to your Google Account → Security
2. Enable **2-Step Verification**
3. Go to **App Passwords** → Generate a 16-character password
4. Set in `.env`:
   ```
   MAIL_USERNAME=your_gmail@gmail.com
   MAIL_PASSWORD=xxxx xxxx xxxx xxxx
   ```

Emails are sent automatically for:
- ✅ Student Registration (welcome email)
- 💰 Fee addition & payment (to student + parent)
- 📊 Exam results published (to student + parent)
- 📢 Admin notifications (general, exam, events)

---

## 📁 Project Structure

```
mrdu/
├── app.py              # Flask app factory
├── config.py           # Configuration
├── models.py           # SQLAlchemy models
├── routes/
│   ├── auth.py         # Login/Logout
│   ├── admin.py        # Admin routes
│   ├── student.py      # Student routes
│   └── main.py         # Index redirect
├── utils/
│   └── email_utils.py  # SMTP email helpers
├── templates/
│   ├── base.html
│   ├── auth/
│   ├── admin/
│   └── student/
└── requirements.txt
```

---

## 🏗️ Tech Stack

- **Backend:** Flask, SQLAlchemy, Flask-Login, Flask-Mail
- **Database:** SQLite (dev) / PostgreSQL (prod)
- **Frontend:** Custom HTML/CSS (no external UI frameworks)
- **Email:** SMTP via Flask-Mail (Gmail/Outlook/custom)
