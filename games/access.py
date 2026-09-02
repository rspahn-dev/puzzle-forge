"""Anonymous usage gate: an anonymous visitor gets one free puzzle generation
(the offline word bank costs nothing to serve) before being asked to sign in
for more. Logged-in users are never gated here."""
from flask import jsonify, session
from flask_login import current_user

SESSION_KEY = "anon_generated"


def anon_generation_gate():
    """Call after basic input validation, right before actually building a
    puzzle. Returns a Flask response to return immediately if the visitor's
    free generation is already used; otherwise records the attempt and
    returns None so the route can proceed."""
    if current_user.is_authenticated:
        return None
    if session.get(SESSION_KEY):
        return jsonify({
            "error": "You've used your free puzzle. Sign in with Google to keep generating.",
            "login_required": True,
        }), 403
    session.permanent = True
    session[SESSION_KEY] = True
    return None
