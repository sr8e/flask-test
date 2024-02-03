import sqlite3
from flask import Blueprint, abort, g, jsonify, url_for, request, render_template

from .auth import auth_required
from .db import get_db, get_users_genres, get_users_methods

blueprint = Blueprint("core", __name__, url_prefix="/api")


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


@blueprint.route("/choices")
@auth_required
def user_choices():
    con = get_db()
    res_m = get_users_methods(con, g.user, True)
    res_g = get_users_genres(con, g.user, True)

    response = {
        "genres": {r["id"]: r["name"] for r in res_g},
        "methods": {r["id"]: r["name"] for r in res_m},
    }

    return jsonify(response)

@blueprint.route("/payment", methods=("GET", "POST"))
@auth_required
def payment():
    con = get_db()
    if request.method == "POST":
        rows = request.get_json()

        # validation
        keys_req = ["amount", "date", "shop", "genre", "method"]
        keys_opt = ["attr", "note"]
        for i in range(len(rows)):
            for k in keys_req:
                if k not in rows[i]:
                    abort(400, {k: "required"})
            for k in keys_opt:
                if k not in rows[i]:
                    rows[i][k] = None

        try:
            con.executemany("insert into payment(`amount`, `date`, `shop`, `genre`, `attr`, `note`, `method`) values (:amount, :date, :shop, :genre, :attr, :note, :method)", rows)
        except sqlite3.ProgrammingError as e:
            abort(400, e.args)
        con.commit()
        return jsonify("success"), 200

    elif request.method == "GET":
        pass

