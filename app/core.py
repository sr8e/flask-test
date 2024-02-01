from flask import Blueprint, g, url_for

from .auth import auth_required
from .db import get_db

blueprint = Blueprint("core", __name__)


@blueprint.route("/")
def top():
    return f'yoyoyo <a href="{url_for("auth.login")}">log in </a>'


@blueprint.route("/mypage")
@auth_required
def mypage():
    con = get_db()
    res = con.execute("select `display_name` from user where `id` = ?", (g.user,))
    name = res.fetchone()[0]
    return f"yo welcome {name}"
