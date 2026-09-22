"""
METEORA Query Parser
Extracts intent, location override, date/time horizon, and parameter focus
from natural-language weather queries. Pure Python — no external NLP libraries.
"""

import re
import httpx
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
import logging

logger = logging.getLogger("meteora.query_parser")


# ---------------------------------------------------------------------------
# Intent keyword maps
# ---------------------------------------------------------------------------

INTENT_KEYWORDS: Dict[str, List[str]] = {
    "RAIN_FORECAST": [
        "rain", "rainfall", "shower", "drizzle", "precipitat", "downpour",
        "thunderstorm", "thunder", "monsoon", "umbrella", "wet", "flood",
        "बारिश", "वर्षा", "மழை", "వర్షం", "ಮಳೆ", "বৃষ্টি", "lluvia",
    ],
    "TEMPERATURE": [
        "temperature", "temp", "hot", "cold", "warm", "cool", "heat",
        "freezing", "degrees", "celsius", "fahrenheit", "feels like",
        "तापमान", "गर्म", "ठंड", "வெப்பநிலை", "ఉష్ణోగ్రత", "ತಾಪಮಾನ", "temperatura",
    ],
    "WIND": [
        "wind", "gust", "breeze", "cyclone", "storm", "windy", "blow",
        "हवा", "காற்று", "గాలి", "ಗಾಳಿ", "বায়ু", "viento",
    ],
    "HUMIDITY": [
        "humidity", "humid", "moisture", "damp", "muggy", "sticky",
        "आर्द्रता", "ஈரப்பதம்", "తేమ", "ಆರ್ದ್ರತೆ", "আর্দ্রতা", "humedad",
    ],
    "UV": [
        "uv", "ultraviolet", "sunburn", "sunscreen", "sun index",
        "यूवी", "சூரிய ஒளி", "यूवी इंडेक्स",
    ],
    "ALERTS": [
        "alert", "warning", "advisory", "severe", "danger", "watch",
        "red alert", "orange alert", "yellow alert", "cyclone warning",
        "चेतावनी", "अलर्ट", "எச்சரிக்கை", "హెచ్చరిక", "ಎಚ್ಚರಿಕೆ", "সতর্কতা",
    ],
    "COMMUTE_SAFETY": [
        "commute", "drive", "driving", "traffic", "road", "travel", "bus",
        "office", "reach", "go out", "leave home", "यात्रा", "பயணம்", "ప్రయాణం",
    ],
    "OUTDOOR_EVENT": [
        "wedding", "event", "party", "outdoor", "concert", "picnic",
        "reception", "match", "festival", "celebration", "function",
        "शादी", "विवाह", "திருமணம்", "పెళ్ళి",
    ],
    "AGRICULTURE": [
        "crop", "farm", "spray", "pesticide", "fertilizer", "harvest",
        "planting", "irrigation", "soil", "खेती", "फसल",
    ],
    "ATHLETICS_HEALTH": [
        "sport", "cricket", "football", "run", "jog", "exercise", "workout",
        "outdoor activity", "yoga", "marathon", "gym",
    ],
    "CURRENT_WEATHER": [
        "current", "right now", "now", "today", "at the moment", "currently",
        "this morning", "this evening", "tonight", "abhi", "अभी", "இப்போது", "ఇప్పుడు",
    ],
    "GENERAL_FORECAST": [
        "forecast", "week", "weekend", "next few days", "coming days",
        "weekly", "भविष्यवाणी", "முன்னறிவிப்பு",
    ],
}

# ---------------------------------------------------------------------------
# Date/time horizon extraction
# ---------------------------------------------------------------------------

DATE_PATTERNS: Dict[str, List[str]] = {
    "today": ["today", "this morning", "tonight", "this evening", "this afternoon", "now", "right now", "currently", "आज", "இன்று", "ఈరోజు", "ಇಂದು", "আজ"],
    "tomorrow": ["tomorrow", "tmrw", "next day", "कल", "நாளை", "రేపు", "ನಾಳೆ", "আগামীকাল"],
    "day_after": ["day after tomorrow", "overmorrow"],
    "this_week": ["this week", "next few days", "coming days", "weekend", "इस सप्ताह"],
    "next_7_days": ["next 7 days", "next week", "weekly", "week forecast"],
}


def parse_date_horizon(query: str) -> Tuple[str, int]:
    """
    Returns (horizon_label, days_offset).
    days_offset=0 → today/current, 1 → tomorrow, 2 → day_after, 7 → week
    """
    q = query.lower()
    for label, keywords in DATE_PATTERNS.items():
        for kw in keywords:
            if kw in q:
                if label == "today":
                    return "today", 0
                elif label == "tomorrow":
                    return "tomorrow", 1
                elif label == "day_after":
                    return "day_after", 2
                elif label in ("this_week", "next_7_days"):
                    return "this_week", 7
    # Default: today/current
    return "today", 0


# ---------------------------------------------------------------------------
# Intent classification
# ---------------------------------------------------------------------------

