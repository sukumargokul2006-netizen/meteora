/**
 * METEORA Mobile Application Controller
 * Handles mobile touch gestures, voice speech recognition, audio playback,
 * language switching, and UI state synchronization.
 */

// Mobile App State
const appState = {
  location: {
    name: 'Bengaluru, IN',
    latitude: 12.9716,
    longitude: 77.5946
  },
  activeQuery: "Will it rain during my evening commute?",
  currentLanguage: 'en',
  isRecording: false,
  isPlayingTTS: false,
  weather: null,
  advisory: null
};

// --- Clock updater for mobile status bar ---
function updateMobileClock() {
  const now = new Date();
  let hours = now.getHours();
  let minutes = now.getMinutes();
  minutes = minutes < 10 ? '0' + minutes : minutes;
  const clockEl = document.getElementById('statusClock');
  if (clockEl) clockEl.textContent = `${hours}:${minutes}`;
}
setInterval(updateMobileClock, 1000);
updateMobileClock();

// --- Weather Code to Icon & Description Mapping ---
function interpretWmo(code) {
  const map = {
    0: { desc: 'Clear Sky', icon: '☀️' },
    1: { desc: 'Mainly Clear', icon: '🌤️' },
    2: { desc: 'Partly Cloudy', icon: '⛅' },
    3: { desc: 'Overcast', icon: '☁️' },
    45: { desc: 'Fog', icon: '🌫️' },
    51: { desc: 'Light Drizzle', icon: '🌦️' },
    61: { desc: 'Light Rain', icon: '🌦️' },
    63: { desc: 'Moderate Rain', icon: '🌧️' },
    65: { desc: 'Heavy Rain', icon: '⛈️' },
    80: { desc: 'Rain Showers', icon: '🌦️' },
    95: { desc: 'Thunderstorm', icon: '⚡' }
  };
  return map[code] || { desc: 'Variably Cloudy', icon: '⛅' };
}

// --- Main Pipeline Execution ---
async function runQuery(customQuery = null) {
  const query = customQuery || document.getElementById('queryInput').value.trim() || appState.activeQuery;
  appState.activeQuery = query;
  document.getElementById('queryInput').value = query;

  try {
    const result = await meteoraApi.analyzeWeatherQuery(
      query,
      appState.location.name,
      appState.location.latitude,
      appState.location.longitude,
      'text',
      appState.currentLanguage
    );

    const data = result.data;
    renderMobileApp(data);
  } catch (err) {
    console.error("Error executing query:", err);
  }
}

// --- Render Mobile Application Views ---
function renderMobileApp(data) {
  const weather = data.weather || {};
  const risk = data.risk_analysis || {};
  const advisory = data.advisory || {};
  const alert = data.imd_alert || {};

  // 1. Weather Snapshot Card
  const wmo = interpretWmo(weather.weather_code);
  document.getElementById('heroTemp').textContent = Math.round(weather.temperature || 26);
  document.getElementById('heroCondition').textContent = wmo.desc;
  document.getElementById('heroIcon').textContent = wmo.icon;
  document.getElementById('statRain').textContent = `${weather.precipitation_probability || 70}%`;
  document.getElementById('statWind').textContent = `${Math.round(weather.wind_speed || 18)} km/h`;

  // 2. Alert Card
  const alertEl = document.getElementById('alertCard');
  const alertColor = (alert.color_code || 'Yellow').toLowerCase();
  alertEl.className = `alert-card alert-${alertColor}`;
  document.getElementById('alertTitle').textContent = alert.headline || 'METEOROLOGICAL ADVISORY';
  document.getElementById('alertText').textContent = alert.bulletin || '';

  // 3. AI Advisory
  document.getElementById('directAnswer').textContent = advisory.direct_answer || '';
  document.getElementById('intentBadge').textContent = (data.intent || 'COMMUTE_SAFETY').replace('_', ' ');

  // Immediate Actions
  const immList = document.getElementById('immList');
  immList.innerHTML = '';
  (advisory.immediate_actions || []).forEach(act => {
    const div = document.createElement('div');
    div.className = 'action-row imm';
    div.innerHTML = act;
    immList.appendChild(div);
  });

  // Preventive Actions
  const prevList = document.getElementById('prevList');
  prevList.innerHTML = '';
  (advisory.preventive_actions || []).forEach(act => {
    const div = document.createElement('div');
    div.className = 'action-row prev';
    div.innerHTML = act;
    prevList.appendChild(div);
  });

  // Best Windows
  const winList = document.getElementById('winList');
  winList.innerHTML = '';
  (advisory.best_windows || []).forEach(act => {
    const div = document.createElement('div');
    div.className = 'action-row win';
    div.innerHTML = act;
    winList.appendChild(div);
  });

  // 4. Risk Gauge
  const score = risk.overall_score || 55;
  document.getElementById('riskDigit').textContent = score;
  const circle = document.getElementById('riskBarCircle');
  if (circle) {
    const offset = 232.5 - (score / 100) * 232.5;
    circle.style.strokeDashoffset = offset;
    circle.style.stroke = score >= 75 ? 'var(--accent-red)' : score >= 50 ? 'var(--accent-orange)' : score >= 25 ? 'var(--accent-yellow)' : 'var(--accent-green)';
  }

  const riskTag = document.getElementById('riskBadge');
  riskTag.className = `risk-tag ${(risk.risk_level || 'moderate').toLowerCase()}`;
  riskTag.textContent = `${risk.risk_level || 'MODERATE'} RISK`;

  // 5. Follow-Up Questions
  const followUpBox = document.getElementById('followUpsList');
  followUpBox.innerHTML = '';
  (advisory.smart_follow_ups || []).forEach(q => {
    const pill = document.createElement('div');
    pill.className = 'f-pill';
    pill.innerHTML = `<span>💡 ${q}</span>`;
    pill.addEventListener('click', () => {
      runQuery(q);
      document.getElementById('scrollView').scrollTo({ top: 100, behavior: 'smooth' });
    });
    followUpBox.appendChild(pill);
  });
}

