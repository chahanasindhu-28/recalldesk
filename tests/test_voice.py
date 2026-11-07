from io import BytesIO

from backend.voice import make_outbound_call, transcribe_audio_file


def test_make_outbound_call_uses_whisper_flow():
    result = make_outbound_call("+15551234567", "Ava")

    assert result["ok"] is False
    assert result["status"] == "not-supported"
    assert "Whisper" in result["message"]


def test_transcribe_audio_uses_groq_whisper(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"text": "hello from the customer"}

    def fake_post(url, headers=None, files=None, data=None, timeout=None):
        assert "audio/transcriptions" in url
        assert headers["Authorization"] == "Bearer test-key"
        assert files["file"][0] == "voice-note.wav"
        return FakeResponse()

    import backend.voice as voice_module
    monkeypatch.setattr(voice_module.requests, "post", fake_post)

    result = transcribe_audio_file(BytesIO(b"audio-bytes"), filename="voice-note.wav")

    assert result["ok"] is True
    assert result["text"] == "hello from the customer"
