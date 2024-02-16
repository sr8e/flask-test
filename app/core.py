from datetime import datetime
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


@blueprint.route("/choices", methods=("GET",))
@auth_required
def user_choices():
    con = get_db()

    include_default = "include_default" in request.args
    res_m = get_users_methods(con, g.user, include_default)
    res_g = get_users_genres(con, g.user, include_default)

    response = {
        "genres": {r["id"]: r["name"] for r in res_g},
        "methods": {r["id"]: r["name"] for r in res_m},
    }

    return jsonify(response)


@blueprint.route("/choices/genre", methods=("GET", "POST"))
@auth_required
def user_genres_list_create():
    con = get_db()

    if request.method == "POST":
        values = request.get_json()
        try:
            con.executemany(
                "insert into genre (`name`, `user_id`) values (?, ?);",
                [(name, g.user) for name in values],
            )
            con.commit()
        except sqlite3.ProgrammingError as e:
            abort(400, e.args)

    include_default = "include_default" in request.args
    res = get_users_genres(con, g.user, include_default)

    return jsonify({r["id"]: r["name"] for r in res}), 200


@blueprint.route("/choices/method", methods=("GET", "POST"))
@auth_required
def user_methods_list_create():
    con = get_db()

    if request.method == "POST":
        values = request.get_json()
        try:
            con.executemany(
                "insert into method (`name`, `not_own`, `user_id`) values (?, ?, ?);",
                [(v["name"], v["not_own"], g.user) for v in values],
            )
            con.commit()
        except sqlite3.ProgrammingError as e:
            abort(400, e.args)
        except KeyError as e:
            abort(400, f"invalid data")

    include_default = "include_default" in request.args
    res = get_users_methods(con, g.user, include_default)

    return jsonify({r["id"]: r["name"] for r in res}), 200


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
            rows[i]["user_id"] = g.user

        try:
            con.executemany(
                "insert into payment(`amount`, `date`, `shop`, `genre`, `attr`, `note`, `method`, `user_id`) "
                "values (:amount, :date, :shop, :genre, :attr, :note, :method, :user_id)",
                rows,
            )
        except sqlite3.ProgrammingError as e:
            abort(400, e.args)
        con.commit()
        return jsonify("success"), 200

    elif request.method == "GET":
        res = con.execute(
            "select sum(payment.`amount`) as `total`, strftime('%Y-%m', payment.`date`) as `month`, "
            "payment.`genre`, method.`not_own` "
            "from payment left outer join method on payment.`method` = method.`id` "
            "where payment.`user_id` = ? group by payment.`genre`, `month`, method.`not_own`;",
            (g.user,),
        )
        return jsonify([dict(zip(r.keys(), r)) for r in res.fetchall()]), 200


@blueprint.route("/payment/detail", methods=("GET",))
@auth_required
def payment_detail():
    con = get_db()
    month_s = request.args.get("month", None)
    genre_s = request.args.get("genre", None)

    params = {"user_id": g.user}
    conds = []

    if month_s is not None:
        try:
            month = datetime.strptime(month_s, "%Y-%m").date()
        except ValueError:
            abort(400, f"invalid parameter: month: {month_s}")
        conds.append(
            "and `date` between date(:month, 'start of month') and "
            "date(:month, 'start of month', '+1 month', '-1 day') "
        )
        params["month"] = month
    
    if genre_s is not None:
        try:
            genre = int(genre_s)
        except ValueError:
            abort(400, f"invalid parameter: genre: {genre_s}")
        conds.append("and `genre` = :genre ")
        params["genre"] = genre
    
    sql = (
        "select payment.`id`, payment.`date`, payment.`amount`, payment.`shop`, "
        "payment.`genre`, payment.`attr`, payment.`note`, payment.`method`, "
        "genre.`name` as `gname`, method.`name` as `mname`, method.`not_own` "
        "from payment "
        "left outer join genre on payment.`genre` = genre.`id` "
        "left outer join method on payment.`method` = method.`id` "
        f"where payment.`user_id` = :user_id {''.join(conds)}"
        "order by payment.`date`"
    )
    res = con.execute(sql, params)
    return jsonify([dict(zip(row.keys(), row)) for row in res.fetchall()])