// --- Render Hourly Forecast Swiper ---
async function loadHourlyForecast() {
  try {
    const data = await meteoraApi.getLiveWeather(appState.location.latitude, appState.location.longitude);
    const swiper = document.getElementById('hourlySwiper');
    swiper.innerHTML = '';
    
    if (data.hourly && data.hourly.time) {
      const count = Math.min(8, data.hourly.time.length);
      for (let i = 0; i < count; i++) {
        const timeStr = new Date(data.hourly.time[i]).toLocaleTimeString([], { hour: 'numeric' });
        const code = data.hourly.weather_code[i];
        const w = interpretWmo(code);
        const temp = Math.round(data.hourly.temperature_2m[i]);
        const p = data.hourly.precipitation_probability ? data.hourly.precipitation_probability[i] : 0;

        const tile = document.createElement('div');
        tile.className = 'h-tile';
        tile.innerHTML = `
          <div class="h-tile-time">${timeStr}</div>
          <div class="h-tile-icon">${w.icon}</div>
          <div class="h-tile-temp">${temp}°</div>
          <div class="h-tile-rain">💧${p}%</div>
        `;
        swiper.appendChild(tile);
      }
    }
  } catch (e) {
    console.warn("Failed to load hourly strip:", e);
  }
}

// --- Web Speech API (Voice Recognition) ---
const voiceBtn = document.getElementById('voiceBtn');
const listenBar = document.getElementById('listenBar');
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

if (SpeechRecognition) {
  const recognizer = new SpeechRecognition();
  recognizer.continuous = false;
  recognizer.interimResults = false;
  
  // Set speech recognition language according to current language
  recognizer.onstart = () => {
    appState.isRecording = true;
    voiceBtn.classList.add('recording');
    listenBar.classList.add('active');
  };

  recognizer.onresult = (e) => {
    const spoken = e.results[0][0].transcript;
    document.getElementById('queryInput').value = spoken;
    runQuery(spoken);
  };

  recognizer.onerror = () => stopMic();
  recognizer.onend = () => stopMic();

  voiceBtn.addEventListener('click', () => {
    if (appState.isRecording) {
      recognizer.stop();
    } else {
      recognizer.lang = appState.currentLanguage === 'hi' ? 'hi-IN' :
                        appState.currentLanguage === 'ta' ? 'ta-IN' :
                        appState.currentLanguage === 'te' ? 'te-IN' :
                        appState.currentLanguage === 'kn' ? 'kn-IN' :
                        appState.currentLanguage === 'bn' ? 'bn-IN' :
                        appState.currentLanguage === 'es' ? 'es-ES' : 'en-US';
      try { recognizer.start(); } catch (err) {}
    }
  });

  function stopMic() {
    appState.isRecording = false;
    voiceBtn.classList.remove('recording');
    listenBar.classList.remove('active');
  }
} else {
  voiceBtn.addEventListener('click', () => {
    alert("Speech recognition is not supported in this browser engine.");
  });
}

