from flask import Blueprint, render_template

account_bp = Blueprint("account", __name__)


@account_bp.get("/account")
def overview():
    return render_template("pages/account/overview.html")


@account_bp.get("/account/profile")
def profile():
    return render_template("pages/account/profile.html")


@account_bp.get("/account/preferences")
def preferences():
    return render_template("pages/account/preferences.html")


@account_bp.get("/account/security")
def security():
    return render_template("pages/account/security.html")
