"""
User-facing routes: dashboard, profile, change-password, analyze,
what-if, history, analytics — all fully implemented.
"""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func

from database.models import BuildingAnalysis, WhatIfAnalysis
from extensions import db
from forms import AnalyzeForm, ChangePasswordForm, EditProfileForm, WhatIfForm


# ── Friendly label helpers ─────────────────────────────────────────────────────

def _analysis_labels(user_id):
    """Return {analysis_id: "Analysis N"} for one user.
    Oldest analysis = Analysis 1, next = Analysis 2, etc. (chronological).
    """
    rows = (BuildingAnalysis.query
            .filter_by(user_id=user_id)
            .order_by(BuildingAnalysis.created_at.asc(),
                      BuildingAnalysis.analysis_id.asc())
            .all())
    return {r.analysis_id: f"Analysis {i + 1}" for i, r in enumerate(rows)}


def _scenario_labels(user_id):
    """Return {scenario_id: "Scenario N"} for one user.
    Oldest scenario = Scenario 1, next = Scenario 2, etc. (chronological).
    """
    rows = (WhatIfAnalysis.query
            .filter_by(user_id=user_id)
            .order_by(WhatIfAnalysis.created_at.asc(),
                      WhatIfAnalysis.scenario_id.asc())
            .all())
    return {r.scenario_id: f"Scenario {i + 1}" for i, r in enumerate(rows)}

user_bp = Blueprint("user", __name__)


# ── Dashboard ──────────────────────────────────────────────────────────────────
@user_bp.route("/dashboard")
@login_required
def dashboard():
    analyses_count  = BuildingAnalysis.query.filter_by(
        user_id=current_user.user_id).count()
    scenarios_count = WhatIfAnalysis.query.filter_by(
        user_id=current_user.user_id).count()
    latest = (BuildingAnalysis.query
              .filter_by(user_id=current_user.user_id)
              .order_by(BuildingAnalysis.created_at.desc())
              .first())
    return render_template(
        "user/dashboard.html",
        analyses_count=analyses_count,
        scenarios_count=scenarios_count,
        latest=latest,
    )


# ── Profile ────────────────────────────────────────────────────────────────────
@user_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = EditProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.name = form.name.data
        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("user.profile"))

    analyses_count  = BuildingAnalysis.query.filter_by(
        user_id=current_user.user_id).count()
    scenarios_count = WhatIfAnalysis.query.filter_by(
        user_id=current_user.user_id).count()
    return render_template(
        "user/profile.html",
        form=form,
        analyses_count=analyses_count,
        scenarios_count=scenarios_count,
    )


# ── Change Password ────────────────────────────────────────────────────────────
@user_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            form.current_password.errors.append("Current password is incorrect.")
            return render_template("user/change_password.html", form=form)
        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash("Password changed successfully.", "success")
        return redirect(url_for("user.profile"))
    return render_template("user/change_password.html", form=form)


# ── Analyze ────────────────────────────────────────────────────────────────────
@user_bp.route("/analyze", methods=["GET", "POST"])
@login_required
def analyze():
    from ml.predictor import MODEL_VERSION, predict, validate_and_build_input

    form = AnalyzeForm()
    if form.validate_on_submit():
        raw = {
            "Relative Compactness":      str(form.relative_compactness.data),
            "Surface Area":              str(form.surface_area.data),
            "Wall Area":                 str(form.wall_area.data),
            "Roof Area":                 str(form.roof_area.data),
            "Overall Height":            str(form.overall_height.data),
            "Orientation":               str(form.orientation.data),
            "Glazing Area":              str(form.glazing_area.data),
            "Glazing Area Distribution": str(form.glazing_area_distribution.data),
        }
        X, errors = validate_and_build_input(raw)
        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("user/analyze.html", form=form)

        heating, cooling = predict(X)
        rec = BuildingAnalysis(
            user_id=current_user.user_id,
            relative_compactness=float(form.relative_compactness.data),
            surface_area=float(form.surface_area.data),
            wall_area=float(form.wall_area.data),
            roof_area=float(form.roof_area.data),
            overall_height=float(form.overall_height.data),
            orientation=int(form.orientation.data),
            glazing_area=float(form.glazing_area.data),
            glazing_area_distribution=int(form.glazing_area_distribution.data),
            predicted_heating_load=heating,
            predicted_cooling_load=cooling,
            model_version=MODEL_VERSION,
        )
        db.session.add(rec)
        db.session.commit()
        return redirect(url_for("user.analysis_detail", analysis_id=rec.analysis_id))

    return render_template("user/analyze.html", form=form)


