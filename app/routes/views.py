from flask import Blueprint, render_template
views_bp = Blueprint("views", __name__)

@views_bp.get("/")
def dashboard():
    return render_template("dashboard.html")

@views_bp.get("/graph")
def graph_view():
    return render_template("graph.html")