from typing import Any, Dict, List, Optional

import streamlit as st

from backend.config import validate_customer_id
from backend.llm import LANGUAGE_NAMES, generate_support_reply
from backend.memory import MEMORY_STORE, recall_customer_memories, retain_customer_memory
from backend.voice import transcribe_audio_file


LANGUAGE_OPTIONS = ["English", "Español", "Français", "Deutsch", "العربية", "हिन्दी", "ಕನ್ನಡ", "తెలుగు"]


SAMPLE_CUSTOMERS = {
    "cust-100": {
        "name": "Ava Patel",
        "profile": "Account owner, laptop user, active support customer",
        "phone": "+1-555-0100",
    },
    "cust-200": {
        "name": "Leo Chen",
        "profile": "Tablet user, invoice questions, prefers email follow-up",
        "phone": "+1-555-0200",
    },
}


def get_language_code(language_label: str) -> str:
    mapping = {
        "English": "en",
        "Español": "es",
        "Français": "fr",
        "Deutsch": "de",
        "العربية": "ar",
        "हिन्दी": "hi",
        "ಕನ್ನಡ": "kn",
        "తెలుగు": "te",
    }
    return mapping.get(language_label, "en")


def build_chat_response(
    message: str,
    customer_id: str,
    customer_name: str,
    memories: Optional[List[Dict[str, Any]]] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    language: str = "en",
) -> str:
    if not message or not str(message).strip():
        return "Please type a message before sending."

    cleaned_customer_id = validate_customer_id(str(customer_id))
    memory_items = list(memories or [])
    if not memory_items:
        memory_items = recall_customer_memories(cleaned_customer_id, message, limit=3)

    memory_text = " ".join(item.get("content", "") for item in memory_items)
    lower_message = str(message).lower()

    if "still happening" in lower_message and ("wifi" in memory_text.lower() or "wi-fi" in memory_text.lower()):
        if language == "es":
            return (
                "Recuerdo que tu laptop tuvo un problema de conexión Wi‑Fi y reiniciar el router no lo solucionó. "
                "El siguiente paso es olvidar la red, volver a conectarte y probar la conexión."
            )
        return (
            "I remember your laptop had a Wi‑Fi connection issue, and restarting your router did not solve it. "
            "Let’s try the next troubleshooting step: forget the network, reconnect, and test again."
        )

    if "problem is still happening" in lower_message and ("wireless" in memory_text.lower() or "wifi" in memory_text.lower()):
        if language == "es":
            return (
                "Recuerdo que tu laptop tuvo un problema de conexión Wi‑Fi y reiniciar el router no lo solucionó. "
                "El siguiente paso es olvidar la red guardada y volver a conectarte para verificar el perfil de la red."
            )
        return (
            "I remember your laptop had a Wi‑Fi connection issue, and restarting your router did not solve it. "
            "Let’s try the next troubleshooting step: forget the saved Wi‑Fi connection and reconnect to verify the network profile."
        )

    reply = generate_support_reply(str(message), memory_items, language=language)
    if reply and reply.lower().startswith("i found a relevant memory"):
        return reply
    return reply


def process_customer_message(
    message: str,
    customer_id: str,
    customer_name: str,
    channel: str = "CHAT",
    language: str = "en",
) -> Dict[str, Any]:
    validated_id = validate_customer_id(str(customer_id))
    memories = recall_customer_memories(validated_id, message, limit=3)
    reply = build_chat_response(message, validated_id, customer_name, memories, language=language)
    retain_customer_memory(validated_id, f"{channel}: {message}", channel)
    return {
        "customer_id": validated_id,
        "customer_name": customer_name,
        "reply": reply,
        "memories_used": memories,
        "memory_status": "stored" if memories else "none-found",
    }


def initialize_chat_session() -> None:
    if "conversation_map" not in st.session_state:
        st.session_state["conversation_map"] = {
            "cust-100": [
                {"role": "customer", "content": "My laptop cannot connect to Wi‑Fi. I restarted the router, but it did not help.", "channel": "PHONE"},
                {"role": "assistant", "content": "I remember your laptop had a Wi‑Fi issue, and restarting the router did not fix it. Let’s try removing the saved network and reconnecting.", "channel": "PHONE"},
            ],
            "cust-200": [
                {"role": "customer", "content": "I need the invoice for March 2025.", "channel": "CHAT"},
                {"role": "assistant", "content": "I can help with that. I’ll review the invoice details and follow up with the exact billing information you need.", "channel": "CHAT"},
            ],
        }
    if "chat_input" not in st.session_state:
        st.session_state["chat_input"] = ""
    if "call_status" not in st.session_state:
        st.session_state["call_status"] = "Whisper ready"
    if "voice_transcript" not in st.session_state:
        st.session_state["voice_transcript"] = ""