# ── Analysis detail — owner-only ───────────────────────────────────────────────
@user_bp.route("/analysis/<int:analysis_id>")
@login_required
def analysis_detail(analysis_id):
    rec = BuildingAnalysis.query.get_or_404(analysis_id)
    if rec.user_id != current_user.user_id:
        abort(403)
    a_labels = _analysis_labels(current_user.user_id)
    return render_template("user/analysis_detail.html", record=rec,
                           a_labels=a_labels)


# ── What-If Analysis ───────────────────────────────────────────────────────────
@user_bp.route("/what-if", methods=["GET", "POST"])
@login_required
def what_if():
    from ml.predictor import MODEL_VERSION, predict, validate_and_build_input

    # All analyses belonging to current user (for the selector)
    user_analyses = (BuildingAnalysis.query
                     .filter_by(user_id=current_user.user_id)
                     .order_by(BuildingAnalysis.created_at.desc())
                     .all())

    # Pre-select an analysis (from query-string or first available)
    selected_id = request.args.get("analysis_id", type=int)
    if selected_id:
        original = BuildingAnalysis.query.get_or_404(selected_id)
        if original.user_id != current_user.user_id:
            abort(403)
    elif user_analyses:
        original = user_analyses[0]
        selected_id = original.analysis_id
    else:
        original = None

    form = WhatIfForm()

    # Build label maps for the selector display
    a_labels = _analysis_labels(current_user.user_id)

    # Pre-fill form with original values on GET when an analysis is selected
    if request.method == "GET" and original:
        orig_label = a_labels.get(original.analysis_id, f"Analysis {original.analysis_id}")
        form.scenario_name.data      = f"Scenario based on {orig_label}"
        form.relative_compactness.data = original.relative_compactness
        form.surface_area.data       = original.surface_area
        form.wall_area.data          = original.wall_area
        form.roof_area.data          = original.roof_area
        form.overall_height.data     = original.overall_height
        form.orientation.data        = str(original.orientation)
        form.glazing_area.data       = original.glazing_area
        form.glazing_area_distribution.data = str(original.glazing_area_distribution)

    if form.validate_on_submit():
        # Resolve original — from hidden field in POST (validated via DB, not trusted directly)
        orig_id = request.form.get("original_analysis_id", type=int)
        if not orig_id:
            flash("Please select an original analysis.", "danger")
            return render_template("user/what_if.html",
                                   form=form, user_analyses=user_analyses,
                                   original=original, selected_id=selected_id,
                                   a_labels=a_labels)
        orig = BuildingAnalysis.query.get_or_404(orig_id)
        if orig.user_id != current_user.user_id:
            abort(403)

        raw = {
            "Relative Compactness":      str(form.relative_compactness.data),
            "Surface Area":              str(form.surface_area.data),
            "Wall Area":                 str(form.wall_area.data),
            "Roof Area":                 str(form.roof_area.data),
            "Overall Height":            str(form.overall_height.data),
            "Orientation":               str(form.orientation.data),
            "Glazing Area":              str(form.glazing_area.data),
            "Glazing Area Distribution": str(form.glazing_area_distribution.data),
        }
        X, errors = validate_and_build_input(raw)
        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("user/what_if.html",
                                   form=form, user_analyses=user_analyses,
                                   original=orig, selected_id=orig_id,
                                   a_labels=a_labels)

        heating, cooling = predict(X)
        scenario = WhatIfAnalysis(
            user_id=current_user.user_id,
            original_analysis_id=orig.analysis_id,
            scenario_name=form.scenario_name.data.strip(),
            relative_compactness=float(form.relative_compactness.data),
            surface_area=float(form.surface_area.data),
            wall_area=float(form.wall_area.data),
            roof_area=float(form.roof_area.data),
            overall_height=float(form.overall_height.data),
            orientation=int(form.orientation.data),
            glazing_area=float(form.glazing_area.data),
            glazing_area_distribution=int(form.glazing_area_distribution.data),
            predicted_heating_load=heating,
            predicted_cooling_load=cooling,
            model_version=MODEL_VERSION,
        )
        db.session.add(scenario)
        db.session.commit()
        return redirect(url_for("user.scenario_detail",
                                scenario_id=scenario.scenario_id))

    return render_template("user/what_if.html",
                           form=form,
                           user_analyses=user_analyses,
                           original=original,
                           selected_id=selected_id,
                           a_labels=a_labels)


