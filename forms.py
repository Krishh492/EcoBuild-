"""
WTForms form definitions for EcoBuild.
"""
from flask_wtf import FlaskForm
from wtforms import DecimalField, EmailField, PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    NumberRange,
    ValidationError,
)

# email-validator 2.x performs deliverability checks by default.
# Disable DNS/deliverability check — format validation only.
_email_validator = Email(
    message="Please enter a valid email address.",
    check_deliverability=False,
    allow_smtputf8=False,
)


class RegistrationForm(FlaskForm):
    name     = StringField("Full Name",
                           validators=[DataRequired(), Length(min=2, max=120)])
    email    = EmailField("Email",
                          validators=[DataRequired(), _email_validator, Length(max=254)])
    password = PasswordField("Password",
                             validators=[DataRequired(), Length(min=8,
                                         message="Password must be at least 8 characters.")])
    confirm  = PasswordField("Confirm Password",
                             validators=[DataRequired(),
                                         EqualTo("password",
                                                 message="Passwords must match.")])
    submit   = SubmitField("Create Account")

    def validate_name(self, field):
        field.data = field.data.strip()
        if not field.data:
            raise ValidationError("Name cannot be blank.")

    def validate_email(self, field):
        field.data = field.data.strip().lower()


class LoginForm(FlaskForm):
    email    = EmailField("Email",
                          validators=[DataRequired(), _email_validator])
    password = PasswordField("Password", validators=[DataRequired()])
    submit   = SubmitField("Sign In")

    def validate_email(self, field):
        field.data = field.data.strip().lower()


class EditProfileForm(FlaskForm):
    name   = StringField("Full Name",
                         validators=[DataRequired(), Length(min=2, max=120)])
    submit = SubmitField("Save Changes")

    def validate_name(self, field):
        field.data = field.data.strip()
        if not field.data:
            raise ValidationError("Name cannot be blank.")


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Current Password",
                                     validators=[DataRequired()])
    new_password     = PasswordField("New Password",
                                     validators=[DataRequired(),
                                                 Length(min=8,
                                                        message="Password must be at least 8 characters.")])
    confirm_password = PasswordField("Confirm New Password",
                                     validators=[DataRequired(),
                                                 EqualTo("new_password",
                                                         message="Passwords must match.")])
    submit           = SubmitField("Change Password")


class AnalyzeForm(FlaskForm):
    """Building parameter input form — ranges mirror feature_metadata.json."""
    relative_compactness = DecimalField(
        "Relative Compactness",
        places=2,
        validators=[DataRequired(), NumberRange(min=0.62, max=0.98,
                    message="Must be between 0.62 and 0.98.")],
    )
    surface_area = DecimalField(
        "Surface Area (m²)",
        places=2,
        validators=[DataRequired(), NumberRange(min=514.5, max=808.5,
                    message="Must be between 514.5 and 808.5.")],
    )
    wall_area = DecimalField(
        "Wall Area (m²)",
        places=2,
        validators=[DataRequired(), NumberRange(min=245.0, max=416.5,
                    message="Must be between 245.0 and 416.5.")],
    )
    roof_area = DecimalField(
        "Roof Area (m²)",
        places=2,
        validators=[DataRequired(), NumberRange(min=110.25, max=220.5,
                    message="Must be between 110.25 and 220.5.")],
    )
    overall_height = DecimalField(
        "Overall Height (m)",
        places=2,
        validators=[DataRequired(), NumberRange(min=3.5, max=7.0,
                    message="Must be between 3.5 and 7.0.")],
    )
    orientation = SelectField(
        "Orientation",
        choices=[("2", "2 — North"), ("3", "3 — East"),
                 ("4", "4 — South"), ("5", "5 — West")],
        validators=[DataRequired()],
    )
    glazing_area = DecimalField(
        "Glazing Area (fraction of floor area)",
        places=2,
        validators=[DataRequired(), NumberRange(min=0.0, max=0.4,
                    message="Must be between 0.0 and 0.4.")],
    )
    glazing_area_distribution = SelectField(
        "Glazing Area Distribution",
        choices=[
            ("0", "0 — Unknown"), ("1", "1 — Uniform"),
            ("2", "2 — North"),   ("3", "3 — East"),
            ("4", "4 — South"),   ("5", "5 — West"),
        ],
        validators=[DataRequired()],
    )
    submit = SubmitField("Predict Energy Loads")


class WhatIfForm(FlaskForm):
    """What-If scenario form — same 8 parameters as AnalyzeForm + scenario name."""
    scenario_name = StringField(
        "Scenario Name",
        validators=[DataRequired(), Length(min=1, max=120)],
    )
    relative_compactness = DecimalField(
        "Relative Compactness",
        places=2,
        validators=[DataRequired(), NumberRange(min=0.62, max=0.98,
                    message="Must be between 0.62 and 0.98.")],
    )
    surface_area = DecimalField(
        "Surface Area (m²)",
        places=2,
        validators=[DataRequired(), NumberRange(min=514.5, max=808.5,
                    message="Must be between 514.5 and 808.5.")],
    )
    wall_area = DecimalField(
        "Wall Area (m²)",
        places=2,
        validators=[DataRequired(), NumberRange(min=245.0, max=416.5,
                    message="Must be between 245.0 and 416.5.")],
    )
    roof_area = DecimalField(
        "Roof Area (m²)",
        places=2,
        validators=[DataRequired(), NumberRange(min=110.25, max=220.5,
                    message="Must be between 110.25 and 220.5.")],
    )
    overall_height = DecimalField(
        "Overall Height (m)",
        places=2,
        validators=[DataRequired(), NumberRange(min=3.5, max=7.0,
                    message="Must be between 3.5 and 7.0.")],
    )
    orientation = SelectField(
        "Orientation",
        choices=[("2", "2 — North"), ("3", "3 — East"),
                 ("4", "4 — South"), ("5", "5 — West")],
        validators=[DataRequired()],
    )
    glazing_area = DecimalField(
        "Glazing Area (fraction of floor area)",
        places=2,
        validators=[DataRequired(), NumberRange(min=0.0, max=0.4,
                    message="Must be between 0.0 and 0.4.")],
    )
    glazing_area_distribution = SelectField(
        "Glazing Area Distribution",
        choices=[
            ("0", "0 — Unknown"), ("1", "1 — Uniform"),
            ("2", "2 — North"),   ("3", "3 — East"),
            ("4", "4 — South"),   ("5", "5 — West"),
        ],
        validators=[DataRequired()],
    )
    submit = SubmitField("Run What-If Prediction")
