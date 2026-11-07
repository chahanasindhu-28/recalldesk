from backend.chat import build_chat_response


def test_chat_response_reuses_customer_memory():
    memories = [
        {
            "content": "Customer reported Wi-Fi connection issue on laptop. Restarted router; issue persisted.",
            "channel": "PHONE",
        }
    ]

    response = build_chat_response(
        "The problem is still happening.",
        customer_id="cust-123",
        customer_name="Ava",
        memories=memories,
        conversation_history=[
            {"role": "customer", "content": "My laptop cannot connect to Wi-Fi. I restarted the router, but it did not help."},
        ],
    )

    text = response.lower()
    assert "remember" in text or "wi-fi" in text
    assert "router" in text


def test_chat_response_supports_optional_language_selection():
    response = build_chat_response(
        "The problem is still happening.",
        customer_id="cust-223",
        customer_name="Sofia",
        memories=[{"content": "Laptop Wi‑Fi issue after router reboot did not help.", "channel": "PHONE"}],
        language="es",
    )

    lowered = response.lower()
    assert "recuerdo" in lowered or "wifi" in lowered or "router" in lowered