def classify_intent(query: str) -> str:
    """Return the primary weather intent from the query."""
    q = query.lower()
    scores: Dict[str, int] = {}
    for intent, keywords in INTENT_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in q)
        if score:
            scores[intent] = score

    if not scores:
        return "GENERAL_WEATHER"

    # Resolve priority ties
    priority_order = [
        "ALERTS", "SEVERE_WEATHER", "RAIN_FORECAST", "TEMPERATURE",
        "COMMUTE_SAFETY", "OUTDOOR_EVENT", "AGRICULTURE", "ATHLETICS_HEALTH",
        "WIND", "HUMIDITY", "UV", "GENERAL_FORECAST", "CURRENT_WEATHER",
        "GENERAL_WEATHER",
    ]
    for intent in priority_order:
        if intent in scores:
            return intent

    return max(scores, key=lambda k: scores[k])


# ---------------------------------------------------------------------------
# Location extraction
# ---------------------------------------------------------------------------

# Common Indian cities + major world cities for quick lookup without geocoding
CITY_QUICK_TABLE: Dict[str, Tuple[str, float, float]] = {
    "bengaluru": ("Bengaluru, IN", 12.9716, 77.5946),
    "bangalore": ("Bengaluru, IN", 12.9716, 77.5946),
    "mumbai": ("Mumbai, IN", 19.0760, 72.8777),
    "bombay": ("Mumbai, IN", 19.0760, 72.8777),
    "delhi": ("New Delhi, IN", 28.6139, 77.2090),
    "new delhi": ("New Delhi, IN", 28.6139, 77.2090),
    "chennai": ("Chennai, IN", 13.0827, 80.2707),
    "madras": ("Chennai, IN", 13.0827, 80.2707),
    "kolkata": ("Kolkata, IN", 22.5726, 88.3639),
    "calcutta": ("Kolkata, IN", 22.5726, 88.3639),
    "hyderabad": ("Hyderabad, IN", 17.3850, 78.4867),
    "pune": ("Pune, IN", 18.5204, 73.8567),
    "ahmedabad": ("Ahmedabad, IN", 23.0225, 72.5714),
    "jaipur": ("Jaipur, IN", 26.9124, 75.7873),
    "surat": ("Surat, IN", 21.1702, 72.8311),
    "lucknow": ("Lucknow, IN", 26.8467, 80.9462),
    "kanpur": ("Kanpur, IN", 26.4499, 80.3319),
    "nagpur": ("Nagpur, IN", 21.1458, 79.0882),
    "indore": ("Indore, IN", 22.7196, 75.8577),
    "bhopal": ("Bhopal, IN", 23.2599, 77.4126),
    "patna": ("Patna, IN", 25.5941, 85.1376),
    "coimbatore": ("Coimbatore, IN", 11.0168, 76.9558),
    "visakhapatnam": ("Visakhapatnam, IN", 17.6868, 83.2185),
    "vizag": ("Visakhapatnam, IN", 17.6868, 83.2185),
    "kochi": ("Kochi, IN", 9.9312, 76.2673),
    "cochin": ("Kochi, IN", 9.9312, 76.2673),
    "thiruvananthapuram": ("Thiruvananthapuram, IN", 8.5241, 76.9366),
    "trivandrum": ("Thiruvananthapuram, IN", 8.5241, 76.9366),
    "guwahati": ("Guwahati, IN", 26.1445, 91.7362),
    "bhubaneswar": ("Bhubaneswar, IN", 20.2961, 85.8245),
    "chandigarh": ("Chandigarh, IN", 30.7333, 76.7794),
    "goa": ("Goa, IN", 15.2993, 74.1240),
    "panaji": ("Goa, IN", 15.4989, 73.8278),
    "shimla": ("Shimla, IN", 31.1048, 77.1734),
    "manali": ("Manali, IN", 32.2396, 77.1887),
    "varanasi": ("Varanasi, IN", 25.3176, 82.9739),
    "amritsar": ("Amritsar, IN", 31.6340, 74.8723),
    "agra": ("Agra, IN", 27.1767, 78.0081),
    # International
    "new york": ("New York, US", 40.7128, -74.0060),
    "london": ("London, UK", 51.5074, -0.1278),
    "tokyo": ("Tokyo, JP", 35.6762, 139.6503),
    "singapore": ("Singapore, SG", 1.3521, 103.8198),
    "dubai": ("Dubai, AE", 25.2048, 55.2708),
    "paris": ("Paris, FR", 48.8566, 2.3522),
    "sydney": ("Sydney, AU", -33.8688, 151.2093),
    "toronto": ("Toronto, CA", 43.6532, -79.3832),
    "berlin": ("Berlin, DE", 52.5200, 13.4050),
    "beijing": ("Beijing, CN", 39.9042, 116.4074),
    "shanghai": ("Shanghai, CN", 31.2304, 121.4737),
}

# Prepositions / phrases that indicate a location reference
LOCATION_PREPOSITIONS = [
    " in ", " at ", " for ", " near ", " around ", " over ", " across ",
    " of ", " within ", " across "
]


