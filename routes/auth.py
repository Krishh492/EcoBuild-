"""
Authentication routes: register, login, logout.
"""
from datetime import datetime, timezone

from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required, login_user, logout_user

from database.models import User
from extensions import db
from forms import LoginForm, RegistrationForm

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("user.dashboard"))

    form = RegistrationForm()
    if form.validate_on_submit():
        # Check for duplicate email (server-side)
        existing = User.query.filter_by(email=form.email.data).first()
        if existing:
            form.email.errors.append("An account with this email already exists.")
            return render_template("auth/register.html", form=form)

        user = User(
            name=form.name.data,
            email=form.email.data,
            role="user",
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Account created successfully. Please sign in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("user.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        # Generic error — never reveal which field is wrong
        if not user or not user.check_password(form.password.data):
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html", form=form)

        if not user.is_active:
            flash("Your account has been disabled. Please contact support.", "warning")
            return render_template("auth/login.html", form=form)

        # Update last_login
        user.last_login = datetime.now(timezone.utc)
        db.session.commit()

        login_user(user)

        if user.is_admin:
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("user.dashboard"))

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("public.home"))