# ── Scenario detail — owner-only ───────────────────────────────────────────────
@user_bp.route("/scenario/<int:scenario_id>")
@login_required
def scenario_detail(scenario_id):
    scenario = WhatIfAnalysis.query.get_or_404(scenario_id)
    if scenario.user_id != current_user.user_id:
        abort(403)
    original = (BuildingAnalysis.query.get(scenario.original_analysis_id)
                if scenario.original_analysis_id else None)
    a_labels = _analysis_labels(current_user.user_id)
    s_labels = _scenario_labels(current_user.user_id)
    return render_template("user/scenario_detail.html",
                           scenario=scenario, original=original,
                           a_labels=a_labels, s_labels=s_labels)


# ── History ────────────────────────────────────────────────────────────────────
@user_bp.route("/history")
@login_required
def history():
    filter_type = request.args.get("type", "all")  # all | analyses | scenarios

    analyses = []
    scenarios = []

    if filter_type in ("all", "analyses"):
        analyses = (BuildingAnalysis.query
                    .filter_by(user_id=current_user.user_id)
                    .order_by(BuildingAnalysis.created_at.desc())
                    .all())

    if filter_type in ("all", "scenarios"):
        scenarios = (WhatIfAnalysis.query
                     .filter_by(user_id=current_user.user_id)
                     .order_by(WhatIfAnalysis.created_at.desc())
                     .all())

    a_labels = _analysis_labels(current_user.user_id)
    s_labels = _scenario_labels(current_user.user_id)
    return render_template(
        "user/history.html",
        analyses=analyses,
        scenarios=scenarios,
        filter_type=filter_type,
        a_labels=a_labels,
        s_labels=s_labels,
    )


# ── Analytics ──────────────────────────────────────────────────────────────────
@user_bp.route("/analytics")
@login_required
def analytics():
    analyses = (BuildingAnalysis.query
                .filter_by(user_id=current_user.user_id)
                .order_by(BuildingAnalysis.created_at.asc())
                .all())
    scenarios = (WhatIfAnalysis.query
                 .filter_by(user_id=current_user.user_id)
                 .order_by(WhatIfAnalysis.created_at.asc())
                 .all())

    # Build chart data using friendly labels (analyses already oldest-first)
    a_labels_map = _analysis_labels(current_user.user_id)
    s_labels_map = _scenario_labels(current_user.user_id)
    analysis_labels = [a_labels_map.get(a.analysis_id, f"Analysis {i+1}")
                       for i, a in enumerate(analyses)]
    heating_data     = [a.predicted_heating_load for a in analyses]
    cooling_data     = [a.predicted_cooling_load for a in analyses]

    # What-If comparison: original vs scenario heating
    wi_labels   = [s_labels_map.get(s.scenario_id, s.scenario_name[:20])
                   for s in scenarios]
    wi_orig_hl  = []
    wi_scen_hl  = []
    wi_orig_cl  = []
    wi_scen_cl  = []
    for s in scenarios:
        orig = (BuildingAnalysis.query.get(s.original_analysis_id)
                if s.original_analysis_id else None)
        wi_orig_hl.append(orig.predicted_heating_load if orig else None)
        wi_scen_hl.append(s.predicted_heating_load)
        wi_orig_cl.append(orig.predicted_cooling_load if orig else None)
        wi_scen_cl.append(s.predicted_cooling_load)

    return render_template(
        "user/analytics.html",
        analyses=analyses,
        scenarios=scenarios,
        analysis_labels=analysis_labels,
        heating_data=heating_data,
        cooling_data=cooling_data,
        wi_labels=wi_labels,
        wi_orig_hl=wi_orig_hl,
        wi_scen_hl=wi_scen_hl,
        wi_orig_cl=wi_orig_cl,
        wi_scen_cl=wi_scen_cl,
        a_labels=a_labels_map,
        s_labels=s_labels_map,
    )
