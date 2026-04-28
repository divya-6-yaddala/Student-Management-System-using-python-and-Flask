from flask import Flask
from extensions import db, login_manager, mail
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure mail is not suppressed
    app.config['MAIL_SUPPRESS_SEND'] = False
    app.config['TESTING'] = False

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    from routes.auth import auth
    from routes.admin import admin
    from routes.student import student
    from routes.main import main

    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(admin, url_prefix='/admin')
    app.register_blueprint(student, url_prefix='/student')
    app.register_blueprint(main)

    with app.app_context():
        db.create_all()
        from models import User, Admin
        from werkzeug.security import generate_password_hash
        if not User.query.filter_by(role='admin').first():
            admin_user = User(
                username='admin',
                email='admin@mrdu.edu.in',
                password_hash=generate_password_hash('admin123'),
                role='admin',
                full_name='MRDU Administrator'
            )
            db.session.add(admin_user)
            db.session.add(Admin(user=admin_user, department='Administration'))
            db.session.commit()
            print("[MRDU] Default admin created: admin / admin123")

        # Print SMTP config on startup so you can verify
        print(f"[MRDU] SMTP → {app.config['MAIL_SERVER']}:{app.config['MAIL_PORT']}")
        print(f"[MRDU] Mail user → {app.config['MAIL_USERNAME']}")

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
