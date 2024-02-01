from pathlib import Path

from flask import Flask

from . import auth, core, db


def create_app():
    app = Flask(__name__)

    app.config.from_mapping({"DATABASE": Path(app.instance_path) / "data.db"})

    app.config.from_pyfile("config.py", silent=True)

    app.teardown_appcontext(db.close_db)
    app.cli.add_command(db.create_db)

    app.register_blueprint(auth.blueprint)
    app.register_blueprint(core.blueprint)

    return app