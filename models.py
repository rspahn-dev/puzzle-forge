import uuid
from datetime import datetime, timezone

from flask_login import UserMixin

from extensions import db


def _uuid():
    return str(uuid.uuid4())


def _now():
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    google_sub = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=_now)

    api_keys = db.relationship("ApiKey", backref="user", cascade="all, delete-orphan")


class ApiKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    provider = db.Column(db.String(32), nullable=False, default="anthropic")
    encrypted_key = db.Column(db.LargeBinary, nullable=False)
    last4 = db.Column(db.String(4))
    created_at = db.Column(db.DateTime, default=_now)

    __table_args__ = (db.UniqueConstraint("user_id", "provider", name="uq_apikey_user_provider"),)


class Puzzle(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", name="fk_puzzle_user_id"), nullable=True)
    game_type = db.Column(db.String(32), nullable=False)
    theme = db.Column(db.String(200))
    params = db.Column(db.JSON)
    data = db.Column(db.JSON, nullable=False)
    source = db.Column(db.String(16))
    created_at = db.Column(db.DateTime, default=_now)
