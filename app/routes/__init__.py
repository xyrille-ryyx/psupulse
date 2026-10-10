from app.routes.admin import bp as admin_bp
from app.routes.alerts import bp as alerts_bp
from app.routes.auth import bp as auth_bp
from app.routes.dashboard import bp as dashboard_bp
from app.routes.feedback import bp as feedback_bp
from app.routes.main import bp as main_bp
from app.routes.reports import bp as reports_bp

blueprints = [main_bp, auth_bp, feedback_bp, dashboard_bp, reports_bp, alerts_bp, admin_bp]
