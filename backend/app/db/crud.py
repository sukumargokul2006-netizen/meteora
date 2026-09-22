from sqlalchemy.orm import Session
from app.db.models import User, UserQueryLog, WeatherCache, RiskReport, ImdAlertBulletin
from typing import Dict, Any, Optional
import hashlib

def hash_password(password: str) -> str:
    """Hash password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(
    db: Session,
    email: str,
    full_name: str,
    password: str,
    role: str = "Daily Commuter",
    default_location: str = "Bengaluru, IN",
    lat: float = 12.9716,
    lon: float = 77.5946,
    lang: str = "en"
) -> User:
    """Create a new registered user in PostgreSQL."""
    hashed = hash_password(password)
    user = User(
        email=email,
        full_name=full_name,
        hashed_password=hashed,
        role=role,
        default_location=default_location,
        default_latitude=lat,
        default_longitude=lon,
        preferred_language=lang
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Retrieve user by unique email."""
    return db.query(User).filter(User.email == email).first()

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Retrieve user by ID."""
    return db.query(User).filter(User.id == user_id).first()

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Verify user credentials."""
    user = get_user_by_email(db, email)
    if not user:
        return None
    if user.hashed_password != hash_password(password):
        return None
    return user

def log_user_query(
    db: Session,
    query_text: str,
    input_type: str,
    intent: str,
    lang: str,
    loc_name: str,
    lat: float,
    lon: float,
    user_id: Optional[int] = None
) -> UserQueryLog:
    """Save user weather query to PostgreSQL."""
    record = UserQueryLog(
        user_id=user_id,
        query_text=query_text,
        input_type=input_type,
        detected_intent=intent,
        language_code=lang,
        location_name=loc_name,
        latitude=lat,
        longitude=lon
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

def save_weather_cache(
    db: Session,
    loc_name: str,
    lat: float,
    lon: float,
    temp: float,
    feels_like: float,
    precip_prob: float,
    wind: float,
    wmo_code: int,
    payload: Dict[str, Any]
) -> WeatherCache:
    """Save latest Open-Meteo observation."""
    record = WeatherCache(
        location_name=loc_name,
        latitude=lat,
        longitude=lon,
        temperature=temp,
        feels_like=feels_like,
        precipitation_prob=precip_prob,
        wind_speed=wind,
        weather_code=wmo_code,
        raw_payload=payload
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

def save_risk_report(
    db: Session,
    query_id: int,
    risk_score: int,
    risk_level: str,
    dim_scores: Dict[str, int],
    alert_color: str,
    advisory: str,
    immediate_actions: list,
    preventive_actions: list,
    best_windows: list
) -> RiskReport:
    """Save risk advisory report."""
    record = RiskReport(
        query_id=query_id,
        overall_risk_score=risk_score,
        risk_level=risk_level,
        dimension_scores=dim_scores,
        alert_color=alert_color,
        direct_advisory=advisory,
        immediate_actions=immediate_actions,
        preventive_actions=preventive_actions,
        best_windows=best_windows
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

def get_recent_weather_cache(
    db: Session,
    loc_name: str,
    max_age_minutes: int = 60
) -> Optional[WeatherCache]:
    """Retrieve recent weather data from database for matching location if available."""
    if not db:
        return None
    try:
        from datetime import datetime, timedelta
        city = loc_name.split(',')[0].strip()
        time_threshold = datetime.utcnow() - timedelta(minutes=max_age_minutes)
        record = db.query(WeatherCache).filter(
            WeatherCache.location_name.ilike(f"%{city}%"),
            WeatherCache.created_at >= time_threshold
        ).order_by(WeatherCache.created_at.desc()).first()
        return record
    except Exception:
        return None