def extract_location_from_query(query: str) -> Optional[Tuple[str, float, float]]:
    """
    Try to extract a city/location mentioned in the query.
    Returns (name, lat, lon) or None if no explicit location found.
    First checks quick table, then tries geocoding API as fallback.
    """
    q_lower = query.lower()

    # 1. Direct quick-table lookup (most efficient)
    for city_key in sorted(CITY_QUICK_TABLE.keys(), key=len, reverse=True):
        if city_key in q_lower:
            return CITY_QUICK_TABLE[city_key]

    # 2. Try regex extraction after prepositions
    pattern = r'(?:in|at|for|near|around|of|over)\s+([A-Z][a-zA-Z\s]+?)(?:\s*[?,.\n]|$)'
    matches = re.findall(pattern, query, re.IGNORECASE)
    for match in matches:
        candidate = match.strip().lower()
        # Check quick table again with extracted candidate
        if candidate in CITY_QUICK_TABLE:
            return CITY_QUICK_TABLE[candidate]
        # Remove common trailing words
        for noise in [" today", " tomorrow", " this", " next", " now"]:
            candidate = candidate.replace(noise, "").strip()
        if candidate in CITY_QUICK_TABLE:
            return CITY_QUICK_TABLE[candidate]

    return None


async def geocode_city(city_name: str) -> Optional[Tuple[str, float, float]]:
    """Geocode a city name using Open-Meteo's geocoding API."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": city_name, "count": 1, "language": "en", "format": "json"}
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("results"):
                    r = data["results"][0]
                    country = r.get("country_code", "")
                    full_name = f"{r['name']}, {country}"
                    return (full_name, r["latitude"], r["longitude"])
    except Exception as e:
        logger.warning(f"Geocoding failed for '{city_name}': {e}")
    return None


# ---------------------------------------------------------------------------
# Parameter focus (which weather fields to emphasize)
# ---------------------------------------------------------------------------

FOCUS_MAP: Dict[str, List[str]] = {
    "RAIN_FORECAST": ["precipitation_probability", "precipitation", "weather_code"],
    "TEMPERATURE": ["temperature_2m", "apparent_temperature", "temperature_2m_max", "temperature_2m_min"],
    "WIND": ["wind_speed_10m", "wind_gusts_10m"],
    "HUMIDITY": ["relative_humidity_2m"],
    "UV": ["uv_index", "uv_index_max"],
    "ALERTS": ["weather_code", "precipitation_probability", "wind_gusts_10m"],
    "COMMUTE_SAFETY": ["precipitation_probability", "wind_speed_10m", "weather_code"],
    "OUTDOOR_EVENT": ["precipitation_probability", "weather_code", "wind_speed_10m", "uv_index"],
    "AGRICULTURE": ["precipitation_probability", "wind_speed_10m", "uv_index", "relative_humidity_2m"],
    "ATHLETICS_HEALTH": ["uv_index", "temperature_2m", "relative_humidity_2m", "precipitation_probability"],
    "CURRENT_WEATHER": ["temperature_2m", "weather_code", "precipitation_probability", "wind_speed_10m"],
    "GENERAL_FORECAST": ["temperature_2m_max", "temperature_2m_min", "precipitation_probability_max", "weather_code"],
    "GENERAL_WEATHER": ["temperature_2m", "weather_code", "precipitation_probability"],
}


def get_parameter_focus(intent: str) -> List[str]:
    return FOCUS_MAP.get(intent, FOCUS_MAP["GENERAL_WEATHER"])


# ---------------------------------------------------------------------------
# Main parse function
# ---------------------------------------------------------------------------

async def parse_weather_query(
    query: str,
    default_lat: float,
    default_lon: float,
    default_location_name: str
) -> Dict[str, Any]:
    """
    Full query parser. Returns a structured dict describing what data to fetch
    and what the user is asking about.

    Returns:
        {
            "intent": str,
            "date_horizon": str,          # "today" | "tomorrow" | "day_after" | "this_week"
            "days_offset": int,           # 0 | 1 | 2 | 7
            "location_name": str,
            "latitude": float,
            "longitude": float,
            "location_overridden": bool,  # True if query explicitly mentions a different city
            "parameter_focus": List[str],
            "query_date": str,            # ISO date string for the target day
        }
    """
    intent = classify_intent(query)
    date_horizon, days_offset = parse_date_horizon(query)

    # Determine target date
    target_date = datetime.now() + timedelta(days=days_offset)
    query_date = target_date.strftime("%Y-%m-%d")

    # Check for explicit location in query
    location_overridden = False
    lat, lon, loc_name = default_lat, default_lon, default_location_name

    extracted = extract_location_from_query(query)
    if extracted:
        candidate_name, candidate_lat, candidate_lon = extracted
        # Only override if it's different from the default
        if candidate_name.lower() != default_location_name.lower():
            loc_name = candidate_name
            lat = candidate_lat
            lon = candidate_lon
            location_overridden = True

    return {
        "intent": intent,
        "date_horizon": date_horizon,
        "days_offset": days_offset,
        "location_name": loc_name,
        "latitude": lat,
        "longitude": lon,
        "location_overridden": location_overridden,
        "parameter_focus": get_parameter_focus(intent),
        "query_date": query_date,
    }
