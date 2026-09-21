/**
 * METEORA Multi-Language Localization Engine (i18n)
 * Supports English, Hindi, Tamil, Telugu, Kannada, Bengali, and Spanish
 */

const I18N = {
  currentLanguage: 'en',

  languages: [
    { code: 'en', name: 'English', native: 'English' },
    { code: 'hi', name: 'Hindi', native: 'हिन्दी' },
    { code: 'ta', name: 'Tamil', native: 'தமிழ்' },
    { code: 'te', name: 'Telugu', native: 'తెలుగు' },
    { code: 'kn', name: 'Kannada', native: 'ಕನ್ನಡ' },
    { code: 'bn', name: 'Bengali', native: 'বাংলা' },
    { code: 'es', name: 'Spanish', native: 'Español' }
  ],

  translations: {
    en: {
      appName: "METEORA",
      tagline: "AI Risk Advisor",
      inputPlaceholder: "Ask weather question...",
      immediateActions: "🚨 Immediate Actions",
      preventiveActions: "🛡️ Preventive Precautions",
      optimalWindows: "⏱️ Optimal Windows",
      whatShouldIDo: "\"What Should I Do?\"",
      listen: "Listen",
      stop: "Stop",
      rainProb: "Precipitation",
      windGusts: "Wind / Gusts",
      uvIndex: "UV Index",
      riskAnalysis: "Multi-Factor Risk Analysis",
      commuteDelay: "Commute & Logistics Friction",
      safetyExposure: "Outdoor Safety & Exposure",
      healthRisk: "Health & UV Exposure",
      hourlyOutlook: "Next 8 Hours Outlook",
      followUpTitle: "Smart Follow-up Inquiries:",
      tabAdvisory: "Advisory",
      tabForecast: "Forecast",
      tabRisk: "Risk",
      tabActions: "Actions",
      chooseLocation: "Choose Location / GPS",
      autoGps: "Auto-Detect My GPS Coordinates",
      popularCities: "POPULAR CITIES:",
      changeLanguage: "Select Language",
      scenarios: {
        commute: "🚗 Evening Commute",
        event: "🎉 Outdoor Event",
        crops: "🌾 Crop Spraying",
        storm: "⚡ Storm Warning",
        sports: "⚽ Sports & UV"
      }
    },
    hi: {
      appName: "मेटीओरा",
      tagline: "एआई मौसम सलाहकार",
      inputPlaceholder: "मौसम संबंधी प्रश्न पूछें...",
      immediateActions: "🚨 तत्काल कदम",
      preventiveActions: "🛡️ निवारक सावधानियां",
      optimalWindows: "⏱️ सर्वोत्तम समय सीमा",
      whatShouldIDo: "\"मुझे क्या करना चाहिए?\"",
      listen: "सुनें",
      stop: "रोकें",
      rainProb: "बारिश की संभावना",
      windGusts: "हवा / झोंके",
      uvIndex: "यूवी इंडेक्स",
      riskAnalysis: "बहु-कारक जोखिम विश्लेषण",
      commuteDelay: "यातायात और लॉजिस्टिक्स बाधा",
      safetyExposure: "बाहरी सुरक्षा जोखिम",
      healthRisk: "स्वास्थ्य और यूवी प्रभाव",
      hourlyOutlook: "अगले 8 घंटे का पूर्वानुमान",
      followUpTitle: "स्मार्ट अनुवर्ती प्रश्न:",
      tabAdvisory: "सलाह",
      tabForecast: "पूर्वानुमान",
      tabRisk: "जोखिम",
      tabActions: "कार्रवाई",
      chooseLocation: "स्थान / जीपीएस चुनें",
      autoGps: "मेरा जीपीएस पता लगाएं",
      popularCities: "प्रमुख शहर:",
      changeLanguage: "भाषा चुनें",
      scenarios: {
        commute: "🚗 शाम की यात्रा",
        event: "🎉 बाहरी कार्यक्रम",
        crops: "🌾 कीटनाशक छिड़काव",
        storm: "⚡ तूफान चेतावनी",
        sports: "⚽ खेल और यूवी"
      }
    },
    ta: {
      appName: "மெட்டியோரா",
      tagline: "வானிலை AI ஆலோசகர்",
      inputPlaceholder: "வானிலை கேள்வியைக் கேளுங்கள்...",
      immediateActions: "🚨 உடனடி நடவடிக்கைகள்",
      preventiveActions: "🛡️ பாதுகாப்பு முன்னெச்சரிக்கைகள்",
      optimalWindows: "⏱️ சிறந்த நேர இடைவெளி",
      whatShouldIDo: "\"நான் என்ன செய்ய வேண்டும்?\"",
      listen: "கேளுங்கள்",
      stop: "நிறுத்து",
      rainProb: "மழை வாய்ப்பு",
      windGusts: "காற்று வேகம்",
      uvIndex: "புற ஊதாக் கதிர்",
      riskAnalysis: "பல்வேறு இடர் பகுப்பாய்வு",
      commuteDelay: "போக்குவரத்து தாமதங்கள்",
      safetyExposure: "வெளிப்புற பாதுகாப்பு",
      healthRisk: "உடல்நல பாதிப்பு",
      hourlyOutlook: "அடுத்த 8 மணி நேர பார்வை",
      followUpTitle: "தொடர்புடைய வினாக்கள்:",
      tabAdvisory: "ஆலோசனை",
      tabForecast: "வானிலை",
      tabRisk: "இடர்",
      tabActions: "நடவடிக்கை",
      chooseLocation: "இருப்பிடத்தை தேர்வு செய்யவும்",
      autoGps: "ஜிபிஎஸ் இருப்பிடத்தை அறிய",
      popularCities: "முக்கிய நகரங்கள்:",
      changeLanguage: "மொழியைத் தேர்வு செய்க",
      scenarios: {
        commute: "🚗 மாலைப் பயணம்",
        event: "🎉 வெளிப்புற நிகழ்வு",
        crops: "🌾 மருந்து தெளித்தல்",
        storm: "⚡ புயல் எச்சரிக்கை",
        sports: "⚽ விளையாட்டு & வெயில்"
      }
    },
    te: {
      appName: "మెటియోరా",
      tagline: "వాతావరణ ఏఐ సలహాదారు",
      inputPlaceholder: "వాతావరణ ప్రశ్న అడగండి...",
      immediateActions: "🚨 తక్షణ చర్యలు",
      preventiveActions: "🛡️ నివారణ జాగ్రత్తలు",
      optimalWindows: "⏱️ అనుకూల సమయం",
      whatShouldIDo: "\"నేను ఏమి చేయాలి?\"",
      listen: "వినండి",
      stop: "ఆపండి",
      rainProb: "వర్షపాతం అవకాశం",
      windGusts: "గాలి తీవ్రత",
      uvIndex: "యూవీ సూచిక",
      riskAnalysis: "బహుళ ప్రమాద విశ్లేషణ",
      commuteDelay: "ప్రయాణ ఆటంకాలు",
      safetyExposure: "బహిరంగ భద్రత",
      healthRisk: "ఆరోగ్య ప్రభావం",
      hourlyOutlook: "తదుపరి 8 గంటల సూచన",
      followUpTitle: "అదనపు ప్రశ్నలు:",
      tabAdvisory: "సలహా",
      tabForecast: "అంచనా",
      tabRisk: "ప్రమాదం",
      tabActions: "చర్యలు",
      chooseLocation: "ప్రదేశం ఎంచుకోండి",
      autoGps: "నా జీపీఎస్ గుర్తించండి",
      popularCities: "ప్రధాన నగరాలు:",
      changeLanguage: "భాషను ఎంచుకోండి",
      scenarios: {
        commute: "🚗 సాయంత్రం ప్రయాణం",
        event: "🎉 బహిరంగ వేడుక",
        crops: "🌾 పంట పిచికారీ",
        storm: "⚡ తుఫాను హెచ్చరిక",
        sports: "⚽ క్రీడలు & ఎండ"
      }
    },
    kn: {
      appName: "ಮೆಟಿಯೋರಾ",
      tagline: "ಹವಾಮಾನ ಎಐ ಸಲಹೆಗಾರ",
      inputPlaceholder: "ಹವಾಮಾನ ಪ್ರಶ್ನೆ ಕೇಳಿ...",
      immediateActions: "🚨 ತಕ್ಷಣದ ಕ್ರಮಗಳು",
      preventiveActions: "🛡️ ಮುನ್ನೆಚ್ಚರಿಕೆ ಕ್ರಮಗಳು",
      optimalWindows: "⏱️ ಉತ್ತಮ ಸಮಯಾವಧಿ",
      whatShouldIDo: "\"ನಾನು ಏನು ಮಾಡಬೇಕು?\"",
      listen: "ಆಲಿಸಿ",
      stop: "ನಿಲ್ಲಿಸಿ",
      rainProb: "ಮಳೆಯ ಸಾಧ್ಯತೆ",
      windGusts: "ಗಾಳಿಯ ವೇಗ",
      uvIndex: "ಯುವಿ ಸೂಚ್ಯಂಕ",
      riskAnalysis: "ಅಪಾಯ ವಿಶ್ಲೇಷಣೆ",
      commuteDelay: "ಸಂಚಾರ ಅಡಚಣೆಗಳು",
      safetyExposure: "ಹೊರಾಂಗಣ ಸುರಕ್ಷತೆ",
      healthRisk: "ಆರೋಗ್ಯದ ಮೇಲಿನ ಪರಿಣಾಮ",
      hourlyOutlook: "ಮುಂದಿನ 8 ಗಂಟೆಗಳ ಮುನ್ನೋಟ",
      followUpTitle: "ಹೆಚ್ಚಿನ ಪ್ರಶ್ನೆಗಳು:",
      tabAdvisory: "ಸಲಹೆ",
      tabForecast: "ಮುನ್ಸೂಚನೆ",
      tabRisk: "ಅಪಾಯ",
      tabActions: "ಕ್ರಮಗಳು",
      chooseLocation: "ಸ್ಥಳವನ್ನು ಆಯ್ಕೆಮಾಡಿ",
      autoGps: "ನನ್ನ ಜಿಪಿಎಸ್ ಪತ್ತೆ ಮಾಡಿ",
      popularCities: "ಪ್ರಮುಖ ನಗರಗಳು:",
      changeLanguage: "ಭಾಷೆ ಆಯ್ಕೆಮಾಡಿ",
      scenarios: {
        commute: "🚗 ಸಂಜೆಯ ಪ್ರಯಾಣ",
        event: "🎉 ಹೊರಾಂಗಣ ಸಮಾರಂಭ",
        crops: "🌾 ಬೆಳೆ ಕೀಟನಾಶಕ",
        storm: "⚡ ಬಿರುಗಾಳಿ ಎಚ್ಚರಿಕೆ",
        sports: "⚽ ಕ್ರೀಡೆ & ಬಿಸಿಲು"
      }
    },
    bn: {
      appName: "মেটিঅরা",
      tagline: "আবহাওয়া এআই উপদেষ্টা",
      inputPlaceholder: "আবহাওয়া সংক্রান্ত প্রশ্ন করুন...",
      immediateActions: "🚨 অবিলম্বে পদক্ষেপ",
      preventiveActions: "🛡️ সতর্কতামূলক ব্যবস্থা",
      optimalWindows: "⏱️ উপযুক্ত সময়সীমা",
      whatShouldIDo: "\"আমার কী করা উচিত?\"",
      listen: "শুনুন",
      stop: "থামুন",
      rainProb: "বৃষ্টির সম্ভাবনা",
      windGusts: "বায়ুপ্রবাহের গতি",
      uvIndex: "ইউভি সূচক",
      riskAnalysis: "বহুমাত্রিক ঝুঁকি বিশ্লেষণ",
      commuteDelay: "যাতায়াতে বিঘ্ন",
      safetyExposure: "বহিঃস্থ নিরাপত্তা",
      healthRisk: "স্বাস্থ্যগত ঝুঁকি",
      hourlyOutlook: "পরবর্তী ৮ ঘণ্টার পূর্বাভাস",
      followUpTitle: "সম্পর্কিত প্রশ্নাবলী:",
      tabAdvisory: "পরামর্শ",
      tabForecast: "পূর্বাভাস",
      tabRisk: "ঝুঁকি",
      tabActions: "পদক্ষেপ",
      chooseLocation: "অবস্থান নির্বাচন করুন",
      autoGps: "আমার জিপিএস শনাক্ত করুন",
      popularCities: "জনপ্রিয় শহর:",
      changeLanguage: "ভাষা নির্বাচন করুন",
      scenarios: {
        commute: "🚗 সন্ধ্যার যাতায়াত",
        event: "🎉 খোলা আকাশের অনুষ্ঠান",
        crops: "🌾 ফসলে কীটনাশক",
        storm: "⚡ ঝড়বৃষ্টি সতর্কতা",
        sports: "⚽ খেলাধুলো ও রোদ"
      }
    },
    es: {
      appName: "METEORA",
      tagline: "Asesor Meteorológico IA",
      inputPlaceholder: "Pregunte sobre el clima...",
      immediateActions: "🚨 Acciones Inmediatas",
      preventiveActions: "🛡️ Precauciones Preventivas",
      optimalWindows: "⏱️ Ventanas Óptimas",
      whatShouldIDo: "\"¿Qué debo hacer?\"",
      listen: "Escuchar",
      stop: "Detener",
      rainProb: "Precipitación",
      windGusts: "Viento / Ráfagas",
      uvIndex: "Índice UV",
      riskAnalysis: "Análisis de Riesgo Multifactorial",
      commuteDelay: "Fricción en Transporte",
      safetyExposure: "Seguridad en Exteriores",
      healthRisk: "Impacto en Salud / UV",
      hourlyOutlook: "Pronóstico Próximas 8 Horas",
      followUpTitle: "Preguntas de Seguimiento:",
      tabAdvisory: "Asesoría",
      tabForecast: "Pronóstico",
      tabRisk: "Riesgo",
      tabActions: "Acciones",
      chooseLocation: "Seleccionar Ubicación / GPS",
      autoGps: "Autodetectar mis coordenadas GPS",
      popularCities: "CIUDADES POPULARES:",
      changeLanguage: "Seleccionar Idioma",
      scenarios: {
        commute: "🚗 Trayecto Tarde",
        event: "🎉 Evento Exterior",
        crops: "🌾 Rociado Agrícola",
        storm: "⚡ Alerta Tormenta",
        sports: "⚽ Deportes & UV"
      }
    }
  },

  get(key) {
    const langObj = this.translations[this.currentLanguage] || this.translations['en'];
    return langObj[key] || this.translations['en'][key] || key;
  },

  setLanguage(langCode) {
    if (this.translations[langCode]) {
      this.currentLanguage = langCode;
      this.applyTranslations();
      return true;
    }
    return false;
  },

  applyTranslations() {
    // Update UI Elements with data-i18n attributes
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      const val = this.get(key);
      if (val) el.textContent = val;
    });

    // Update Input Placeholders
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
      const key = el.getAttribute('data-i18n-placeholder');
      const val = this.get(key);
      if (val) el.placeholder = val;
    });

    // Update Scenario Chips
    const scenarios = this.translations[this.currentLanguage]?.scenarios || this.translations['en'].scenarios;
    const chips = document.querySelectorAll('.scenario-scroll-row .s-pill');
    if (chips.length >= 5) {
      chips[0].textContent = scenarios.commute;
      chips[1].textContent = scenarios.event;
      chips[2].textContent = scenarios.crops;
      chips[3].textContent = scenarios.storm;
      chips[4].textContent = scenarios.sports;
    }

    // Update Active Language Indicator
    const langBtn = document.getElementById('currentLangCode');
    if (langBtn) {
      langBtn.textContent = this.currentLanguage.toUpperCase();
    }
  }
};
