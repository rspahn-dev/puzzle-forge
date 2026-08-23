from dotenv import load_dotenv
from flask import Flask

load_dotenv()

from config import Config
from extensions import db, login_manager, migrate, oauth


def create_app(config_class=Config):
    flask_app = Flask(__name__)
    flask_app.config.from_object(config_class)

    db.init_app(flask_app)
    migrate.init_app(flask_app, db)

    login_manager.init_app(flask_app)
    login_manager.login_view = "auth.login"

    oauth.init_app(flask_app)
    oauth.register(
        name="google",
        client_id=flask_app.config["GOOGLE_CLIENT_ID"],
        client_secret=flask_app.config["GOOGLE_CLIENT_SECRET"],
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

    from models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from account.routes import account_bp
    from auth.routes import auth_bp
    from games.word_search.routes import word_search_bp
    from games.word_scramble.routes import word_scramble_bp

    flask_app.register_blueprint(word_search_bp)
    flask_app.register_blueprint(word_scramble_bp)
    flask_app.register_blueprint(auth_bp)
    flask_app.register_blueprint(account_bp)

    return flask_app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
