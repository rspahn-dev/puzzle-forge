import uuid
from datetime import datetime, timezone

from extensions import db


def _uuid():
    return str(uuid.uuid4())


def _now():
    return datetime.now(timezone.utc)


class Puzzle(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    user_id = db.Column(db.Integer, nullable=True)  # FK added once User model exists
    game_type = db.Column(db.String(32), nullable=False)
    theme = db.Column(db.String(200))
    params = db.Column(db.JSON)
    data = db.Column(db.JSON, nullable=False)
    source = db.Column(db.String(16))
    created_at = db.Column(db.DateTime, default=_now)
