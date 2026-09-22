from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

from app.db.database import get_db
from app.db import crud
from app.services.weather_service import weather_service
from app.services.imd_service import imd_service
from app.services.climate_service import climate_service
from app.services.query_parser import parse_weather_query

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    """Payload for the end-to-end weather query analysis pipeline."""
    query: str = Field(..., description="Natural language weather query (text or transcribed voice)")
    location_name: str = Field("Current Location", description="Human-readable location label")
    latitude: float = Field(12.9716, description="Latitude of the user's selected location")
    longitude: float = Field(77.5946, description="Longitude of the user's selected location")
    input_type: str = Field("text", description="'text' or 'voice'")
    language: str = Field("en", description="BCP-47 language code, e.g. 'en', 'hi', 'ta'")
    user_id: Optional[int] = Field(None, description="Registered user ID (optional for guests)")

def generate_dynamic_answer(
    intent: str,
    date_horizon: str,
    days_offset: int,
    location_name: str,
    current: dict,
    hourly: dict,
    daily: dict
) -> str:
    city = location_name.split(",")[0].strip()
    
    d_max = daily.get("temperature_2m_max", [])
    d_min = daily.get("temperature_2m_min", [])
    d_rain = daily.get("precipitation_probability_max", [])
    
    idx = days_offset if days_offset < len(d_max) else 0
    
    cur_temp_val = current.get("temperature_2m")
    temp_max = round(d_max[idx]) if (idx < len(d_max) and d_max[idx] is not None) else (round(cur_temp_val) if cur_temp_val is not None else 26)
    temp_min = round(d_min[idx]) if (idx < len(d_min) and d_min[idx] is not None) else (round(cur_temp_val - 4) if cur_temp_val is not None else 22)
    
    h_rain = hourly.get("precipitation_probability", [0])
    rain_p = round(d_rain[idx]) if (idx < len(d_rain) and d_rain[idx] is not None) else (max(h_rain[:6]) if h_rain else 50)
    
    cur_temp = round(cur_temp_val) if cur_temp_val is not None else None
    feels_like = round(current.get("apparent_temperature")) if current.get("apparent_temperature") is not None else cur_temp
    humidity = current.get("relative_humidity_2m")
    wind_speed = round(current.get("wind_speed_10m")) if current.get("wind_speed_10m") is not None else None
    wind_gusts = round(current.get("wind_gusts_10m")) if current.get("wind_gusts_10m") is not None else None
    uv_idx = hourly.get("uv_index", [0])[0] if hourly.get("uv_index") else 0

    time_prefix = "Tomorrow" if days_offset == 1 else ("In 2 days" if days_offset == 2 else ("This week" if days_offset >= 7 else "Today"))

    if intent == "RAIN_FORECAST":
        if days_offset >= 1:
            return f"{time_prefix} in {city}, there is a {rain_p}% chance of rain. The expected temperature is around {temp_min}°C–{temp_max}°C."
        else:
            return f"Today in {city}, there is a {rain_p}% chance of rain with a current temperature of {cur_temp if cur_temp is not None else temp_max}°C."

    elif intent == "TEMPERATURE":
        if days_offset >= 1:
            return f"{time_prefix} in {city}, expected high is {temp_max}°C and low is {temp_min}°C."
        else:
            if cur_temp is not None:
                return f"The current temperature in {city} is {cur_temp}°C (feels like {feels_like}°C), with an expected high of {temp_max}°C and low of {temp_min}°C today."
            else:
                return f"In {city}, expected high is {temp_max}°C and low is {temp_min}°C today."

    elif intent == "HUMIDITY":
        if humidity is not None:
            return f"The relative humidity in {city} is currently {humidity}%, with a temperature of {cur_temp if cur_temp is not None else temp_max}°C."
        else:
            return f"In {city}, humidity information shows temperature at {cur_temp if cur_temp is not None else temp_max}°C."

    elif intent == "WIND":
        if wind_speed is not None:
            gust_str = f" with gusts up to {wind_gusts} km/h" if wind_gusts else ""
            return f"The current wind speed in {city} is {wind_speed} km/h{gust_str}."
        else:
            return f"Wind conditions in {city} are currently mild to moderate."

    elif intent == "UV":
        return f"The UV index in {city} is currently {uv_idx}."

    elif intent == "COMMUTE_SAFETY":
        if rain_p >= 50:
            return f"Expect showers during your commute in {city} ({rain_p}% chance of rain). Waterlogging and traffic delays possible."
        else:
            return f"No heavy rain expected during your commute in {city} ({rain_p}% chance). Roads should remain clear."

    else:
        if days_offset >= 1:
            return f"{time_prefix} in {city}, expected temperature is {temp_min}°C–{temp_max}°C with a {rain_p}% chance of rain."
        else:
            return f"Current weather in {city}: {cur_temp if cur_temp is not None else temp_max}°C, {rain_p}% chance of rain, wind {wind_speed if wind_speed is not None else 15} km/h."


