from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, EmailStr
from typing import Dict, Any, List, Optional

from app.db.database import get_db
from app.db import crud
from app.services.weather_service import weather_service
from app.services.imd_service import imd_service
from app.services.hf_service import hf_service
from app.services.climate_service import climate_service

router = APIRouter()

@router.get("/huggingface/datasets")
async def list_huggingface_datasets():
    """List datasets configured for Meteora's Hugging Face workspace."""
    return await hf_service.list_datasets()

# --- Auth Request & Response Schemas ---
class UserRegisterRequest(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: str = "Daily Commuter"
    default_location: str = "Bengaluru, IN"
    latitude: float = 12.9716
    longitude: float = 77.5946
    language_preference: str = "en"

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserProfileResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    default_location: str
    default_latitude: float
    default_longitude: float
    preferred_language: str

class AnalyzeRequest(BaseModel):
    query: str = Field(..., example="Will it rain during my evening commute?")
    location_name: str = Field(default="Bengaluru, IN")
    latitude: float = Field(default=12.9716)
    longitude: float = Field(default=77.5946)
    input_type: str = Field(default="text") # 'text' or 'voice'
    language: str = Field(default="en") # 'en', 'hi', 'ta', 'te', 'kn', 'bn', 'es'
    user_id: Optional[int] = None

# Multi-language translation dictionary for backend responses
TRANSLATIONS = {
    "hi": {
        "commute_yes": "हाँ, आपकी शाम की यात्रा के दौरान बारिश की संभावना है (शाम 5:45 - 7:30)। प्रमुख सड़कों पर जलभराव संभव है।",
        "commute_no": "आपकी शाम की यात्रा के दौरान भारी बारिश की संभावना नहीं है। सड़कें साफ रहेंगी।",
        "alert_yellow": "आईएमडी पीली चेतावनी: गरज के साथ तेज हवाएं",
        "imm_1": "शाम 4:45 से पहले निकलें या रात 7:45 के बाद यात्रा करें।",
        "imm_2": "हवा प्रतिरोधी छाता साथ रखें; तेज हवाएं चल सकती हैं।",
        "prev_1": "रेलवे अंडरपास और जलभराव वाले चौराहों से बचें।",
        "prev_2": "ट्रैफिक जाम की स्थिति के लिए फोन चार्ज रखें।",
        "win_1": "सबसे सुरक्षित यात्रा समय: अभी से शाम 4:45 तक।",
        "follow_1": "शाम को बारिश किस समय सबसे तेज होगी?",
        "follow_2": "क्या कल सुबह की यात्रा में भी बारिश होगी?"
    },
    "ta": {
        "commute_yes": "ஆம், உங்கள் மாலை பயணத்தின் போது மழை பெய்ய வாய்ப்புள்ளது (மாலை 5:45 - 7:30). முக்கிய சாலைகளில் நீர் தேங்கலாம்.",
        "commute_no": "உங்கள் பயணத்தின் போது மழை பெய்ய வாய்ப்பில்லை. போக்குவரத்து சீராக இருக்கும்.",
        "alert_yellow": "வானிலை மஞ்சள் எச்சரிக்கை: இடியுடன் கூடிய பலத்த காற்று",
        "imm_1": "மாலை 4:45 க்கு முன் அல்லது 7:45 க்குப் பிறகு புறப்படுங்கள்.",
        "imm_2": "காற்றுக்கு தாங்கக்கூடிய குடையை உடன் எடுத்துச் செல்லுங்கள்.",
        "prev_1": "தாழ்வான ரயில்வே பாலங்கள் மற்றும் நீர் தேங்கும் பகுதிகளைத் தவிர்க்கவும்.",
        "prev_2": "போக்குவரத்து நெரிசலுக்காக மொபைல் பேட்டரியை முழுமையாக வைத்திருக்கவும்.",
        "win_1": "பாதுகாப்பான பயண நேரம்: தற்போது முதல் மாலை 4:45 வரை.",
        "follow_1": "இன்று மாலை எந்த நேரத்தில் மழை அதிகமாக இருக்கும்?",
        "follow_2": "நாளை காலை பயணத்திலும் மழை பெய்யுமா?"
    },
    "te": {
        "commute_yes": "అవును, మీ సాయంత్రం ప్రయాణంలో వర్షం పడే అవకాశం ఉంది (సాయంత్రం 5:45 - 7:30). రహదారులపై నీరు నిలిచే ప్రమాదం ఉంది.",
        "commute_no": "మీ ప్రయాణంలో వర్షం పడే అవకాశం తక్కువ. ప్రయాణం సాఫీగా సాగుతుంది.",
        "alert_yellow": "వాతావరణ శాఖ ఎల్లో అలర్ట్: ఈదురు గాలులతో కూడిన వర్షం",
        "imm_1": "సాయంత్రం 4:45 కంటే ముందే లేదా 7:45 తర్వాత బయలుదేరండి.",
        "imm_2": "గాలికి తట్టుకునే గొడుగును వెంట ఉంచుకోండి.",
        "prev_1": "నీరు నిలిచే అండర్‌పాస్‌లు మరియు లోతట్టు ప్రాంతాలను నివారించండి.",
        "prev_2": "ట్రాఫిక్ ఆలస్యం కోసం ఫోన్‌ను ఛార్జ్ చేసి ఉంచుకోండి.",
        "win_1": "సురక్షితమైన ప్రయాణ సమయం: ప్రస్తుత సమయం నుండి సాయంత్రం 4:45 వరకు.",
        "follow_1": "ఈ సాయంత్రం ఏ సమయంలో వర్షం ఎక్కువగా ఉంటుంది?",
        "follow_2": "రేపు ఉదయం ప్రయాణంలో కూడా వర్షం పడుతుందా?"
    },
    "kn": {
        "commute_yes": "ಹೌದು, ನಿಮ್ಮ ಸಂಜೆಯ ಪ್ರಯಾಣದ ಸಮಯದಲ್ಲಿ ಮಳೆಯಾಗುವ ಸಾಧ್ಯತೆಯಿದೆ (ಸಂಜೆ 5:45 - 7:30). ರಸ್ತೆಗಳಲ್ಲಿ ನೀರು ನಿಲ್ಲುವ ಸಾಧ್ಯತೆಯಿದೆ.",
        "commute_no": "ನಿಮ್ಮ ಪ್ರಯಾಣದ ಸಮಯದಲ್ಲಿ ಮಳೆಯಾಗುವ ಸಾಧ್ಯತೆ ಕಡಿಮೆ. ರಸ್ತೆಗಳು ಸಾಮಾನ್ಯವಾಗಿರುತ್ತವೆ.",
        "alert_yellow": "ಹವಾಮಾನ ಇಲಾಖೆ ಹಳದಿ ಎಚ್ಚರಿಕೆ: ಬಿರುಗಾಳಿ ಸಹಿತ ಮಳೆ",
        "imm_1": "ಸಂಜೆ 4:45 ಕ್ಕಿಂತ ಮೊದಲು ಅಥವಾ 7:45 ರ ನಂತರ ಪ್ರಯಾಣಿಸಿ.",
        "imm_2": "ಗಾಳಿಗೆ ತಡೆಯುವ ಬಲವಾದ ಛತ್ರಿಯನ್ನು ಕೊಂಡೊಯ್ಯಿರಿ.",
        "prev_1": "ನೀರು ತುಂಬುವ ಅಂಡರ್‌ಪಾಸ್‌ಗಳು ಮತ್ತು ತಗ್ಗು ಪ್ರದೇಶಗಳನ್ನು ತಪ್ಪಿಸಿ.",
        "prev_2": "ಸಂಚಾರ ದಟ್ಟಣೆಗಾಗಿ ಮೊಬೈಲ್ ಚಾರ್ಜ್ ಇರಿಸಿಕೊಳ್ಳಿ.",
        "win_1": "ಸುರಕ್ಷಿತ ಪ್ರಯಾಣದ ಸಮಯ: ಈಗಿನಿಂದ ಸಂಜೆ 4:45 ರವರೆಗೆ.",
        "follow_1": "ಇಂದು ಸಂಜೆ ಯಾವ ಸಮಯದಲ್ಲಿ ಮಳೆ ಹೆಚ್ಚಾಗುತ್ತದೆ?",
        "follow_2": "ನಾಳೆ ಬೆಳಗಿನ ಪ್ರಯಾಣದಲ್ಲೂ ಮಳೆಯಾಗುವುದೇ?"
    },
    "bn": {
        "commute_yes": "হ্যাঁ, আপনার সন্ধ্যার যাতায়াতের সময় বৃষ্টির সম্ভাবনা রয়েছে (সন্ধ্যা ৫:৪৫ - ৭:৩০)। রাস্তায় জল জমার সম্ভাবনা আছে।",
        "commute_no": "আপনার যাতায়াতের সময় বৃষ্টির সম্ভাবনা কম। রাস্তা স্বাভাবিক থাকবে।",
        "alert_yellow": "আবহাওয়া হলুদ সতর্কতা: দমকা হাওয়াসহ বজ্রপাত",
        "imm_1": "বিকেল ৪:৪৫ এর আগে অথবা সন্ধ্যা ৭:৪৫ এর পরে বের হন।",
        "imm_2": "হাওয়াপ্রতিরোধী ছাতা সাথে রাখুন।",
        "prev_1": "জলমগ্ন আন্ডারপাস ও নিচু রাস্তা এড়িয়ে চলুন।",
        "prev_2": "যানজটের জন্য মোবাইল ফোন চার্জ রাখুন।",
        "win_1": "নিরাপদ যাতায়াতের সময়: এখন থেকে বিকেল ৪:৪৫ পর্যন্ত।",
        "follow_1": "আজ সন্ধ্যায় কোন সময় বৃষ্টি সবচেয়ে বেশি হবে?",
        "follow_2": "কাল সকালে কি বৃষ্টি হতে পারে?"
    },
    "es": {
        "commute_yes": "Sí, se esperan lluvias durante su trayecto vespertino (17:45 - 19:30). Posible congestión por acumulación de agua.",
        "commute_no": "No se esperan lluvias significativas para su trayecto. Condiciones de tráfico normales.",
        "alert_yellow": "ALERTA AMARILLA: Tormentas con ráfagas de viento",
        "imm_1": "Salga antes de las 16:45 o después de las 19:45 para evitar el pico de lluvia.",
        "imm_2": "Lleve un paraguas resistente al viento contra ráfagas de 40 km/h.",
        "prev_1": "Evite pasos a desnivel y zonas propensas a anegamientos.",
        "prev_2": "Mantenga el teléfono cargado ante posibles demoras.",
        "win_1": "Ventana más segura: Desde ahora hasta las 16:45.",
        "follow_1": "¿A qué hora alcanzará su punto máximo la lluvia?",
        "follow_2": "¿Lloverá también durante el trayecto de mañana por la mañana?"
    }
}

# --- User Authentication Endpoints ---

@router.post("/auth/register", response_model=UserProfileResponse)
async def register_user(payload: UserRegisterRequest, db: Session = Depends(get_db)):
    """Register a new user in PostgreSQL."""
    existing = crud.get_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered.")
    
    user = crud.create_user(
        db=db,
        email=payload.email,
        full_name=payload.full_name,
        password=payload.password,
        role=payload.role,
        default_location=payload.default_location,
        lat=payload.latitude,
        lon=payload.longitude,
        lang=payload.language_preference
    )
    return UserProfileResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        default_location=user.default_location,
        default_latitude=user.default_latitude,
        default_longitude=user.default_longitude,
        preferred_language=user.preferred_language
    )

