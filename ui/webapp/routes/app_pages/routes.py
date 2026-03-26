from flask import Blueprint, render_template

app_pages_bp = Blueprint("app_pages", __name__)


@app_pages_bp.get("/home")
def home():
    return render_template("pages/app/home.html")


@app_pages_bp.get("/settings")
def settings():
    return render_template("pages/app/settings.html")
