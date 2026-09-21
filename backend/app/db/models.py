from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base

class User(Base):
    """PostgreSQL Table for Registered Users & Profiles"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(100), default="Daily Commuter") # 'Daily Commuter', 'Farmer / Agriculturalist', 'Event Organizer', 'Outdoor Athlete'
    default_location = Column(String(200), default="Bengaluru, IN")
    default_latitude = Column(Float, default=12.9716)
    default_longitude = Column(Float, default=77.5946)
    preferred_language = Column(String(10), default="en")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class UserQueryLog(Base):
    """PostgreSQL Table for User Weather Inquiries"""
    __tablename__ = "user_query_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    query_text = Column(String(500), nullable=False)
    input_type = Column(String(50), default="text") # 'text' or 'voice'
    detected_intent = Column(String(100), nullable=True)
    language_code = Column(String(10), default="en")
    location_name = Column(String(200), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class WeatherCache(Base):
    """PostgreSQL Table for Cached Open-Meteo Weather Observations"""
    __tablename__ = "weather_cache"

    id = Column(Integer, primary_key=True, index=True)
    location_name = Column(String(200), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    temperature = Column(Float, nullable=False)
    feels_like = Column(Float, nullable=True)
    precipitation_prob = Column(Float, nullable=True)
    wind_speed = Column(Float, nullable=True)
    weather_code = Column(Integer, nullable=False)
    raw_payload = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class RiskReport(Base):
    """PostgreSQL Table for Synthesized AI Risk Assessments & Actions"""
    __tablename__ = "risk_reports"

    id = Column(Integer, primary_key=True, index=True)
    query_id = Column(Integer, nullable=True)
    overall_risk_score = Column(Integer, nullable=False)
    risk_level = Column(String(50), nullable=False)
    dimension_scores = Column(JSON, nullable=False)
    alert_color = Column(String(20), default="Green")
    direct_advisory = Column(Text, nullable=False)
    immediate_actions = Column(JSON, nullable=True)
    preventive_actions = Column(JSON, nullable=True)
    best_windows = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ImdAlertBulletin(Base):
    """PostgreSQL Table for Synoptic Meteorological Bulletins"""
    __tablename__ = "imd_bulletins"

    id = Column(Integer, primary_key=True, index=True)
    district_or_state = Column(String(200), nullable=False)
    color_code = Column(String(20), nullable=False)
    headline = Column(String(300), nullable=False)
    bulletin_body = Column(Text, nullable=False)
    valid_until = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
