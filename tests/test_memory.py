from backend.memory import MEMORY_STORE, retain_customer_memory, recall_customer_memories, normalize_hindsight_payload


def test_normalize_hindsight_payload_supports_common_response_shapes():
    assert normalize_hindsight_payload({"items": [{"customer_id": "cust-7", "content": "wifi issue", "channel": "PHONE"}]}) == [{"customer_id": "cust-7", "content": "wifi issue", "channel": "PHONE"}]
    assert normalize_hindsight_payload({"data": [{"customer_id": "cust-8", "content": "router reset", "channel": "CHAT"}]}) == [{"customer_id": "cust-8", "content": "router reset", "channel": "CHAT"}]
    assert normalize_hindsight_payload([{"content": "invoice", "channel": "CHAT"}]) == [{"content": "invoice", "channel": "CHAT"}]


def test_retain_and_recall_customer_memory():
    customer_id = "cust-remember"
    retain_customer_memory(customer_id, "Laptop Wi‑Fi issue persisted after router restart.", "PHONE")
    memories = recall_customer_memories(customer_id, "wifi")
    assert len(memories) >= 1
    assert "Wi‑Fi" in memories[0]["content"] or "wifi" in memories[0]["content"].lower()


def test_customer_memory_isolation():
    customer_a = "cust-a"
    customer_b = "cust-b"
    retain_customer_memory(customer_a, "Needs invoice copy for March 2025.", "CHAT")
    retain_customer_memory(customer_b, "Laptop Wi‑Fi issue after router reset.", "PHONE")

    memory_a = recall_customer_memories(customer_a, "invoice")
    memory_b = recall_customer_memories(customer_b, "wifi")

    assert any("invoice" in item["content"].lower() for item in memory_a)
    assert any("wifi" in item["content"].lower() for item in memory_b)
    assert not any("invoice" in item["content"].lower() for item in memory_b)
    assert not any("wifi" in item["content"].lower() for item in memory_a)


def test_cross_channel_memory_retrieval():
    customer_id = "cust-cross"
    retain_customer_memory(customer_id, "My laptop cannot connect to Wi‑Fi. I restarted the router, but it did not help.", "PHONE")
    memories = recall_customer_memories(customer_id, "The problem is still happening.")
    assert len(memories) >= 1
    assert "router" in memories[0]["content"].lower()
