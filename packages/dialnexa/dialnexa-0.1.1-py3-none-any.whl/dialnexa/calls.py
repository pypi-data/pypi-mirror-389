from __future__ import annotations

from typing import Any, Dict, Optional

from .http import HttpClient


def _require_fields(fields: Dict[str, Any]) -> None:
    for name, value in fields.items():
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValueError(f"{name} is required")


class CallsClient:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(
        self,
        *,
        agent_id: Optional[str] = None,
        call_id: Optional[str] = None,
        batch_call_id: Optional[str] = None,
        from_: Optional[str] = None,
        page: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> Any:
        params: Dict[str, Any] = {}
        if agent_id: params["agent_id"] = agent_id
        if call_id: params["call_id"] = call_id
        if batch_call_id: params["batch_call_id"] = batch_call_id
        if from_: params["from"] = from_
        # Apply fallbacks when not provided
        params["page"] = 1 if page is None else page
        params["limit"] = 30 if limit is None else limit
        return self._http.get_json("/calls", params=params, prefix="Calls request failed")

    def create(
        self,
        *,
        phone_number: str,
        agent_id: str,
        metadata: Dict[str, Any],
        agent_version_number: int,
    ) -> Dict[str, Any]:
        _require_fields({
            "phone_number": phone_number,
            "agent_id": agent_id,
            "metadata": metadata,
            "agent_version_number": agent_version_number,
        })
        body: Dict[str, Any] = {
            "phone_number": phone_number,
            "agent_id": agent_id,
            "metadata": metadata,
            "agent_version_number": agent_version_number,
        }
        return self._http.post_json("/calls", body, prefix="Calls request failed")

    def get(self, call_id: str) -> Dict[str, Any]:
        if not call_id:
            raise ValueError("id is required")
        return self._http.get_json(f"/calls/{call_id}", prefix="Calls request failed")
