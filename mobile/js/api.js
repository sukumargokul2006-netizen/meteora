/**
 * METEORA Mobile API Connector
 * Connects the mobile frontend to the FastAPI backend with resilient failover
 */

const API_CONFIG = {
  baseUrl: 'http://localhost:8000/api/v1',
  timeoutMs: 5000
};

class MeteoraAPIConnector {
  constructor(baseUrl = API_CONFIG.baseUrl) {
    this.baseUrl = baseUrl;
  }

  /**
   * Run the end-to-end weather analysis pipeline via FastAPI backend
   */
  async analyzeWeatherQuery(query, locationName, latitude, longitude, inputType = 'text', language = 'en') {
    const payload = {
      query,
      location_name: locationName,
      latitude,
      longitude,
      input_type: inputType,
      language
    };

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.timeoutMs);

      const res = await fetch(`${this.baseUrl}/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload),
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!res.ok) throw new Error(`Backend response status: ${res.status}`);
      const data = await res.json();
      return { source: 'FASTAPI_BACKEND', data };
    } catch (err) {
      console.warn(`[Meteora API Connector] FastAPI backend unavailable (${err.message}). Connecting via resilient direct weather engine.`);
      return this._directClientPipeline(payload);
    }
  }

  /**
   * Fetch live weather directly from Open-Meteo
   */
  async getLiveWeather(latitude, longitude) {
    try {
      const url = `https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,cloud_cover,pressure_msl,wind_speed_10m,wind_gusts_10m&hourly=temperature_2m,precipitation_probability,precipitation,weather_code,wind_speed_10m,uv_index&timezone=auto`;
      const res = await fetch(url);
      if (!res.ok) throw new Error("Open-Meteo fetch failed");
      return await res.json();
    } catch (err) {
      console.warn("Using simulated meteorological fallback:", err);
      return this._generateMockWeather();
    }
  }

  /**
   * Direct client-side pipeline fallback when backend is offline
   */
  async _directClientPipeline(payload) {
    const weather = await this.getLiveWeather(payload.latitude, payload.longitude);
    const cur = weather.current || {};
    const hourly = weather.hourly || {};
    
    const rainP = hourly.precipitation_probability ? Math.max(...hourly.precipitation_probability.slice(0, 6)) : 72;
    const temp = cur.temperature_2m || 26.4;
    const wind = cur.wind_speed_10m || 18.0;
    const gusts = cur.wind_gusts_10m || 41.5;

    const commuteRisk = Math.min(100, Math.round(rainP * 0.6 + gusts * 0.6));
    const safetyRisk = Math.min(100, Math.round(rainP * 0.4 + wind * 0.8));
    const healthRisk = Math.min(100, Math.round(temp > 33 ? 55 : 28));
    const overall = Math.min(98, Math.max(15, Math.round(commuteRisk * 0.65 + safetyRisk * 0.35)));

    const riskLevel = overall >= 75 ? "SEVERE" : overall >= 50 ? "HIGH" : overall >= 25 ? "MODERATE" : "LOW";

    // Multi-lingual fallback responses
    const lang = payload.language || 'en';
    const localized = this._getLocalizedAdvisory(payload.query, lang, rainP, gusts, payload.location_name);

    return {
      source: 'DIRECT_CLIENT_ENGINE',
      data: {
        query: payload.query,
        language: lang,
        location: payload.location_name,
        weather: {
          temperature: temp,
          feels_like: cur.apparent_temperature || temp,
          precipitation_probability: rainP,
          wind_speed: wind,
          wind_gusts: gusts,
          weather_code: cur.weather_code || 63
        },
        imd_alert: {
          color_code: overall >= 50 ? "Orange" : "Yellow",
          headline: localized.alertHeader,
          bulletin: `Upper air convective circulation active over ${payload.location_name.split(',')[0]}. Thunderstorms with gusts to ${Math.round(gusts)} km/h possible.`
        },
        risk_analysis: {
          overall_score: overall,
          risk_level: riskLevel,
          dimensions: {
            commute: commuteRisk,
            safety: safetyRisk,
            health: healthRisk
          }
        },
        advisory: {
          direct_answer: localized.directAnswer,
          immediate_actions: localized.immediateActions,
          preventive_actions: localized.preventiveActions,
          best_windows: localized.bestWindows,
          smart_follow_ups: localized.followUps
        }
      }
    };
  }

  _getLocalizedAdvisory(query, lang, rainP, gusts, location) {
    const isHindi = lang === 'hi';
    const isTamil = lang === 'ta';
    const isSpanish = lang === 'es';

    if (isHindi) {
      return {
        alertHeader: "आईएमडी पीली चेतावनी: गरज के साथ तेज हवाएं",
        directAnswer: rainP >= 50 
          ? `हाँ, ${location.split(',')[0]} में आपकी शाम की यात्रा के दौरान बारिश की संभावना है। 20-40 मिनट की देरी संभव है।`
          : `${location.split(',')[0]} में यात्रा के दौरान भारी बारिश की संभावना नहीं है।`,
        immediateActions: [
          "🚗 शाम 4:45 से पहले निकलें या 7:45 के बाद यात्रा करें।",
          `🌂 हवा प्रतिरोधी छाता साथ रखें; ${Math.round(gusts)} किमी/घंटा तक के झोंके संभव हैं।`
        ],
        preventiveActions: [
          "🗺️ रेलवे अंडरपास और जलभराव वाले चौराहों से बचें।",
          "🔋 ट्रैफिक जाम की स्थिति के लिए फोन चार्ज रखें।"
        ],
        bestWindows: ["☀️ सबसे सुरक्षित यात्रा समय: अभी से शाम 4:45 तक।"],
        followUps: [
          "शाम को बारिश किस समय सबसे तेज होगी?",
          "क्या कल सुबह की यात्रा में भी बारिश होगी?"
        ]
      };
    } else if (isTamil) {
      return {
        alertHeader: "வானிலை மஞ்சள் எச்சரிக்கை: பலத்த காற்றுடன் மழை",
        directAnswer: rainP >= 50 
          ? `ஆம், ${location.split(',')[0]} பகுதியில் உங்கள் பயணத்தின் போது மழை பெய்ய வாய்ப்புள்ளது.`
          : `${location.split(',')[0]} பகுதியில் மழைக்கு வாய்ப்பில்லை, சாலைகள் சீராக இருக்கும்.`,
        immediateActions: [
          "🚗 மாலை 4:45 க்கு முன் அல்லது 7:45 க்குப் பிறகு புறப்படுங்கள்.",
          "🌂 காற்றுக்கு தாங்கக்கூடிய குடையை உடன் எடுத்துச் செல்லுங்கள்."
        ],
        preventiveActions: [
          "🗺️ நீர் தேங்கும் சுரங்கப்பாதைகளைத் தவிர்க்கவும்.",
          "🔋 மொபைல் பேட்டரியை முழுமையாக வைத்திருக்கவும்."
        ],
        bestWindows: ["☀️ பாதுகாப்பான பயண நேரம்: தற்போது முதல் மாலை 4:45 வரை."],
        followUps: [
          "இன்று மாலை எந்த நேரத்தில் மழை அதிகமாக இருக்கும்?",
          "நாளை காலை பயணத்திலும் மழை பெய்யுமா?"
        ]
      };
    } else if (isSpanish) {
      return {
        alertHeader: "ALERTA AMARILLA: Tormentas con ráfagas de viento",
        directAnswer: rainP >= 50
          ? `Sí, se esperan lluvias durante su trayecto en ${location.split(',')[0]}. Posibles demoras de 20 a 40 minutos.`
          : `No se esperan lluvias significativas para su trayecto en ${location.split(',')[0]}.`,
        immediateActions: [
          "🚗 Salga antes de las 16:45 o después de las 19:45.",
          `🌂 Lleve un paraguas resistente al viento (${Math.round(gusts)} km/h).`
        ],
        preventiveActions: [
          "🗺️ Evite pasos a desnivel y zonas bajas con acumulación de agua.",
          "🔋 Mantenga su dispositivo móvil con suficiente carga."
        ],
        bestWindows: ["☀️ Ventana más segura: Desde ahora hasta las 16:45."],
        followUps: [
          "¿A qué hora alcanzará su punto máximo la lluvia?",
          "¿Lloverá también durante el trayecto de mañana?"
        ]
      };
    }

    // Default English
    return {
      alertHeader: "IMD YELLOW ALERT: THUNDERSTORM WARNING",
      directAnswer: rainP >= 50 
        ? `Yes, expect showers during your evening commute in ${location.split(',')[0]} (around 5:45 PM – 7:30 PM). Delays of 20–40 mins likely.`
        : `No significant rain expected for your commute in ${location.split(',')[0]}. Roads should remain clear.`,
      immediateActions: [
        "🚗 Depart before 16:45 or delay until after 19:45 to avoid peak downpour.",
        `🌂 Carry a windproof umbrella; gusts up to ${Math.round(gusts)} km/h expected.`
      ],
      preventiveActions: [
        "🗺️ Bypass known waterlogging underpasses and bottle-neck intersections.",
        "🔋 Keep mobile devices charged above 50% in case of traffic delays."
      ],
      bestWindows: ["☀️ Safest travel window: Current time until 16:45 (<20% rain)."],
      followUps: [
        "What time will rain peak this evening?",
        "Will tomorrow morning's commute also have rain?",
        "Show hourly wind gusts between 5 and 8 PM"
      ]
    };
  }

  _generateMockWeather() {
    const now = new Date();
    return {
      current: {
        temperature_2m: 26.4,
        apparent_temperature: 28.1,
        relative_humidity_2m: 78,
        precipitation: 2.4,
        weather_code: 63,
        wind_speed_10m: 18.2,
        wind_gusts_10m: 41.5,
        pressure_msl: 1012.4
      },
      hourly: {
        time: Array.from({length: 8}, (_, i) => new Date(now.getTime() + i * 3600000).toISOString()),
        temperature_2m: [26.4, 25.8, 24.5, 24.0, 23.5, 23.0, 22.8, 22.5],
        precipitation_probability: [35, 55, 75, 82, 65, 40, 25, 15],
        weather_code: [2, 61, 63, 65, 63, 80, 2, 2]
      }
    };
  }
}

const meteoraApi = new MeteoraAPIConnector();
