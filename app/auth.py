import base64
import functools
import hashlib
import json
import os
import urllib
from datetime import timedelta

import requests
from flask import (
    Blueprint, current_app, g, redirect, request, session, url_for
)

from .db import get_db
from .utils import now

blueprint = Blueprint("auth", __name__, url_prefix="/auth")


def generate_openid_request_url(state):
    qparam = urllib.parse.urlencode(
        {
            "client_id": current_app.config["CLIENT_ID"],
            "scope": "openid profile",
            "redirect_uri": url_for("auth.check", _external=True),
            "state": state,
            "response_type": "code",
        }
    )
    return f"https://accounts.google.com/o/oauth2/auth?{qparam}"


def verify_idtoken(token):
    body = token.split(".")[1]
    body += "=" * (-len(body) % 4)

    return json.loads(base64.urlsafe_b64decode(body))


@blueprint.before_app_request
def check_login_state():
    g.user = session.get("id", None)
    g.exp = session.get("expires_at", None)


@blueprint.route("/login", methods=("GET",))
def login():
    if (
        getattr(g, "user", None) is not None
        and (exp := getattr(g, "exp", None)) is not None
        and exp >= now()
    ):
        return redirect(url_for("core.mypage"))

    session.clear()
    state = hashlib.sha256(os.urandom(64)).hexdigest()[:16]
    session["state"] = state
    return f'<a href="{generate_openid_request_url(state)}">log in with google</a>'


@blueprint.route("/callback")
def check():
    if request.args.get("state") != session["state"]:
        return "invalid state"

    res = requests.post(
        "https://www.googleapis.com/oauth2/v4/token",
        data={
            "code": request.args.get("code"),
            "client_id": current_app.config["CLIENT_ID"],
            "client_secret": current_app.config["CLIENT_SECRET"],
            "redirect_uri": url_for("auth.check", _external=True),
            "grant_type": "authorization_code",
        },
    ).json()

    data = verify_idtoken(res["id_token"])
    sub = data["sub"]
    con = get_db()
    res = con.execute("select count(*) from user where `id` = ?", (sub,))
    if res.fetchone()[0] == 0:
        # new user
        con.execute(
            "insert into user(`id`, `display_name`) values (?, ?)", (sub, data["name"])
        )
        con.commit()

    session.clear()
    session["id"] = sub
    session["expires_at"] = now() + timedelta(hours=2)

    return redirect(url_for("core.mypage"))


@blueprint.route("/logout")
def logout():
    session.clear()
    g.pop("user")
    return redirect(url_for("core.top"))


# decorator
def auth_required(view):
    @functools.wraps(view)
    def _wrapper(*args, **kwargs):
        if g.user is None or g.exp < now():
            return redirect(url_for("auth.login"))

        return view(*args, **kwargs)

    return _wrapper
