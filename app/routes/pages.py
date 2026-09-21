from flask import Blueprint, render_template

pages_bp = Blueprint("pages", __name__)


@pages_bp.route("/")
def landing():
    return render_template("landing.html")


@pages_bp.route("/login")
def login_page():
    return render_template("login.html")


@pages_bp.route("/student/dashboard")
def student_dashboard():
    return render_template("student_dashboard.html")


@pages_bp.route("/cdpc/dashboard")
def cdpc_dashboard():
    return render_template("cdpc_dashboard.html")


@pages_bp.route("/company/dashboard")
def company_dashboard():
    return render_template("company_dashboard.html")
