from flask import Blueprint, render_template

public_bp = Blueprint("public", __name__)


@public_bp.get("/")
def landing():
    return render_template("pages/public/home.html")


@public_bp.get("/login")
def login():
    return render_template("pages/public/login.html")


@public_bp.get("/register")
def register():
    return render_template("pages/public/register.html")


@public_bp.get("/forgot-password")
def forgot_password():
    return render_template("pages/public/forgot_password.html")


@public_bp.get("/reset-password")
def reset_password():
    return render_template("pages/public/reset_password.html")


@public_bp.get("/accept-access")
def accept_access():
    return render_template("pages/public/accept_access.html")


@public_bp.get("/logout")
def logout():
    return render_template("pages/public/logout.html")
