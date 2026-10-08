"""
SQLAlchemy models for EcoBuild.
Three application tables: users, building_analysis, what_if_analysis.
"""
from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    user_id    = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(120), nullable=False)
    email      = db.Column(db.String(254), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role       = db.Column(db.String(10), nullable=False, default="user")   # "user" | "admin"
    is_active  = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc), nullable=False)
    last_login = db.Column(db.DateTime(timezone=True), nullable=True)

    # Relationships
    analyses  = db.relationship("BuildingAnalysis",  back_populates="user",
                                 foreign_keys="BuildingAnalysis.user_id",
                                 lazy="dynamic", cascade="all, delete-orphan")
    scenarios = db.relationship("WhatIfAnalysis", back_populates="user",
                                 foreign_keys="WhatIfAnalysis.user_id",
                                 lazy="dynamic", cascade="all, delete-orphan")

    # Flask-Login requires get_id() to return a string
    def get_id(self):
        return str(self.user_id)

    # Password helpers — never expose hash
    def set_password(self, plaintext: str):
        self.password_hash = generate_password_hash(plaintext)

    def check_password(self, plaintext: str) -> bool:
        return check_password_hash(self.password_hash, plaintext)

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    def __repr__(self):
        return f"<User {self.user_id} {self.email}>"


class BuildingAnalysis(db.Model):
    __tablename__ = "building_analysis"

    analysis_id   = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(db.Integer, db.ForeignKey("users.user_id",
                              ondelete="CASCADE"), nullable=False, index=True)

    # Input features (8 UCI ENB2012 features)
    relative_compactness        = db.Column(db.Float, nullable=False)
    surface_area                = db.Column(db.Float, nullable=False)
    wall_area                   = db.Column(db.Float, nullable=False)
    roof_area                   = db.Column(db.Float, nullable=False)
    overall_height              = db.Column(db.Float, nullable=False)
    orientation                 = db.Column(db.Integer, nullable=False)
    glazing_area                = db.Column(db.Float, nullable=False)
    glazing_area_distribution   = db.Column(db.Integer, nullable=False)

    # Predictions
    predicted_heating_load = db.Column(db.Float, nullable=True)
    predicted_cooling_load = db.Column(db.Float, nullable=True)
    model_version          = db.Column(db.String(50), nullable=True)
    created_at             = db.Column(db.DateTime(timezone=True),
                                       default=lambda: datetime.now(timezone.utc),
                                       nullable=False)

    # Relationships
    user      = db.relationship("User", back_populates="analyses",
                                foreign_keys=[user_id])
    scenarios = db.relationship("WhatIfAnalysis",
                                back_populates="original_analysis",
                                foreign_keys="WhatIfAnalysis.original_analysis_id",
                                lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<BuildingAnalysis {self.analysis_id} user={self.user_id}>"


class WhatIfAnalysis(db.Model):
    __tablename__ = "what_if_analysis"

    scenario_id          = db.Column(db.Integer, primary_key=True)
    user_id              = db.Column(db.Integer, db.ForeignKey("users.user_id",
                                     ondelete="CASCADE"), nullable=False, index=True)
    original_analysis_id = db.Column(db.Integer,
                                     db.ForeignKey("building_analysis.analysis_id",
                                                   ondelete="CASCADE"),
                                     nullable=True, index=True)
    scenario_name        = db.Column(db.String(120), nullable=False, default="Scenario")

    # Input features (mirrored from BuildingAnalysis)
    relative_compactness        = db.Column(db.Float, nullable=False)
    surface_area                = db.Column(db.Float, nullable=False)
    wall_area                   = db.Column(db.Float, nullable=False)
    roof_area                   = db.Column(db.Float, nullable=False)
    overall_height              = db.Column(db.Float, nullable=False)
    orientation                 = db.Column(db.Integer, nullable=False)
    glazing_area                = db.Column(db.Float, nullable=False)
    glazing_area_distribution   = db.Column(db.Integer, nullable=False)

    # Predictions
    predicted_heating_load = db.Column(db.Float, nullable=True)
    predicted_cooling_load = db.Column(db.Float, nullable=True)
    model_version          = db.Column(db.String(50), nullable=True)
    created_at             = db.Column(db.DateTime(timezone=True),
                                       default=lambda: datetime.now(timezone.utc),
                                       nullable=False)

    # Relationships
    user              = db.relationship("User", back_populates="scenarios",
                                        foreign_keys=[user_id])
    original_analysis = db.relationship("BuildingAnalysis",
                                        back_populates="scenarios",
                                        foreign_keys=[original_analysis_id])

    def __repr__(self):
        return f"<WhatIfAnalysis {self.scenario_id} user={self.user_id}>"
