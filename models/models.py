# models/models.py
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Athlete(db.Model):
    """بيانات الرياضي"""
    __tablename__ = 'athletes'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=True)
    clinical_id = db.Column(db.String(50), nullable=True, unique=True)
    sport = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    reports = db.relationship('GenomicsReport', backref='athlete', lazy=True, cascade="all, delete-orphan")


class GenomicsReport(db.Model):
    """سجل التقرير الجيني المستخرج من الـ AI"""
    __tablename__ = 'genomics_reports'
    id = db.Column(db.Integer, primary_key=True)
    athlete_id = db.Column(db.Integer, db.ForeignKey('athletes.id'), nullable=True)
    filename = db.Column(db.String(255), nullable=True)
    raw_text = db.Column(db.Text, nullable=True)
    generated_report = db.Column(db.Text, nullable=False)
    
    # مقاييس التوكينز والتكلفة
    prompt_tokens = db.Column(db.Integer, default=0)
    completion_tokens = db.Column(db.Integer, default=0)
    total_tokens = db.Column(db.Integer, default=0)
    cost_usd = db.Column(db.Float, default=0.0)
    latency_sec = db.Column(db.Float, default=0.0)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))