// --- Text-to-Speech (Spoken Audio Reader) ---
const audioBtn = document.getElementById('audioBtn');
audioBtn.addEventListener('click', () => {
  if (!('speechSynthesis' in window)) return;

  if (appState.isPlayingTTS) {
    window.speechSynthesis.cancel();
    appState.isPlayingTTS = false;
    audioBtn.classList.remove('playing');
    document.getElementById('audioBtnText').textContent = I18N.get('listen');
    return;
  }

  const text = document.getElementById('directAnswer').textContent;
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = appState.currentLanguage === 'hi' ? 'hi-IN' :
                   appState.currentLanguage === 'ta' ? 'ta-IN' :
                   appState.currentLanguage === 'es' ? 'es-ES' : 'en-US';
  utterance.rate = 0.95;

  utterance.onstart = () => {
    appState.isPlayingTTS = true;
    audioBtn.classList.add('playing');
    document.getElementById('audioBtnText').textContent = I18N.get('stop');
  };

  utterance.onend = () => {
    appState.isPlayingTTS = false;
    audioBtn.classList.remove('playing');
    document.getElementById('audioBtnText').textContent = I18N.get('listen');
  };

  window.speechSynthesis.speak(utterance);
});

// --- Scenario Quick Chips ---
document.querySelectorAll('.scenario-scroll-row .s-pill').forEach(pill => {
  pill.addEventListener('click', () => {
    const q = pill.getAttribute('data-query');
    runQuery(q);
  });
});

// --- Submit Query Button & Enter ---
document.getElementById('sendBtn').addEventListener('click', () => runQuery());
document.getElementById('queryInput').addEventListener('keydown', (e) => {
  if (e.key === 'Enter') runQuery();
});

// --- Bottom Navigation Tab Switching ---
document.querySelectorAll('.app-bottom-bar .b-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.app-bottom-bar .b-tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    const targetId = tab.getAttribute('data-target');
    const el = document.getElementById(targetId);
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
});

// --- Location Bottom Sheet ---
const locSheet = document.getElementById('locationSheet');
const openLocBtn = document.getElementById('openLocationBtn');
const closeLocBtn = document.getElementById('closeLocationBtn');

openLocBtn.addEventListener('click', () => locSheet.classList.add('active'));
closeLocBtn.addEventListener('click', () => locSheet.classList.remove('active'));
locSheet.addEventListener('click', (e) => {
  if (e.target === locSheet) locSheet.classList.remove('active');
});

function changeLocation(name, lat, lon) {
  appState.location = { name, latitude: lat, longitude: lon };
  document.getElementById('locationTitle').textContent = name;
  locSheet.classList.remove('active');
  runQuery();
  loadHourlyForecast();
}

document.querySelectorAll('.sheet-grid-2col .sheet-choice-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const lat = parseFloat(btn.getAttribute('data-lat'));
    const lon = parseFloat(btn.getAttribute('data-lon'));
    const name = btn.getAttribute('data-name');
    changeLocation(name, lat, lon);
  });
});

// Auto GPS button
document.getElementById('gpsBtn').addEventListener('click', () => {
  if ('geolocation' in navigator) {
    navigator.geolocation.getCurrentPosition(
      pos => {
        const lat = pos.coords.latitude;
        const lon = pos.coords.longitude;
        changeLocation(`GPS (${lat.toFixed(1)}°, ${lon.toFixed(1)}°)`, lat, lon);
      },
      err => alert(`GPS: ${err.message}`)
    );
  }
});

// City search in location sheet
document.getElementById('cityInput').addEventListener('keydown', async (e) => {
  if (e.key === 'Enter') {
    const term = e.target.value.trim();
    if (!term) return;
    try {
      const res = await fetch(`https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(term)}&count=1&language=en&format=json`);
      const data = await res.json();
      if (data.results && data.results.length > 0) {
        const loc = data.results[0];
        changeLocation(`${loc.name}, ${loc.country_code || ''}`, loc.latitude, loc.longitude);
      } else {
        alert(`City "${term}" not found.`);
      }
    } catch (err) {
      alert("Error searching city.");
    }
  }
});

// --- Language Bottom Sheet ---
const langSheet = document.getElementById('languageSheet');
const openLangBtn = document.getElementById('openLangBtn');
const closeLangBtn = document.getElementById('closeLangBtn');

openLangBtn.addEventListener('click', () => langSheet.classList.add('active'));
closeLangBtn.addEventListener('click', () => langSheet.classList.remove('active'));
langSheet.addEventListener('click', (e) => {
  if (e.target === langSheet) langSheet.classList.remove('active');
});

document.querySelectorAll('#langGrid .sheet-choice-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const code = btn.getAttribute('data-lang');
    appState.currentLanguage = code;
    I18N.setLanguage(code);
    langSheet.classList.remove('active');
    runQuery(); // Re-run query to retrieve localized advice from backend/engine
  });
});

// --- App Initialization ---
window.addEventListener('DOMContentLoaded', () => {
  I18N.applyTranslations();
  runQuery();
  loadHourlyForecast();
});
