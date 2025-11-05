from __future__ import annotations

from typing import Any, Dict

from .http import HttpClient


class AgentsClient:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def create(self, body: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(body, dict):
            raise ValueError("body is required")
        prompts = body.get("prompts") or {}
        welcome = prompts.get("welcome_message")
        if not isinstance(welcome, str) or not welcome.strip():
            raise ValueError("prompts.welcome_message is required and must be a non-empty string")
        return self._http.post_api("/agents2", body)

    def list(self) -> Dict[str, Any]:
        return self._http.get_api("/agents2")

    def get(self, agent_id: str) -> Dict[str, Any]:
        if not agent_id:
            raise ValueError("id is required")
        return self._http.get_api(f"/agents2/{agent_id}")

    def update(self, agent_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        if not agent_id:
            raise ValueError("id is required")
        if not isinstance(body, dict):
            raise ValueError("body is required")
        return self._http.patch_api(f"/agents2/{agent_id}", body)