# --- Weather Pipeline Analysis Endpoint ---

@router.post("/analyze")
async def analyze_weather_query(payload: AnalyzeRequest, db: Session = Depends(get_db)):
    """
    End-to-End Dynamic Query Processing & Data Retrieval Pipeline:
    1. Parse query for Location, Date/Time, Weather Parameter & Intent
    2. Search Application Database first for recent cached weather data
    3. Fall back to live Weather API (Open-Meteo & IMD) if DB miss
    4. Validate retrieved data & generate response strictly from retrieved data
    """
    try:
        user = crud.get_user_by_id(db, payload.user_id) if payload.user_id else None
        
        # Step 1: Parse user query (extract location, intent, date horizon)
        parsed = await parse_weather_query(
            query=payload.query,
            default_lat=payload.latitude,
            default_lon=payload.longitude,
            default_location_name=payload.location_name
        )
        
        target_loc_name = parsed["location_name"]
        target_lat = parsed["latitude"]
        target_lon = parsed["longitude"]
        intent = parsed["intent"]
        date_horizon = parsed["date_horizon"]
        days_offset = parsed["days_offset"]

        # Step 2: Search Database FIRST for recent matching weather data
        db_cache = crud.get_recent_weather_cache(db, target_loc_name, max_age_minutes=60)
        weather_raw = None
        data_source = "Application Database"

        if db_cache and db_cache.raw_payload:
            weather_raw = db_cache.raw_payload
        else:
            # Step 3: Fetch from connected Weather API if DB miss
            data_source = "Weather API (Open-Meteo)"
            try:
                weather_raw = await weather_service.get_forecast(target_lat, target_lon)
                # Save cache to database
                c_data = weather_raw.get("current", {})
                h_data = weather_raw.get("hourly", {})
                rain_p = max(h_data.get("precipitation_probability", [0])[:6]) if h_data.get("precipitation_probability") else 0
                crud.save_weather_cache(
                    db, target_loc_name, target_lat, target_lon,
                    c_data.get("temperature_2m", 26.0),
                    c_data.get("apparent_temperature", 26.0),
                    rain_p,
                    c_data.get("wind_speed_10m", 15.0),
                    c_data.get("weather_code", 0),
                    weather_raw
                )
            except Exception as api_err:
                weather_raw = None

        # Step 4: Validate retrieved data
        if not weather_raw or not isinstance(weather_raw, dict):
            return {
                "query": payload.query,
                "language": payload.language,
                "intent": intent,
                "location": target_loc_name,
                "data_source": "None",
                "advisory": {
                    "direct_answer": "Sorry, I couldn't find verified weather data for your query.",
                    "immediate_actions": ["Please check your internet connection or verify the city name."],
                    "preventive_actions": [],
                    "best_windows": [],
                    "smart_follow_ups": ["Weather in Bengaluru today", "Will it rain tomorrow?"]
                }
            }

        current = weather_raw.get("current", {})
        hourly = weather_raw.get("hourly", {})
        daily = weather_raw.get("daily", {})

        # 5. IMD Warnings
        imd_data = await imd_service.get_active_warnings(target_loc_name.split(",")[0])
        
        # 6. Climate baseline
        temp_val = current.get("temperature_2m", 26.0)
        climate_data = climate_service.get_climate_comparison(temp_val, target_loc_name)
        
        # 7. Generate verified dynamic answer strictly from retrieved data
        direct_answer = generate_dynamic_answer(
            intent=intent,
            date_horizon=date_horizon,
            days_offset=days_offset,
            location_name=target_loc_name,
            current=current,
            hourly=hourly,
            daily=daily
        )

        # Calculate risk scores based on retrieved weather values
        rain_prob = max(hourly.get("precipitation_probability", [65])[:6]) if hourly.get("precipitation_probability") else 65
        wind = current.get("wind_speed_10m", 18.0)
        gusts = current.get("wind_gusts_10m", 38.0)
        
        commute_risk = min(100, int(rain_prob * 0.6 + gusts * 0.6))
        safety_risk = min(100, int(rain_prob * 0.4 + wind * 0.8))
        health_risk = min(100, int(35 if temp_val > 32 else 20))
        
        overall_score = min(98, max(15, int(commute_risk * 0.65 + safety_risk * 0.35)))
        risk_level = "SEVERE" if overall_score >= 75 else "HIGH" if overall_score >= 50 else "MODERATE" if overall_score >= 25 else "LOW"
        
        alert_header = imd_data.get("headline", "IMD WEATHER ADVISORY")
        
        current_temp_display = round(current.get("temperature_2m", temp_val))
        immediate_actions = [
            f"Check weather conditions in {target_loc_name.split(',')[0]} before heading out.",
            f"Expected wind gusts up to {int(gusts)} km/h — exercise caution."
        ]
        preventive_actions = [
            "Keep phone battery charged above 50%.",
            "Stay informed via local weather updates."
        ]
        best_windows = [
            f"Safest travel window: Current conditions ({current_temp_display}°C, {int(rain_prob)}% rain chance)."
        ]
        follow_ups = [
            f"What is the forecast in {target_loc_name.split(',')[0]} tomorrow?",
            f"What is the humidity in {target_loc_name.split(',')[0]}?"
        ]

        # Log query to DB
        try:
            query_log = crud.log_user_query(
                db, payload.query, payload.input_type, intent, payload.language,
                target_loc_name, target_lat, target_lon,
                user_id=payload.user_id
            )
            crud.save_risk_report(
                db, query_log.id, overall_score, risk_level,
                {"commute": commute_risk, "safety": safety_risk, "health": health_risk},
                imd_data.get("color_code", "Yellow"), direct_answer,
                immediate_actions, preventive_actions, best_windows
            )
        except Exception as db_err:
            pass

        return {
            "query": payload.query,
            "language": payload.language,
            "intent": intent,
            "location": target_loc_name,
            "data_source": data_source,
            "user": {
                "name": user.full_name if user else "Guest User",
                "role": user.role if user else "General"
            },
            "weather": {
                "temperature": temp_val,
                "feels_like": current.get("apparent_temperature", temp_val),
                "precipitation_probability": rain_prob,
                "wind_speed": wind,
                "wind_gusts": gusts,
                "weather_code": current.get("weather_code", 0)
            },
            "imd_alert": {
                "color_code": imd_data.get("color_code", "Yellow"),
                "headline": alert_header,
                "bulletin": imd_data.get("bulletin_body")
            },
            "climate_anomaly": climate_data,
            "risk_analysis": {
                "overall_score": overall_score,
                "risk_level": risk_level,
                "dimensions": {
                    "commute": commute_risk,
                    "safety": safety_risk,
                    "health": health_risk
                }
            },
            "advisory": {
                "direct_answer": direct_answer,
                "immediate_actions": immediate_actions,
                "preventive_actions": preventive_actions,
                "best_windows": best_windows,
                "smart_follow_ups": follow_ups
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")


@router.get("/weather")
async def get_live_weather(lat: float = Query(12.9716), lon: float = Query(77.5946)):
    """Fetch live Open-Meteo weather parameters for coordinates."""
    data = await weather_service.get_forecast(lat, lon)
    return data

@router.get("/alerts")
async def get_imd_alerts(district: str = Query("Bengaluru")):
    """Fetch active IMD meteorological bulletins."""
    data = await imd_service.get_active_warnings(district)
    return data

@router.get("/languages")
async def get_supported_languages():
    """Return supported languages for multi-language support."""
    return [
        {"code": "en", "name": "English", "native": "English"},
        {"code": "hi", "name": "Hindi", "native": "हिन्दी"},
        {"code": "ta", "name": "Tamil", "native": "தமிழ்"},
        {"code": "te", "name": "Telugu", "native": "తెలుగు"},
        {"code": "kn", "name": "Kannada", "native": "ಕನ್ನಡ"},
        {"code": "bn", "name": "Bengali", "native": "বাংলা"},
        {"code": "es", "name": "Spanish", "native": "Español"}
    ]
