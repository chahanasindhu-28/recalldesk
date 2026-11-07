from io import BytesIO
from typing import Any, Dict, Optional, BinaryIO

import requests
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import Response

from backend.config import get_settings


app = FastAPI(title="RecallDesk Voice API")


def make_outbound_call(
    to_phone: str,
    customer_name: str = "customer",
    message: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "ok": False,
        "status": "not-supported",
        "message": "Twilio was removed to avoid paid phone-number requirements. Use Whisper transcription from a browser or uploaded audio file instead.",
    }


def transcribe_audio_file(audio_file: BinaryIO, filename: str = "voice-note.wav", language: str = "en") -> Dict[str, Any]:
    settings = get_settings()
    api_key = settings["groq_api_key"]
    if not api_key:
        return {
            "ok": False,
            "status": "not-configured",
            "message": "Add GROQ_API_KEY in your environment to use Whisper transcription.",
        }

    try:
        file_bytes = audio_file.read() if hasattr(audio_file, "read") else bytes(audio_file)
        if not file_bytes:
            return {"ok": False, "status": "empty-file", "message": "The uploaded audio file is empty."}

        response = requests.post(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {api_key}"},
            files={"file": (filename, BytesIO(file_bytes), "audio/mpeg")},
            data={"model": "distil-whisper-large-v3-en", "language": language},
            timeout=90,
        )
        response.raise_for_status()
        payload = response.json()
        text = payload.get("text") or ""
        return {"ok": True, "status": "transcribed", "text": text, "provider": "Whisper"}
    except Exception as exc:
        return {"ok": False, "status": "transcription-failed", "message": f"Whisper transcription failed: {exc}"}


@app.get("/health")
def health():
    return {"status": "ok", "service": "RecallDesk voice", "provider": "Whisper"}


@app.get("/api/voice/status")
def voice_status():
    settings = get_settings()
    configured = bool(settings["groq_api_key"])
    return {
        "status": "ready" if configured else "not-configured",
        "provider": "Whisper",
        "configured": configured,
    }


@app.post("/api/voice/incoming-call")
def incoming_call():
    twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Amanda">This RecallDesk app uses browser-based Whisper voice transcription instead of a paid phone number service.</Say>
</Response>
"""
    return Response(content=twiml, media_type="application/xml")


@app.websocket("/ws/voice")
async def voice_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive_text()
            if not message:
                continue
            await websocket.send_text(message)
    except WebSocketDisconnect:
        pass
    except Exception:
        await websocket.close(code=1008)


@app.post("/api/voice/demo")
def voice_demo():
    return {
        "status": "demo",
        "message": "Use Whisper transcription from a file upload or a browser mic flow instead of a Twilio number.",
        "instructions": [
            "Upload an audio file in the dashboard.",
            "Use the Whisper transcription result as the customer message.",
            "Keep support memory and AI replies enabled for the live conversation."
        ],
    }
