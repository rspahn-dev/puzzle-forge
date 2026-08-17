import os


def _normalize_db_url(url):
    if url and url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = _normalize_db_url(os.environ.get("DATABASE_URL")) or "sqlite:///puzzles.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")

    # Render sets RENDER=true automatically; only require HTTPS-only cookies
    # in that environment, since local dev runs over plain http.
    SESSION_COOKIE_SECURE = bool(os.environ.get("RENDER"))
