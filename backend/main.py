from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.chat import build_chat_response
from backend.voice import app as voice_app

app = FastAPI(title="RecallDesk")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "RecallDesk"}


@app.post("/api/chat")
def chat_endpoint(payload: dict):
    customer_id = payload.get("customer_id")
    message = payload.get("message", "")
    memories = payload.get("memories", [])
    history = payload.get("conversation_history", [])
    response = build_chat_response(
        message=message,
        customer_id=customer_id,
        customer_name=payload.get("customer_name", "Customer"),
        memories=memories,
        conversation_history=history,
    )
    return {"reply": response, "memories_used": memories}


app.mount("/voice", voice_app)
