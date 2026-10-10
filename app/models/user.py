from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models.base import now
from app.models.unit import user_units


class User(UserMixin, db.Model):
    __tablename__ = "users"

    ROLES = {
        "student": "Student",
        "faculty": "Faculty",
        "dept_head": "Department Head",
        "student_affairs": "Student Affairs / Guidance",
        "admin": "System Administrator",
    }
    STAFF_ROLES = ("faculty", "dept_head", "student_affairs", "admin")

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120))
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, index=True)
    active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=now, nullable=False)
    last_login = db.Column(db.DateTime)

    units = db.relationship("Unit", secondary=user_units, backref="users", order_by="Unit.code")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self):
        return self.active

    @property
    def role_label(self):
        return self.ROLES.get(self.role, self.role)

    @property
    def is_staff(self):
        return self.role in self.STAFF_ROLES

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"
