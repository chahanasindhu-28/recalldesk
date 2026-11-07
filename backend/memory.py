import re
from typing import Any, Dict, List, Optional

import requests

from backend.config import get_settings, validate_customer_id


def normalize_memory_text(text: str) -> str:
    normalized = (text or "").lower()
    for dash in ["-", "‐", "‑", "‒", "–", "—", "―", "−", "﹘", "﹣", "－"]:
        normalized = normalized.replace(dash, " ")
    normalized = re.sub(r"\bwi\s*fi\b", "wifi", normalized)
    normalized = re.sub(r"\bwi\s*f\s*i\b", "wifi", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def normalize_hindsight_payload(payload: Any) -> List[Dict[str, Any]]:
    if payload is None:
        return []
    if isinstance(payload, list):
        items = payload
    elif isinstance(payload, dict):
        for key in ["items", "data", "records", "memories", "results", "entries"]:
            value = payload.get(key)
            if isinstance(value, list):
                items = value
                break
        else:
            if any(k in payload for k in ("customer_id", "content", "message")):
                items = [payload]
            elif "memory" in payload and isinstance(payload["memory"], dict):
                items = [payload["memory"]]
            else:
                items = []
    else:
        items = []

    normalized: List[Dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        record = dict(item)
        if "content" not in record and "message" in record:
            record["content"] = record["message"]
        if "channel" not in record and "source" in record:
            record["channel"] = "CHAT"
        if "customer_id" not in record and "customer" in record and isinstance(record["customer"], dict):
            record["customer_id"] = record["customer"].get("id") or record["customer"].get("customer_id")
        normalized.append(record)
    return normalized


class InMemoryBank:
    def __init__(self):
        self._records: Dict[str, List[Dict[str, Any]]] = {}

    def retain(self, customer_id: str, content: str, channel: str = "CHAT") -> Dict[str, Any]:
        validated_id = validate_customer_id(customer_id)
        cleaned = (content or "").strip()
        if not cleaned:
            raise ValueError("Memory content cannot be empty.")
        cleaned = normalize_memory_text(cleaned)
        cleaned = cleaned.replace("wifi", "wifi")
        record = {
            "customer_id": validated_id,
            "content": cleaned,
            "channel": channel.upper(),
            "source": "demo-memory-store",
        }
        self._records.setdefault(validated_id, []).append(record)
        return record

    def recall(self, customer_id: str, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        validated_id = validate_customer_id(customer_id)
        items = self._records.get(validated_id, [])
        if not query:
            return items[-limit:]
        q = normalize_memory_text(query)
        matches = []
        for item in items:
            content = normalize_memory_text(item["content"])
            channel = normalize_memory_text(item["channel"])
            source = normalize_memory_text(str(item.get("source", "")))
            if q in content or q in channel or q in source:
                matches.append(item)
        return matches[-limit:] if matches else items[-limit:]

    def list_customer_memories(self, customer_id: str) -> List[Dict[str, Any]]:
        validated_id = validate_customer_id(customer_id)
        return list(self._records.get(validated_id, []))

    def isolate_customer(self, customer_id: str) -> List[Dict[str, Any]]:
        validated_id = validate_customer_id(customer_id)
        return self.list_customer_memories(validated_id)


class HindsightMemoryClient(InMemoryBank):
    """Safe wrapper around Hindsight memory operations.

    A real Hindsight instance can be toggled on by setting the env values in .env.
    When the credentials are missing, this class automatically falls back to the demo
    in-memory store so local development remains stable.
    """

    def __init__(self):
        super().__init__()
        self.settings = get_settings()
        self.mode = "demo" if not self.settings["hindsight_api_key"] else "live"

    def can_use_live_api(self) -> bool:
        return bool(self.settings["hindsight_api_key"] and self.settings["hindsight_base_url"] and self.settings["hindsight_bank_id"])

    def _build_live_candidates(self, method: str) -> List[str]:
        base = (self.settings["hindsight_base_url"] or "").rstrip("/")
        bank_id = (self.settings["hindsight_bank_id"] or "").strip()
        candidates: List[str] = []
        seen = set()
        endpoints = [
            f"{base}/memories",
            f"{base}/v1/memories",
            f"{base}/api/memories",
            f"{base}/api/v1/memories",
        ]
        if bank_id:
            endpoints += [
                f"{base}/banks/{bank_id}/memories",
                f"{base}/v1/banks/{bank_id}/memories",
                f"{base}/api/banks/{bank_id}/memories",
                f"{base}/api/v1/banks/{bank_id}/memories",
            ]
        for url in endpoints:
            if url and url not in seen:
                candidates.append(url)
                seen.add(url)
        return candidates

    def _live_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.settings['hindsight_api_key']}",
            "X-API-Key": self.settings["hindsight_api_key"],
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _normalize_live_response(self, payload: Any) -> List[Dict[str, Any]]:
        items = normalize_hindsight_payload(payload)
        return [
            {
                "customer_id": item.get("customer_id") or item.get("customer") or "unknown",
                "content": item.get("content") or item.get("message") or "",
                "channel": (item.get("channel") or "CHAT").upper(),
                "source": "hindsight-live",
            }
            for item in items
            if item.get("content") or item.get("message")
        ]

    def _call_live(self, method: str, url: str, payload: Optional[Dict[str, Any]] = None) -> Any:
        request_kwargs: Dict[str, Any] = {"headers": self._live_headers(), "timeout": 20}
        if method.upper() == "GET":
            request_kwargs["params"] = payload or {}
        else:
            request_kwargs["json"] = payload or {}
        response = requests.request(method, url, **request_kwargs)
        response.raise_for_status()
        try:
            return response.json()
        except ValueError:
            return {}

    def retain(self, customer_id: str, content: str, channel: str = "CHAT") -> Dict[str, Any]:
        if self.can_use_live_api():
            for url in self._build_live_candidates("POST"):
                try:
                    result = self._call_live(
                        "POST",
                        url,
                        {
                            "customer_id": customer_id,
                            "content": content,
                            "channel": channel.upper(),
                            "bank_id": self.settings["hindsight_bank_id"],
                            "source": "internal",
                        },
                    )
                    memory_items = self._normalize_live_response(result)
                    if memory_items:
                        return memory_items[0]
                except Exception:
                    continue
        return super().retain(customer_id, content, channel)

    def recall(self, customer_id: str, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        if self.can_use_live_api():
            for url in self._build_live_candidates("GET"):
                try:
                    result = self._call_live(
                        "GET",
                        url,
                        {
                            "customer_id": customer_id,
                            "query": query,
                            "limit": limit,
                            "bank_id": self.settings["hindsight_bank_id"],
                        },
                    )
                    memory_items = self._normalize_live_response(result)
                    if memory_items:
                        return memory_items[:limit]
                except Exception:
                    continue
        return super().recall(customer_id, query, limit)


MEMORY_STORE = HindsightMemoryClient()


def recall_customer_memories(customer_id: str, query: str = "", limit: int = 3) -> List[Dict[str, Any]]:
    return MEMORY_STORE.recall(customer_id, query, limit)


def retain_customer_memory(customer_id: str, content: str, channel: str = "CHAT") -> Dict[str, Any]:
    return MEMORY_STORE.retain(customer_id, content, channel)


def get_customer_memory_snapshot(customer_id: str) -> List[Dict[str, Any]]:
    return MEMORY_STORE.list_customer_memories(customer_id)


def safe_customer_mapping(customer_id: str) -> str:
    validated = validate_customer_id(customer_id)
    return re.sub(r"[^A-Za-z0-9_-]", "", validated)
