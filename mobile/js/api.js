/**
 * METEORA Mobile API Connector
 * Connects the mobile frontend to the FastAPI backend with resilient failover
 */

const API_CONFIG = {
  baseUrl: 'http://localhost:8000/api/v1',
  timeoutMs: 15000
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
   * Fetch live weather directly from Open-Meteo (no mock fallback)
   */
  async getLiveWeather(latitude, longitude) {
    const url = `https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,cloud_cover,pressure_msl,wind_speed_10m,wind_gusts_10m&hourly=temperature_2m,precipitation_probability,precipitation,weather_code,wind_speed_10m,uv_index&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,uv_index_max&timezone=auto`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Open-Meteo HTTP ${res.status}`);
    return await res.json();
  }

  /**
   * Direct client-side pipeline fallback when backend is offline.
   * Only uses real Open-Meteo data — never returns hardcoded dummy values.
   */
  async _directClientPipeline(payload) {
    let weather;
    try {
      weather = await this.getLiveWeather(payload.latitude, payload.longitude);
    } catch (err) {
      // Cannot reach weather API either — surface a clean error to the UI
      return {
        source: 'ERROR',
        data: {
          query: payload.query,
          language: payload.language || 'en',
          location: payload.location_name,
          data_source: 'Unavailable',
          weather: {},
          imd_alert: { color_code: 'Yellow', headline: 'WEATHER DATA UNAVAILABLE', bulletin: '' },
          risk_analysis: { overall_score: 0, risk_level: 'UNKNOWN', dimensions: {} },
          advisory: {
            direct_answer: `Unable to retrieve live weather data for ${payload.location_name}. Please check your internet connection and try again.`,
            immediate_actions: ['Check your internet connection.'],
            preventive_actions: [],
            best_windows: [],
            smart_follow_ups: ['Try again', 'Check weather for current location']
          }
        }
      };
    }

    const cur = weather.current || {};
    const hourly = weather.hourly || {};
    const daily = weather.daily || {};
    
    const rainP = hourly.precipitation_probability ? Math.max(...hourly.precipitation_probability.slice(0, 6)) : 0;
    const temp = cur.temperature_2m;
    const feelsLike = cur.apparent_temperature ?? temp;
    const wind = cur.wind_speed_10m ?? 0;
    const gusts = cur.wind_gusts_10m ?? 0;
    const humidity = cur.relative_humidity_2m ?? null;

    if (temp == null) {
      return {
        source: 'ERROR',
        data: {
          query: payload.query,
          language: payload.language || 'en',
          location: payload.location_name,
          data_source: 'Weather API (Open-Meteo)',
          weather: {},
          imd_alert: { color_code: 'Yellow', headline: 'NO DATA RETURNED', bulletin: '' },
          risk_analysis: { overall_score: 0, risk_level: 'UNKNOWN', dimensions: {} },
          advisory: {
            direct_answer: `No current weather data returned for ${payload.location_name}. The location may not be supported.`,
            immediate_actions: [],
            preventive_actions: [],
            best_windows: [],
            smart_follow_ups: ['Try a nearby city', 'Enter coordinates manually']
          }
        }
      };
    }

    const q = (payload.query || '').toLowerCase();
    const city = payload.location_name.split(',')[0].trim();
    const isTomorrow = q.includes('tomorrow');

    let directAnswer = "";
    if (q.includes('temp') || q.includes('hot') || q.includes('cold') || q.includes('heat')) {
      if (isTomorrow) {
        const tMax = daily.temperature_2m_max ? Math.round(daily.temperature_2m_max[1]) : null;
        const tMin = daily.temperature_2m_min ? Math.round(daily.temperature_2m_min[1]) : null;
        directAnswer = tMax != null && tMin != null
          ? `Tomorrow in ${city}, expected high is ${tMax}°C and low is ${tMin}°C.`
          : `Tomorrow's temperature data is not yet available for ${city}.`;
      } else {
        directAnswer = `The current temperature in ${city} is ${Math.round(temp)}°C (feels like ${Math.round(feelsLike)}°C).`;
        if (daily.temperature_2m_max && daily.temperature_2m_max[0] != null) {
          directAnswer += ` Expected high: ${Math.round(daily.temperature_2m_max[0])}°C, low: ${Math.round(daily.temperature_2m_min[0])}°C.`;
        }
      }
    } else if (q.includes('rain') || q.includes('shower') || q.includes('precipitat') || q.includes('umbrella') || q.includes('wet')) {
      if (isTomorrow) {
        const rMax = daily.precipitation_probability_max ? Math.round(daily.precipitation_probability_max[1]) : null;
        directAnswer = rMax != null
          ? `Tomorrow in ${city}, there is a ${rMax}% chance of rain.`
          : `Tomorrow's rain data is not yet available for ${city}.`;
      } else {
        directAnswer = `Today in ${city}, there is a ${Math.round(rainP)}% chance of rain. The current temperature is ${Math.round(temp)}°C.`;
      }
    } else if (q.includes('humid') || q.includes('moisture') || q.includes('damp')) {
      directAnswer = humidity != null
        ? `The relative humidity in ${city} is currently ${humidity}%, with a temperature of ${Math.round(temp)}°C.`
        : `Humidity data is currently unavailable for ${city}.`;
    } else if (q.includes('wind') || q.includes('gust') || q.includes('breeze')) {
      directAnswer = `The current wind speed in ${city} is ${Math.round(wind)} km/h with gusts up to ${Math.round(gusts)} km/h.`;
    } else {
      directAnswer = `Current weather in ${city}: ${Math.round(temp)}°C, ${Math.round(rainP)}% chance of rain, wind ${Math.round(wind)} km/h.`;
    }

    const commuteRisk = Math.min(100, Math.round(rainP * 0.6 + gusts * 0.6));
    const safetyRisk = Math.min(100, Math.round(rainP * 0.4 + wind * 0.8));
    const healthRisk = Math.min(100, Math.round(temp > 33 ? 55 : 28));
    const overall = Math.min(98, Math.max(15, Math.round(commuteRisk * 0.65 + safetyRisk * 0.35)));
    const riskLevel = overall >= 75 ? "SEVERE" : overall >= 50 ? "HIGH" : overall >= 25 ? "MODERATE" : "LOW";

    return {
      source: 'DIRECT_CLIENT_ENGINE',
      data: {
        query: payload.query,
        language: payload.language || 'en',
        location: payload.location_name,
        data_source: 'Weather API (Open-Meteo)',
        weather: {
          temperature: temp,
          feels_like: feelsLike,
          precipitation_probability: rainP,
          wind_speed: wind,
          wind_gusts: gusts,
          weather_code: cur.weather_code ?? 0
        },
        imd_alert: {
          color_code: overall >= 50 ? "Orange" : "Yellow",
          headline: `METEOROLOGICAL BULLETIN: ${city.toUpperCase()}`,
          bulletin: `Live weather observation for ${city}. Temperature: ${Math.round(temp)}°C. Wind: ${Math.round(wind)} km/h.`
        },
        risk_analysis: {
          overall_score: overall,
          risk_level: riskLevel,
          dimensions: { commute: commuteRisk, safety: safetyRisk, health: healthRisk }
        },
        advisory: {
          direct_answer: directAnswer,
          immediate_actions: [
            `Check conditions in ${city} before travel.`,
            gusts > 0 ? `Expected wind gusts up to ${Math.round(gusts)} km/h.` : `Current wind speed: ${Math.round(wind)} km/h.`
          ],
          preventive_actions: ["Keep mobile devices charged above 50%.", "Stay informed of weather updates."],
          best_windows: [`Safest travel window: Current conditions (${Math.round(temp)}°C, ${Math.round(rainP)}% rain chance).`],
          smart_follow_ups: [
            `What is tomorrow's forecast in ${city}?`,
            `What is the humidity in ${city}?`,
            `What are the wind conditions in ${city}?`
          ]
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

  /**
   * No mock weather data. If we can't reach Open-Meteo, we surface an error.
   * This method is intentionally left as a stub that throws to prevent
   * fake/hardcoded data from ever appearing in the app.
   */
  _generateMockWeather() {
    throw new Error("Live weather data unavailable. Please check your internet connection.");
  }
}

const meteoraApi = new MeteoraAPIConnector();
