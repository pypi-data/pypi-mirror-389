from __future__ import annotations

from typing import Any, Dict, Optional

from .http import HttpClient


class VoicesClient:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(self, *, provider_name: Optional[str] = None, accent: Optional[str] = None,
             gender: Optional[str] = None, name: Optional[str] = None,
             page: Optional[int] = None, limit: Optional[int] = None) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if provider_name: params["provider_name"] = provider_name
        if accent: params["accent"] = accent
        if gender: params["gender"] = gender
        if name: params["name"] = name
        if page is not None: params["page"] = page
        if limit is not None: params["limit"] = limit
        return self._http.get_json("/voices", params=params, prefix="Failed to list voices")

    def get(self, voice_id: str) -> Dict[str, Any]:
        if not voice_id:
            raise ValueError("id is required")
        return self._http.get_json(f"/voices/{voice_id}", prefix="Failed to get voice")