@router.post("/auth/login", response_model=UserProfileResponse)
async def login_user(payload: UserLoginRequest, db: Session = Depends(get_db)):
    """Authenticate user with email and password."""
    user = crud.authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")
    
    return UserProfileResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        default_location=user.default_location,
        default_latitude=user.default_latitude,
        default_longitude=user.default_longitude,
        preferred_language=user.preferred_language
    )

@router.get("/auth/me", response_model=UserProfileResponse)
async def get_current_user_profile(user_id: int = Query(...), db: Session = Depends(get_db)):
    """Get profile of current authenticated user."""
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return UserProfileResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        default_location=user.default_location,
        default_latitude=user.default_latitude,
        default_longitude=user.default_longitude,
        preferred_language=user.preferred_language
    )

# --- Weather Pipeline Analysis Endpoint ---

@router.post("/analyze")
async def analyze_weather_query(payload: AnalyzeRequest, db: Session = Depends(get_db)):
    """
    End-to-End Orchestrator Pipeline with User Profile Context:
    User Context -> Voice/Text -> NLP Intent -> Open-Meteo + IMD -> HF AI Reasoning -> Risk Analysis -> Action Matrix
    """
    try:
        # Check user context if user_id provided
        user = crud.get_user_by_id(db, payload.user_id) if payload.user_id else None
        
        # 1. Live Weather Data via Open-Meteo
        weather_raw = await weather_service.get_forecast(payload.latitude, payload.longitude)
        current = weather_raw.get("current", {})
        hourly = weather_raw.get("hourly", {})
        
        # 2. IMD Warning Feed
        imd_data = await imd_service.get_active_warnings(payload.location_name.split(",")[0])
        
        # 3. Climate Baseline Anomaly
        temp_val = current.get("temperature_2m", 26.0)
        climate_data = climate_service.get_climate_comparison(temp_val, payload.location_name)
        
        # 4. Hugging Face AI Intent & Context Reasoning
        hf_result = await hf_service.generate_advisory_reasoning(
            query=payload.query,
            weather_summary={
                "temp": temp_val,
                "rain_prob": max(hourly.get("precipitation_probability", [50])[:6]),
                "wind": current.get("wind_speed_10m", 18.0),
                "gusts": current.get("wind_gusts_10m", 38.0),
                "user_role": user.role if user else "General"
            },
            language_code=payload.language
        )
        intent = hf_result.get("intent", "COMMUTE_SAFETY")
        
        # 5. Risk Calculation
        rain_prob = max(hourly.get("precipitation_probability", [65])[:6]) if hourly.get("precipitation_probability") else 65
        wind = current.get("wind_speed_10m", 18.0)
        gusts = current.get("wind_gusts_10m", 38.0)
        
        commute_risk = min(100, int(rain_prob * 0.6 + gusts * 0.6))
        safety_risk = min(100, int(rain_prob * 0.4 + wind * 0.8))
        health_risk = min(100, int(35 if temp_val > 32 else 20))
        
        overall_score = min(98, max(15, int(commute_risk * 0.65 + safety_risk * 0.35)))
        risk_level = "SEVERE" if overall_score >= 75 else "HIGH" if overall_score >= 50 else "MODERATE" if overall_score >= 25 else "LOW"
        
        # 6. Localized Response Synthesis
        lang = payload.language
        t = TRANSLATIONS.get(lang, {})
        
        direct_answer = t.get("commute_yes" if rain_prob >= 50 else "commute_no", 
            f"Showers are expected during your commute in {payload.location_name}." if rain_prob >= 50 else f"No significant rain expected for your commute in {payload.location_name}."
        )
        
        alert_header = t.get("alert_yellow", imd_data.get("headline", "IMD WEATHER ADVISORY"))
        
        immediate_actions = [
            t.get("imm_1", "Depart before 16:45 or after 19:45 to avoid peak downpour."),
            t.get("imm_2", f"Carry a windproof umbrella; gusts up to {int(gusts)} km/h expected.")
        ]
        preventive_actions = [
            t.get("prev_1", "Bypass known waterlogging underpasses and bottle-neck intersections."),
            t.get("prev_2", "Keep mobile devices charged in case of heavy traffic gridlock.")
        ]
        best_windows = [
            t.get("win_1", "Safest travel window: Current time until 16:45.")
        ]
        follow_ups = [
            t.get("follow_1", "What time will rain peak this evening?"),
            t.get("follow_2", "Will tomorrow morning's commute also have rain?")
        ]

        # 7. PostgreSQL Persistence
        try:
            query_log = crud.log_user_query(
                db, payload.query, payload.input_type, intent, payload.language,
                payload.location_name, payload.latitude, payload.longitude,
                user_id=payload.user_id
            )
            crud.save_weather_cache(
                db, payload.location_name, payload.latitude, payload.longitude,
                temp_val, current.get("apparent_temperature"), rain_prob, wind,
                current.get("weather_code", 0), weather_raw
            )
            crud.save_risk_report(
                db, query_log.id, overall_score, risk_level,
                {"commute": commute_risk, "safety": safety_risk, "health": health_risk},
                imd_data.get("color_code", "Yellow"), direct_answer,
                immediate_actions, preventive_actions, best_windows
            )
        except Exception as db_err:
            print(f"[PostgreSQL Log Notice] DB transaction notice: {db_err}")

        return {
            "query": payload.query,
            "language": payload.language,
            "intent": intent,
            "location": payload.location_name,
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
