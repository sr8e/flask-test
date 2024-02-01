import sqlite3
from pathlib import Path

import click
from flask import current_app, g


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])

    return g.db


def close_db(*args):
    db = g.pop("db", None)
    if db is not None:
        db.close()


@click.command("createdb")
def create_db():
    Path(current_app.config["DATABASE"]).unlink(missing_ok=True)
    db = get_db()
    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf-8"))
    click.echo("created db.")
