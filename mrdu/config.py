import os

# Try to load .env file if python-dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'mrdu-secret-key-2024-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///mrdu.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ─── SMTP Email Configuration ─────────────────────────────────
    # Gmail: use your Gmail address + 16-char App Password (NOT your normal password)
    # To get App Password: Google Account → Security → 2-Step Verification → App Passwords
    MAIL_SERVER   = 'smtp.gmail.com'
    MAIL_PORT     = 587
    MAIL_USE_TLS  = True
    MAIL_USE_SSL  = False

    # ★ PUT YOUR GMAIL AND APP PASSWORD HERE ★
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'satishkunduuu@gmail.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'tykt vuif rwsk fjlv')

    MAIL_DEFAULT_SENDER = ('MRDU Notifications', MAIL_USERNAME)
    MAIL_MAX_EMAILS     = None
    MAIL_ASCII_ATTACHMENTS = False

    UNIVERSITY_NAME = 'Mallareddy Deemed University'
    UNIVERSITY_SHORT = 'MRDU'
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
