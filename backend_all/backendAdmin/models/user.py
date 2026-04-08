# models.py
from backendAdmin.extensions import db, bcrypt
from datetime import datetime


class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.set_password(password)

    def set_password(self, password):
        """设置密码并哈希加密"""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """验证密码"""
        return bcrypt.check_password_hash(self.password_hash, password)

    def to_dict(self):
        """返回用户信息（不包含密码）"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }

    def __repr__(self):
        return f'<User {self.username}>'