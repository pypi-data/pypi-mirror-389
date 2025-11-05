from __future__ import annotations

from typing import Any, Dict, Optional

from .http import HttpClient


class LanguagesClient:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(self) -> Dict[str, Any]:
        return self._http.get_json("/languages", prefix="Failed to list languages")

    def get(self, language_id: str) -> Dict[str, Any]:
        if not language_id:
            raise ValueError("id is required")
        return self._http.get_json(f"/languages/{language_id}", prefix="Failed to get language")
