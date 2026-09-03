from flask import Blueprint, current_app, redirect, url_for
from flask_login import login_required, login_user, logout_user

from extensions import db, oauth
from models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login")
def login():
    redirect_uri = url_for("auth.callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route("/dev-login")
def dev_login():
    """Bypass Google entirely and log in as a local dummy account. Dev-only
    convenience: never active under gunicorn/production (app.debug is only
    ever True via `python app.py`'s explicit debug=True), for testing pages
    that require login when Google OAuth isn't set up or working locally."""
    if not current_app.debug:
        return "Not found", 404

    user = User.query.filter_by(google_sub="dev-local").first()
    if user is None:
        user = User(google_sub="dev-local", email="dev@localhost", display_name="Dev User")
        db.session.add(user)
        db.session.commit()

    login_user(user)
    return redirect(url_for("account.index"))


@auth_bp.route("/callback")
def callback():
    token = oauth.google.authorize_access_token()
    userinfo = token.get("userinfo") or oauth.google.userinfo(token=token)
    google_sub = userinfo["sub"]
    email = userinfo.get("email", "")
    name = userinfo.get("name", email)

    user = User.query.filter_by(google_sub=google_sub).first()
    if user is None:
        user = User(google_sub=google_sub, email=email, display_name=name)
        db.session.add(user)
    else:
        user.email = email
    db.session.commit()

    login_user(user)
    return redirect(url_for("account.index"))


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("word_search.index"))
