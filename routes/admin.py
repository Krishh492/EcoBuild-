"""
Admin routes — all require admin role, enforced server-side.
"""
from flask import Blueprint, render_template

from database.models import BuildingAnalysis, User, WhatIfAnalysis
from decorators import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# ── Admin Dashboard ────────────────────────────────────────────────────────────
@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    total_users     = User.query.count()
    total_analyses  = BuildingAnalysis.query.count()
    total_scenarios = WhatIfAnalysis.query.count()

    recent_users    = (User.query
                       .order_by(User.created_at.desc())
                       .limit(5).all())
    recent_analyses = (BuildingAnalysis.query
                       .order_by(BuildingAnalysis.created_at.desc())
                       .limit(5).all())
    return render_template(
        "admin/dashboard.html",
        total_users=total_users,
        total_analyses=total_analyses,
        total_scenarios=total_scenarios,
        recent_users=recent_users,
        recent_analyses=recent_analyses,
    )


# ── Users management ───────────────────────────────────────────────────────────
@admin_bp.route("/users")
@admin_required
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=all_users)


# ── Analyses management ────────────────────────────────────────────────────────
@admin_bp.route("/analyses")
@admin_required
def analyses():
    all_analyses = (BuildingAnalysis.query
                    .order_by(BuildingAnalysis.created_at.desc())
                    .all())
    # Build user lookup to avoid N+1 in template
    user_map = {u.user_id: u for u in User.query.all()}
    return render_template("admin/analyses.html",
                           analyses=all_analyses, user_map=user_map)


# ── Scenarios management ───────────────────────────────────────────────────────
@admin_bp.route("/scenarios")
@admin_required
def scenarios():
    all_scenarios = (WhatIfAnalysis.query
                     .order_by(WhatIfAnalysis.created_at.desc())
                     .all())
    user_map = {u.user_id: u for u in User.query.all()}
    return render_template("admin/scenarios.html",
                           scenarios=all_scenarios, user_map=user_map)


# ── Admin analytics ────────────────────────────────────────────────────────────
@admin_bp.route("/analytics")
@admin_required
def analytics():
    from sqlalchemy import func
    from extensions import db

    total_users     = User.query.count()
    total_analyses  = BuildingAnalysis.query.count()
    total_scenarios = WhatIfAnalysis.query.count()

    # All analyses ordered by date for charts
    all_analyses  = (BuildingAnalysis.query
                     .order_by(BuildingAnalysis.created_at.asc()).all())
    all_scenarios = (WhatIfAnalysis.query
                     .order_by(WhatIfAnalysis.created_at.asc()).all())

    analysis_labels = [f"#{a.analysis_id}" for a in all_analyses]
    heating_data    = [a.predicted_heating_load for a in all_analyses]
    cooling_data    = [a.predicted_cooling_load for a in all_analyses]

    # Per-user analysis counts (top 10)
    user_counts_raw = (db.session.query(User.name,
                                        func.count(BuildingAnalysis.analysis_id))
                       .join(BuildingAnalysis,
                             User.user_id == BuildingAnalysis.user_id,
                             isouter=True)
                       .group_by(User.user_id)
                       .order_by(func.count(BuildingAnalysis.analysis_id).desc())
                       .limit(10).all())
    user_count_labels = [r[0] for r in user_counts_raw]
    user_count_values = [r[1] for r in user_counts_raw]

    return render_template(
        "admin/analytics.html",
        total_users=total_users,
        total_analyses=total_analyses,
        total_scenarios=total_scenarios,
        all_analyses=all_analyses,
        analysis_labels=analysis_labels,
        heating_data=heating_data,
        cooling_data=cooling_data,
        user_count_labels=user_count_labels,
        user_count_values=user_count_values,
    )
