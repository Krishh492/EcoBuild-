"""
Public routes: home, about, how-it-works.
"""
from flask import Blueprint, render_template

public_bp = Blueprint("public", __name__)


@public_bp.route("/")
def home():
    return render_template("public/home.html")


@public_bp.route("/about")
def about():
    return render_template("public/about.html")


@public_bp.route("/how-it-works")
def how_it_works():
    return render_template("public/how_it_works.html")
