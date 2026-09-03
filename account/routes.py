from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from crypto import encrypt_api_key
from extensions import db
from models import ApiKey

account_bp = Blueprint("account", __name__, url_prefix="/account")


@account_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    existing = ApiKey.query.filter_by(user_id=current_user.id, provider="anthropic").first()
    error = None

    if request.method == "POST":
        action = request.form.get("action")

        if action == "remove":
            if existing:
                db.session.delete(existing)
                db.session.commit()
            return redirect(url_for("account.index"))

        if action == "update_profile":
            display_name = (request.form.get("display_name") or "").strip()
            current_user.display_name = display_name or None
            db.session.commit()
            return redirect(url_for("account.index"))

        if action == "update_prefs":
            current_user.prefer_offline_wordbank = bool(request.form.get("prefer_offline_wordbank"))
            db.session.commit()
            return redirect(url_for("account.index"))

        new_key = (request.form.get("api_key") or "").strip()
        if not new_key.startswith("sk-ant-"):
            error = "That doesn't look like an Anthropic API key (should start with sk-ant-)."
        else:
            encrypted = encrypt_api_key(new_key)
            last4 = new_key[-4:]
            if existing:
                existing.encrypted_key = encrypted
                existing.last4 = last4
            else:
                db.session.add(ApiKey(user_id=current_user.id, provider="anthropic", encrypted_key=encrypted, last4=last4))
            db.session.commit()
            return redirect(url_for("account.index"))

    masked_key = f"sk-ant-...{existing.last4}" if existing else None
    return render_template("account/index.html", masked_key=masked_key, error=error)
