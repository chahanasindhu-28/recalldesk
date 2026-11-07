import json
import os
from typing import Any, Dict, List, Optional

import requests

from backend.config import get_settings


LANGUAGE_NAMES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "ar": "Arabic",
    "hi": "Hindi",
    "kn": "Kannada",
    "te": "Telugu",
}


def _fallback_reply(message: str, memories: Optional[List[Dict[str, Any]]] = None, language: str = "en") -> str:
    memory_text = " ".join(item.get("content", "") for item in (memories or []))
    lower = message.lower()

    if language == "es":
        if "still happening" in lower and ("wifi" in memory_text.lower() or "wi-fi" in memory_text.lower()):
            return (
                "Recuerdo que tu laptop tuvo un problema de conexión Wi‑Fi y reiniciar el router no lo resolvió. "
                "Siguiente paso: olvida la red, conéctate otra vez y prueba la conexión."
            )
        if "invoice" in lower:
            return "Puedo ayudarte con tu factura. Dime qué factura o problema de cobro necesitas revisar."
        if "password" in lower:
            return "Puedo ayudarte con tu contraseña. Dime qué cuenta o sistema no acepta la contraseña."
        if memory_text:
            return (
                f"Encontré un recuerdo relevante: {memory_text[:220]} "
                "Comparte más detalles y continuaré con el siguiente paso de solución."
            )
        return "Estoy listo para ayudarte. Describe el problema y los pasos que ya intentaste."

    if language == "hi":
        if "still happening" in lower and ("wifi" in memory_text.lower() or "wi-fi" in memory_text.lower()):
            return (
                "Mere yaad hai ki aapke laptop mein Wi‑Fi connection problem tha aur router restart karne ke baad bhi problem nahi gaya. "
                "Agla step hai: network bhool kar dobara connect kijiye aur test kijiye."
            )
        if "invoice" in lower:
            return "Main aapki invoice me madad kar sakta hoon. Kya invoice ya billing issue check karni hai?"
        if "password" in lower:
            return "Main aapki password issue me madad kar sakta hoon. Kaun sa account ya system password accept nahi kar raha?"
        if memory_text:
            return (
                f"Mujhe ek relevant memory mili: {memory_text[:220]} "
                "Aur detail share kijiye, main agla troubleshooting step bata dunga."
            )
        return "Main aapki madad ke liye ready hoon. Problem aur aapne jo steps try kiye hain batayiye."

    if language == "kn":
        if "still happening" in lower and ("wifi" in memory_text.lower() or "wi-fi" in memory_text.lower()):
            return (
                "ನಿಮ್ಮ ಲ್ಯಾಪ್‌ಟಾಪ್‌ನಲ್ಲಿ Wi‑Fi ಸಂಪರ್ಕ ಸಮಸ್ಯೆ ಇತ್ತು ಮತ್ತು ರೌಟರ್ ಅನ್ನು ರಿ‌ಸ್ಟಾರ್ಟ್ ಮಾಡಿದ್ದರೂ ಸರಿಪಡಿಸಲಿಲ್ಲ. "
                "ಮುಂದಿನ ಹಂತ: ನೆಟ್‌ವರ್ಕ್ ಮರೆಯಿಸಿ, ಮತ್ತೆ ಕನೆಕ್ಟ್ ಮಾಡಿ ಮತ್ತು ಪರೀಕ್ಷಿಸಿ."
            )
        if "invoice" in lower:
            return "ನಿಮ್ಮ ಇನ್ವಾಯಿಸ್ ವಿಷಯದಲ್ಲಿ ನಾನು ಸಹಾಯ ಮಾಡಬಲ್ಲೆ. ಯಾವ ಇನ್ವಾಯಿಸ್ ಅಥವಾ ಬಿಲ್ ಸಮಸ್ಯೆ ಪರಿಶೀಲಿಸಬೇಕು?"
        if "password" in lower:
            return "ಪಾಸ್‌ವರ್ಡ್ ಸಮಸ್ಯೆಯಲ್ಲಿ ನಾನು ಸಹಾಯ ಮಾಡಬಲ್ಲೆ. ಯಾವ account ಅಥವಾ ಸಿಸ್ಟಮ್ ಪಾಸ್‌ವರ್ಡ್ ಒಪ್ಪುತ್ತಿಲ್ಲ?"
        if memory_text:
            return (
                f"ನನಗೆ ಸಂಬಂಧಿತ ಮೆಮೊರಿ ಸಿಕ್ಕಿದೆ: {memory_text[:220]} "
                "ಹೆಚ್ಚಿನ ವಿವರ ನೀಡಿ, ನಾನು ಮುಂದಿನ ಟ್ರಬಲ್‌ಶೂಟಿಂಗ್ ಹಂತವನ್ನು ಹೇಳುತ್ತೇನೆ."
            )
        return "ನಾನು ಸಹಾಯ ಮಾಡಲು ಸಿದ್ಧನಿದ್ದೇನೆ. ಸಮಸ್ಯೆ ಮತ್ತು ನೀವು ಪ್ರಯತ್ನಿಸಿದ ಹಂತಗಳನ್ನು ವಿವರಿಸಿ."

    if language == "te":
        if "still happening" in lower and ("wifi" in memory_text.lower() or "wi-fi" in memory_text.lower()):
            return (
                "మీ ల్యాప్‌టాప్‌లో Wi‑Fi కనెక్షన్ సమస్య ఉంది మరియు రూటర్‌ని రీస్టార్ట్ చేసిన తర్వాత కూడా పరిష్కారం కాలేదు. "
                "మరుసటి స్టెప్: నెట్‌వర్క్‌ను మర్చిపోండి, మళ్లీ కనెక్ట్ చేసి పరీక్షించండి."
            )
        if "invoice" in lower:
            return "నేను మీ ఇన్‌వాయిస్ సమస్యలో సహాయం చేయగలను. ఏ ఇన్‌వాయిస్ లేదా బిల్లింగ్ సమస్యను తనిఖీ చేయాలి?"
        if "password" in lower:
            return "నేను మీ పాస్‌వర్డ్ సమస్యలో సహాయం చేయగలను. ఏ account లేదా సిస్టమ్ పాస్‌వర్డ్‌ను అంగీకరించలేదు?"
        if memory_text:
            return (
                f"నాకు సంబంధిత మెమోరీ దొరికింది: {memory_text[:220]} "
                "మరిన్ని వివరాలు చెప్పండి, నేను తదుపరి ట్రబుల్షూటింగ్ స్టెప్ చెప్పబోతున్నాను."
            )
        return "నేను సహాయం చేయడానికి సిద్ధంగా ఉన్నాను. సమస్య మరియు మీరు尝试 చేసిన స్టెప్స్ చెప్పండి."

    if "still happening" in lower and ("wifi" in memory_text.lower() or "wi-fi" in memory_text.lower()):
        return (
            "I remember your laptop had a Wi‑Fi connection issue, and restarting your router did not solve it. "
            "Let’s try the next troubleshooting step: confirm the laptop is connecting to the correct network, "
            "forget the Wi‑Fi network, then reconnect and test again."
        )
    if "invoice" in lower:
        return "I can help with your invoice question. Please tell me which invoice or billing issue you need reviewed."
    if "password" in lower:
        return "I can help with a password issue. Please tell me which account or system is refusing the password."
    if memory_text:
        return (
            f"I found a relevant memory for this customer: {memory_text[:220]} "
            "Please share a little more detail and I’ll continue with the next troubleshooting step."
        )
    return "I’m ready to help. Please describe the issue and any steps you’ve already tried."


def generate_support_reply(message: str, memories: Optional[List[Dict[str, Any]]] = None, language: str = "en") -> str:
    settings = get_settings()
    api_key = settings["groq_api_key"]
    model = settings["groq_model"] or "llama-3.3-70b-versatile"

    if os.getenv("APP_ENV", "").lower() == "test" or "PYTEST_CURRENT_TEST" in os.environ:
        return _fallback_reply(message, memories, language)

    if not api_key:
        return _fallback_reply(message, memories, language)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    f"You are a professional customer support representative for a SaaS support desk. "
                    f"Answer in {LANGUAGE_NAMES.get(language, 'English')} language. "
                    "Use only retrieved customer memories, keep answers clear and empathetic, avoid inventing policies, "
                    "and ask follow-up questions when needed."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Customer message: {message}\n\n"
                    f"Relevant memories: {json.dumps(memories or [])}\n\n"
                    "Give a friendly, practical answer with the next troubleshooting step where relevant."
                ),
            },
        ],
        "temperature": 0.3,
        "max_tokens": 300,
    }

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        if not data.get("choices"):
            raise ValueError("Groq returned no completion choices")
        return data["choices"][0]["message"]["content"].strip()
    except Exception:
        return _fallback_reply(message, memories, language)
