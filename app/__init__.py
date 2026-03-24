from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.documents import documents_bp
    from app.routes.admin import admin_bp
    from app.routes.notifications import notifications_bp
    from app.routes.messages import messages_bp
    from app.routes.rubrics import rubrics_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(messages_bp)
    app.register_blueprint(rubrics_bp)

    @app.context_processor
    def inject_globals():
        from flask import session
        from app.models import User
        current_user = User.query.get(session['user_id']) if 'user_id' in session else None
        demo_users   = User.query.order_by(User.role, User.full_name).all() if current_user else []
        return dict(current_user=current_user, demo_users=demo_users)

    with app.app_context():
        db.create_all()
        from app.seed import seed_data
        seed_data()

    return app
