from dotenv import load_dotenv
from flask import Flask

load_dotenv()

from config import Config
from extensions import db, migrate


def create_app(config_class=Config):
    flask_app = Flask(__name__)
    flask_app.config.from_object(config_class)

    db.init_app(flask_app)
    migrate.init_app(flask_app, db)

    from games.word_search.routes import word_search_bp
    flask_app.register_blueprint(word_search_bp)

    return flask_app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