def render_chat_dashboard() -> None:
    st.set_page_config(page_title="RecallDesk", page_icon="💬", layout="wide")
    initialize_chat_session()

    st.markdown(
        """
        <style>
            .main {
                background: #ffffff;
                color: #111827;
            }

            .block-container {
                padding-top: 1.1rem;
                padding-bottom: 1.5rem;
            }

            div[data-testid="stSidebar"] {
                background: #f3f4f6;
                border-right: 1px solid #e5e7eb;
                color: #111827;
            }

            .stMarkdown {
                color: #111827 !important;
            }

            p, div, span, label {
                color: #111827 !important;
            }

            .brand {
                display: flex;
                align-items: center;
                gap: 0.75rem;
                padding: 0.25rem 0 1rem;
            }

            .brand-mark {
                width: 38px;
                height: 38px;
                border-radius: 12px;
                background: linear-gradient(135deg, #16a34a 0%, #22c55e 100%);
                color: white;
                font-weight: 900;
                display: flex;
                align-items: center;
                justify-content: center;
            }

            .brand-name {
                font-size: 1.5rem;
                font-weight: 800;
                letter-spacing: -0.05em;
                color: #111827;
            }

            .sidebar-card {
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 18px;
                padding: 0.9rem 0.95rem;
                margin-bottom: 0.9rem;
                box-shadow: 0 1px 2px rgba(0,0,0,0.04);
            }

            .eyebrow {
                font-size: 0.68rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                color: #4b5563;
                margin-bottom: 0.8rem;
            }

            .header-card {
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 22px;
                padding: 1rem 1.1rem;
                box-shadow: 0 6px 18px rgba(15, 23, 42, 0.08);
                margin-bottom: 1rem;
            }

            .header-title {
                font-size: 2.15rem;
                font-weight: 800;
                letter-spacing: -0.06em;
                color: #111827;
                margin: 0;
            }

            .status-pill {
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
                padding: 0.45rem 0.7rem;
                border-radius: 999px;
                background: rgba(34, 197, 94, 0.12);
                border: 1px solid rgba(34, 197, 94, 0.28);
                color: #166534;
                font-size: 0.7rem;
                font-weight: 800;
                letter-spacing: 0.08em;
                text-transform: uppercase;
            }

            .status-pill::before {
                content: "";
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: #22c55e;
                box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.18);
            }

            .compact-label {
                font-size: 0.63rem;
                letter-spacing: 0.12em;
                text-transform: uppercase;
                color: #4b5563;
                margin-bottom: 0.45rem;
            }

            .mini-value {
                font-size: 0.95rem;
                font-weight: 700;
                color: #111827;
                line-height: 1.6;
            }

            .stat-grid {
                display: grid;
                grid-template-columns: repeat(4, minmax(0, 1fr));
                gap: 0.9rem;
                margin-bottom: 1rem;
            }

            .stat-card {
                background: #f9fafb;
                border: 1px solid #e5e7eb;
                border-radius: 18px;
                padding: 0.9rem 1rem;
            }

            .stat-label {
                font-size: 0.68rem;
                letter-spacing: 0.1em;
                text-transform: uppercase;
                color: #4b5563;
            }

            .stat-value {
                margin-top: 0.5rem;
                font-size: 1.35rem;
                font-weight: 800;
                color: #111827;
            }

            .main-grid {
                display: grid;
                grid-template-columns: minmax(0, 2.2fr) minmax(240px, 0.9fr);
                gap: 1rem;
                align-items: start;
            }

            .chat-pane {
                background: #f8fafc;
                border: 1px solid #e5e7eb;
                border-radius: 22px;
                padding: 0.9rem;
            }

            .chat-title {
                color: #111827;
                font-weight: 700;
                font-size: 1rem;
                margin-bottom: 0.8rem;
            }

            .chat-shell {
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 18px;
                padding: 0.9rem;
                min-height: 490px;
                max-height: 490px;
                overflow-y: auto;
            }

            .bubble {
                max-width: 80%;
                margin: 0.7rem 0;
                padding: 0.8rem 0.9rem;
                border-radius: 16px;
                line-height: 1.55;
                font-size: 0.95rem;
                box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06);
            }

            .bubble.user {
                margin-left: auto;
                background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
                color: white;
                border-top-right-radius: 6px;
            }

            .bubble.assistant {
                background: #ecfdf5;
                color: #111827;
                border: 1px solid #bbf7d0;
                border-top-left-radius: 6px;
            }

            .side-pane {
                background: #f8fafc;
                border: 1px solid #e5e7eb;
                border-radius: 22px;
                padding: 1rem;
            }

            .side-card {
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 16px;
                padding: 0.9rem;
                margin-bottom: 0.9rem;
            }

            .side-label {
                font-size: 0.68rem;
                letter-spacing: 0.12em;
                text-transform: uppercase;
                color: #4b5563;
                margin-bottom: 0.4rem;
            }

            .side-value {
                color: #111827;
                font-weight: 700;
                line-height: 1.5;
            }

            [data-testid="stChatInput"] {
                border-radius: 16px;
                border: 1px solid #d1d5db;
                background: white;
                color: #111827;
            }

            .stButton > button {
                border: none;
                border-radius: 12px;
                background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
                color: white;
                font-weight: 800;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown(
            """
            <div class="brand">
                <div class="brand-mark">R</div>
                <div class="brand-name">RecallDesk</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="eyebrow">Support desk</div>', unsafe_allow_html=True)
        selected_customer = st.selectbox("Customer", list(SAMPLE_CUSTOMERS.keys()), index=0, label_visibility="collapsed")
        customer_data = SAMPLE_CUSTOMERS[selected_customer]

        st.markdown("<div class='sidebar-card'>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:1.12rem; font-weight:800; color:white; margin-bottom:0.35rem;'>{customer_data['name']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='mini-value'>Phone: {customer_data['phone']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='mini-value'>Profile: {customer_data['profile']}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        selected_language_label = st.selectbox("Language", LANGUAGE_OPTIONS, index=0)
        language_code = get_language_code(selected_language_label)
        memory_mode = "Live" if MEMORY_STORE.can_use_live_api() else "Demo"

        st.markdown("<div class='sidebar-card'>", unsafe_allow_html=True)
        st.markdown("<div class='compact-label'>Memory status</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='status-pill'>{memory_mode}</div>", unsafe_allow_html=True)
        st.markdown("<div class='mini-value' style='margin-top:0.7rem;'>Channel: Chat + Voice</div>", unsafe_allow_html=True)
        st.markdown("<div class='mini-value'>SLA: 02 min</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='sidebar-card'>", unsafe_allow_html=True)
        st.markdown("<div class='compact-label'>Voice capture</div>", unsafe_allow_html=True)
        audio_input = st.audio_input("Record voice note", key="customer_voice_recording")
        if audio_input is not None:
            with st.spinner("Transcribing audio with Whisper..."):
                result = transcribe_audio_file(audio_input, filename=f"voice-{selected_customer}.webm")
            if result["ok"]:
                st.session_state["voice_transcript"] = result["text"]
                st.session_state["call_status"] = "Transcribed with Whisper"
                st.success("Voice note captured")
                st.code(result["text"])
                if st.button("Send transcript", use_container_width=True):
                    prompt = result["text"].strip()
                    if prompt:
                        st.session_state["conversation_map"].setdefault(selected_customer, []).append({
                            "role": "customer",
                            "content": prompt,
                            "channel": "VOICE",
                        })
                        response = process_customer_message(prompt, selected_customer, customer_data["name"], "VOICE", language=language_code)
                        st.session_state["conversation_map"].setdefault(selected_customer, []).append({
                            "role": "assistant",
                            "content": response["reply"],
                            "channel": "VOICE",
                        })
                        st.rerun()
            else:
                st.session_state["call_status"] = "Whisper unavailable"
                st.warning(result["message"])

        uploaded_audio = st.file_uploader("Upload audio", type=["wav", "mp3", "m4a", "ogg", "webm"], label_visibility="collapsed")
        if uploaded_audio is not None:
            with st.spinner("Transcribing uploaded audio with Whisper..."):
                result = transcribe_audio_file(uploaded_audio, filename=uploaded_audio.name)
            if result["ok"]:
                st.session_state["voice_transcript"] = result["text"]
                st.session_state["call_status"] = "Transcribed with Whisper"
                st.success("Audio uploaded and transcribed")
                st.code(result["text"])
                if st.button("Send uploaded transcript", use_container_width=True):
                    prompt = result["text"].strip()
                    if prompt:
                        st.session_state["conversation_map"].setdefault(selected_customer, []).append({
                            "role": "customer",
                            "content": prompt,
                            "channel": "VOICE",
                        })
                        response = process_customer_message(prompt, selected_customer, customer_data["name"], "VOICE", language=language_code)
                        st.session_state["conversation_map"].setdefault(selected_customer, []).append({
                            "role": "assistant",
                            "content": response["reply"],
                            "channel": "VOICE",
                        })
                        st.rerun()
            else:
                st.session_state["call_status"] = "Whisper unavailable"
                st.warning(result["message"])
        st.caption(f"Status: {st.session_state['call_status']}")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='sidebar-card'>", unsafe_allow_html=True)
        st.markdown("<div class='compact-label'>Recommended next step</div>", unsafe_allow_html=True)
        if selected_customer == "cust-100":
            st.markdown("<div class='mini-value'>Ask the customer to forget the saved Wi‑Fi network and reconnect to confirm the network profile.</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='mini-value'>Confirm billing details and send the invoice summary with clear follow-up instructions.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        """
        <div class="header-card">
            <div style="display:flex; align-items:center; justify-content:space-between; gap:1rem; flex-wrap:wrap;">
                <div>
                    <div class="eyebrow" style="color: rgba(148,163,184,0.8); margin-bottom: 0.2rem;">Support workspace</div>
                    <div class="header-title">{customer_name}</div>
                </div>
                <div class="status-pill">AI memory active</div>
            </div>
        </div>
        """.format(customer_name=customer_data["name"]),
        unsafe_allow_html=True,
    )

    metric_items = [
        ("Queue", "12 active"),
        ("SLA", "02 min"),
        ("Memory", memory_mode),
        ("Response", "Fast"),
    ]

    cols = st.columns(4)
    for col, (label, value) in zip(cols, metric_items):
        with col:
            st.markdown(f"<div class='stat-card'><div class='stat-label'>{label}</div><div class='stat-value'>{value}</div></div>", unsafe_allow_html=True)

    left_col, right_col = st.columns([2.15, 0.85])

    with left_col:
        st.markdown("<div class='chat-pane'>", unsafe_allow_html=True)
        st.markdown("<div class='chat-title'>Live conversation</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        chat_history = st.session_state["conversation_map"].get(selected_customer, [])

        st.markdown("<div class='chat-shell'>", unsafe_allow_html=True)
        for item in chat_history:
            role = "user" if item["role"] == "customer" else "assistant"
            st.markdown(f"<div class='bubble {role}'>{item['content']}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        voice_fill = st.session_state.get("voice_fill_text", "")
        if voice_fill:
            current_value = st.session_state.get("support_reply_text", "")
            st.session_state["support_reply_text"] = (f"{current_value} {voice_fill}" if current_value else voice_fill).strip()
            st.session_state["voice_fill_text"] = ""

        st.session_state["selected_customer"] = selected_customer
        st.session_state["customer_data"] = customer_data
        st.session_state["language_code"] = language_code

        input_cols = st.columns([6, 1])
        with input_cols[0]:
            with st.form(key="reply_form", clear_on_submit=True):
                prompt = st.text_input(
                    "Reply to customer",
                    key="support_reply_text",
                    placeholder="Type a reply...",
                )
                submitted = st.form_submit_button("Send message", use_container_width=True)
                if submitted and prompt.strip():
                    st.session_state["conversation_map"].setdefault(selected_customer, []).append({
                        "role": "customer",
                        "content": prompt.strip(),
                        "channel": "CHAT",
                    })
                    result = process_customer_message(prompt.strip(), selected_customer, customer_data["name"], "CHAT", language=language_code)
                    st.session_state["conversation_map"].setdefault(selected_customer, []).append({
                        "role": "assistant",
                        "content": result["reply"],
                        "channel": "CHAT",
                    })
                    st.rerun()
        with input_cols[1]:
            voice_note = st.audio_input(
                "🎙",
                key=f"reply_voice_{selected_customer}",
                label_visibility="collapsed",
                help="Record a voice note and convert it to text",
            )
            if voice_note is not None:
                with st.spinner("Transcribing voice note..."):
                    result = transcribe_audio_file(voice_note, filename=f"reply-{selected_customer}.webm")
                if result["ok"]:
                    transcript = result["text"].strip()
                    st.session_state["voice_fill_text"] = transcript
                    st.success("Voice converted to text")
                else:
                    st.warning(result["message"])

    with right_col:
        st.markdown("<div class='side-pane'>", unsafe_allow_html=True)
        st.markdown(
            """
            <div class="side-card">
                <div class="side-label">Customer profile</div>
                <div class="side-value">{customer_name}</div>
            </div>
            """.format(customer_name=customer_data["name"]),
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="side-card">
                <div class="side-label">Live status</div>
                <div class="side-value">{call_status}</div>
            </div>
            """.format(call_status=st.session_state["call_status"]),
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="side-card">
                <div class="side-label">Latest memory</div>
                <div class="side-value">Wi‑Fi instability and router restarts did not resolve the issue.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="side-card">
                <div class="side-label">Case notes</div>
                <div class="side-value">Priority: medium • Response window: under 2 minutes • AI memory retention enabled</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    render_chat_dashboard()
